"""Imagine helper, pushed to the AI CT (/opt/imagine/gen.py) and run there by the agent through `pct exec`.

Reads one JSON request on stdin and talks to the local ComfyUI (127.0.0.1:8188, stdlib only):
  {"op": "ready"}                                  -> {"event": "ready", "ok": bool}
  {"op": "free"}                                   -> {"event": "freed"}
  {"op": "image", "prompt", "style", "size", "draft", "adult"?, "seed"?, "reference_b64"?, "reference_id"?, "ip_weight"?}
        -> {"event": "saved", "png_b64": ..., "seed": int} or {"event": "error", "kind": "oom" | "other", "msg": ...}
The workflows are fixed here; the owner never picks a model or steps. The seed is random unless the request carries one
(regenerating from the edit panel reuses the stored seed).
A non-draft Anime request that carries `reference_b64` (a character's reference PNG) also gets IP-Adapter: the PNG is uploaded to the
engine's input folder (named by `reference_id` + a hash, so it is reused) and steers the NoobAI model towards that face and look.
"""
import base64, hashlib, json, os, random, re, sys, time, urllib.error, urllib.parse, urllib.request, uuid

BASE = "http://127.0.0.1:8188"

# --- MODELS: the one place that names a model. To swap one, edit its line here (and the same file name in REQUIRED_FILES
# in agent/imagine.py, which only checks that the files exist). Files live in /models/comfyui/models/<folder>/.
# Which workflow serves which request: Draft (any style) -> "draft"; Photo -> "photo"; Anime -> "anime"; Pixel / Logo -> "flux".
#   workflow  file(s)                                              steps  cfg  sampler          scheduler
MODELS = {
    "draft": {"ckpt": "sd_xl_turbo_1.0_fp16.safetensors", "steps": 4, "cfg": 1.0, "sampler": "euler_ancestral", "scheduler": "simple"},  # SDXL Turbo
    "photo": {"ckpt": "juggernautXL.safetensors", "steps": 25, "cfg": 5.5, "sampler": "dpmpp_2m", "scheduler": "karras"},  # Juggernaut XL
    "anime": {"ckpt": "noobai-xl-1.1.safetensors", "steps": 28, "cfg": 5.5, "sampler": "euler_ancestral", "scheduler": "normal"},  # NoobAI-XL 1.1 (SDXL eps), CLIP skip 1
    "flux": {"unet": "flux1-schnell-Q5_K_S.gguf", "clip_t5": "t5-v1_1-xxl-encoder-Q5_K_M.gguf", "clip_l": "clip_l.safetensors",
             "vae": "ae.safetensors", "steps": 4, "cfg": 1.0, "sampler": "euler", "scheduler": "simple"},  # FLUX.1-schnell Q5_K_S
    # IP-Adapter (ComfyUI_IPAdapter_plus), only for non-draft Anime jobs that carry a character's reference picture. It is applied to the
    # NoobAI model: "adapter" in models/ipadapter, "vision" in models/clip_vision. weight_type / combine_embeds / embeds_scaling are the pack's own values.
    "ipadapter": {"adapter": "ip-adapter-plus_sdxl_vit-h.safetensors", "vision": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
                  "weight": 0.25, "weight_type": "linear", "combine_embeds": "concat", "embeds_scaling": "V only", "start_at": 0.0, "end_at": 1.0},
}

OUT_DIRS = ("/models/comfyui/output",)  # SaveImage results are removed again once fetched
STYLE = {
    "photo": "photorealistic, natural light, detailed",
    "anime": "anime illustration, clean line art, vibrant colors",
    "pixel": "pixel art, 16-bit, limited palette, crisp pixels",
    "logo": "minimal vector logo, flat design, centered, white background",
}
NEG = "blurry, low quality, watermark, text artifacts"
# NoobAI (Anime, not Draft): quality tags first, then the prompt, then the style text. Adult mode drops "safe," and "nsfw" only.
ANIME_PRE = "masterpiece, best quality, newest, absurdres, highres,"
ANIME_NEG = "worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands, mammal, anthro, furry, ambiguous form, feral, semi-anthro"
SIZES = {"square": (1024, 1024), "portrait": (832, 1216), "landscape": (1216, 832), "phone": (576, 1248)}


def _req(path, data=None, timeout=30):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/json"} if body else {})
    with urllib.request.urlopen(r, timeout=timeout) as f:
        return f.read()


def _json(path, data=None, timeout=30):
    return json.loads(_req(path, data, timeout) or b"null")


def turbo_size(w, h, cap=512):
    k = cap / max(w, h)
    return max(8, round(w * k / 8) * 8), max(8, round(h * k / 8) * 8)


def build(prompt, style, size, draft, seed, adult=False, ref=None, weight=None):
    """the API-format workflow dict for one image (adult only matters for Anime, and not for Draft).
    ref = the reference image's file name in the engine's input folder: only a non-draft Anime image uses it (IP-Adapter)."""
    text = f"{prompt}, {STYLE[style]}"
    w, h = SIZES[size]
    if draft:
        w, h = turbo_size(w, h)
        return _sdxl(MODELS["draft"], text, w, h, seed)
    if style == "anime":
        pos = f"{ANIME_PRE} {'' if adult else 'safe, '}{text}"
        return _sdxl(MODELS["anime"], pos, w, h, seed, neg=ANIME_NEG if adult else "nsfw, " + ANIME_NEG, ref=ref, weight=weight)
    if style == "photo":
        return _sdxl(MODELS["photo"], text, w, h, seed)
    m = MODELS["flux"]
    return {  # FLUX schnell (GGUF): no negative prompt at cfg 1, an empty one fills the slot
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": m["unet"]}},
        "2": {"class_type": "DualCLIPLoaderGGUF", "inputs": {"clip_name1": m["clip_t5"], "clip_name2": m["clip_l"], "type": "flux"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["2", 0]}},
        "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "seed": seed, "steps": m["steps"], "cfg": m["cfg"], "sampler_name": m["sampler"],
              "scheduler": m["scheduler"], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0], "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "imagine"}},
    }


def _sdxl(m, text, w, h, seed, neg=NEG, ref=None, weight=None):
    """checkpoint workflow shared by Draft (SDXL Turbo), Photo (Juggernaut XL) and Anime (NoobAI-XL);
    with ref the KSampler gets the model through IP-Adapter (nodes 20-24)"""
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": m["ckpt"]}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "seed": seed, "steps": m["steps"], "cfg": m["cfg"], "sampler_name": m["sampler"],
              "scheduler": m["scheduler"], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0], "denoise": 1.0}},
        "6": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["5", 0], "vae": ["1", 2], "tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "imagine"}},
    }
    if ref:
        ip = MODELS["ipadapter"]
        wf.update({
            "20": {"class_type": "LoadImage", "inputs": {"image": ref}},
            "21": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": ip["adapter"]}},
            "22": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": ip["vision"]}},
            "23": {"class_type": "IPAdapterAdvanced", "inputs": {
                "model": ["1", 0], "ipadapter": ["21", 0], "image": ["20", 0], "clip_vision": ["22", 0],
                "weight": float(weight if weight is not None else ip["weight"]), "weight_type": ip["weight_type"], "combine_embeds": ip["combine_embeds"],
                "start_at": ip["start_at"], "end_at": ip["end_at"], "embeds_scaling": ip["embeds_scaling"]}},
        })
        wf["5"]["inputs"]["model"] = ["23", 0]
    return wf


def upload_reference(cid, png):
    """put the reference PNG into the engine's input folder as ref_<id>_<hash>.png (same picture = same name, so it is reused) -> that name"""
    cid = re.sub(r"[^a-f0-9]", "", str(cid or ""))[:10] or "x"
    name = f"ref_{cid}_{hashlib.sha256(png).hexdigest()[:12]}.png"
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n").encode() + png \
        + (f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"type\"\r\n\r\ninput\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n").encode()
    r = urllib.request.Request(BASE + "/upload/image", data=body, headers={"Content-Type": "multipart/form-data; boundary=" + b})
    with urllib.request.urlopen(r, timeout=60) as f:
        got = json.loads(f.read() or b"{}")
    return got.get("name") or name


def _fit(wf):
    """drop inputs a node of this ComfyUI version does not know (VAEDecodeTiled grew temporal_* later)"""
    for node in wf.values():
        if node["class_type"] != "VAEDecodeTiled":
            continue
        try:
            info = _json("/object_info/VAEDecodeTiled")["VAEDecodeTiled"]["input"]
            known = set(info.get("required", {})) | set(info.get("optional", {}))
            node["inputs"] = {k: v for k, v in node["inputs"].items() if k in known or isinstance(v, list)}
        except Exception:
            pass
    return wf


def _fail(kind, msg):
    return {"event": "error", "kind": kind, "msg": str(msg)[:600]}


def _kind(msg):
    m = str(msg).lower()
    return "oom" if "out of memory" in m or "outofmemory" in m else "other"


def image(req):
    try:
        seed = int(req.get("seed") or 0)
    except (TypeError, ValueError):
        seed = 0
    if not 0 < seed < 2**53:
        seed = random.randrange(1, 2**53)
    ref = None
    if req.get("reference_b64") and req["style"] == "anime" and not req["draft"]:  # Draft never uses the reference
        try:
            ref = upload_reference(req.get("reference_id"), base64.b64decode(req["reference_b64"]))
        except Exception as e:  # noqa: BLE001
            return _fail("other", f"could not hand the reference picture to the engine: {e}")
    wf = _fit(build(req["prompt"], req["style"], req["size"], bool(req["draft"]), seed, bool(req.get("adult")), ref, req.get("ip_weight")))
    try:
        pid = _json("/prompt", {"prompt": wf, "client_id": "imagine"})["prompt_id"]
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        return _fail(_kind(txt), txt)
    except Exception as e:
        return _fail("other", e)
    end = time.time() + 900
    while time.time() < end:
        time.sleep(1)
        try:
            h = _json(f"/history/{pid}").get(pid)
        except Exception:
            continue
        if not h:
            continue
        st = h.get("status") or {}
        if st.get("status_str") == "error":
            for name, d in st.get("messages", []):
                if name == "execution_error":
                    msg = d.get("exception_message") or d.get("exception_type") or "failed"
                    return _fail(_kind(msg + " " + str(d.get("exception_type", ""))), msg)
            return _fail("other", "the engine reported an error")
        for out in (h.get("outputs") or {}).values():
            for im in out.get("images", []):
                q = urllib.parse.urlencode({"filename": im["filename"], "subfolder": im.get("subfolder", ""), "type": im.get("type", "output")})
                png = _req("/view?" + q, timeout=60)
                for d in OUT_DIRS:
                    try:
                        os.remove(os.path.join(d, im.get("subfolder", ""), im["filename"]))
                    except OSError:
                        pass
                return {"event": "saved", "png_b64": base64.b64encode(png).decode(), "seed": seed}
        if st.get("completed"):
            return _fail("other", "no image came out")
    return _fail("other", "timed out")


def main():
    req = json.loads(sys.stdin.read() or "{}")
    op = req.get("op")
    if op == "ready":
        try:
            _json("/system_stats", timeout=5)
            res = {"event": "ready", "ok": True}
        except Exception:
            res = {"event": "ready", "ok": False}
    elif op == "free":
        try:
            _req("/free", {"unload_models": True, "free_memory": True}, timeout=30)
        except Exception:
            pass
        res = {"event": "freed"}
    elif op == "image":
        res = image(req)
    else:
        res = _fail("other", "unknown op")
    print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
