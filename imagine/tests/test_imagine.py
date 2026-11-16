"""offline tests for the pure logic of agent/imagine.py: python3 -I addons/imagine/tests/test_imagine.py"""
import base64
import json
import sys
from datetime import date
import tempfile
import threading
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "agent"))
sys.path.insert(0, str(root / "addons/imagine/agent"))
sys.path.insert(0, str(root / "addons/imagine/bin"))
import imagine as m  # noqa: E402
import gen  # noqa: E402

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def raises(fn, *a):
    try:
        fn(*a)
    except ValueError:
        return True
    return False


good = {"prompt": "  a fox  ", "style": "anime", "size": "square", "draft": 1, "count": "4"}
v = m.validate(good)
check("validate ok", v == {"prompt": "a fox", "style": "anime", "size": "square", "draft": True, "count": 4, "adult": False})
check("empty prompt", raises(m.validate, {**good, "prompt": "  "}))
check("long prompt", raises(m.validate, {**good, "prompt": "x" * 1001}))
check("1000 chars ok", m.validate({**good, "prompt": "x" * 1000})["count"] == 4)
check("bad style", raises(m.validate, {**good, "style": "oil"}))
check("bad size", raises(m.validate, {**good, "size": "wide"}))
check("count 0", raises(m.validate, {**good, "count": 0}))
check("count 5", raises(m.validate, {**good, "count": 5}))
check("count junk", raises(m.validate, {**good, "count": "x"}))
check("body not dict", raises(m.validate, None))

jobs = [m.new_job(v, 100), m.new_job(v, 101), m.new_job(v, 102)]
check("new job fields", jobs[0]["status"] == "queued" and jobs[0]["done_n"] == 0 and len(jobs[0]["id"]) == 10 and m.ID_RE.fullmatch(jobs[0]["id"]))
check("next job is first queued", m.next_job(jobs) is jobs[0])
check("cancel queued", m.cancel_job(jobs, jobs[0]["id"]) == "done" and jobs[0]["status"] == "cancelled")
check("next skips cancelled", m.next_job(jobs) is jobs[1])
jobs[1]["status"] = "running"
check("cancel running flags", m.cancel_job(jobs, jobs[1]["id"]) == "flag" and jobs[1]["status"] == "running")
check("cancel finished refused", raises(m.cancel_job, jobs, jobs[0]["id"]))
check("cancel unknown", raises(m.cancel_job, jobs, "0123456789"))
jobs[2]["status"] = "paused"
m.recover(jobs)
check("recover running+paused -> queued", jobs[1]["status"] == "queued" and jobs[2]["status"] == "queued" and jobs[0]["status"] == "cancelled")
many = [{**m.new_job(v), "status": "done"} for _ in range(50)] + [m.new_job(v)]
p = m.prune(many)
check("prune keeps live + last 30", len(p) == 31 and p[-1]["status"] == "queued")

pmon = """# gpu         pid   type     sm    mem    enc    dec    jpg    ofa    command
# Idx           #    C/G      %      %      %      %      %      %    name
    0       1234     C     12      3      -      -      -      -    ollama
    0       5678     G      0      1      -      -      -      -    Xorg
"""
check("parse_pmon", m.parse_pmon(pmon) == [1234, 5678])
check("parse_pmon empty", m.parse_pmon("") == [] and m.parse_pmon("No devices") == [])
check("parse_encoder", m.parse_encoder("0\n") == 0 and m.parse_encoder("2\n") == 2 and m.parse_encoder("N/A\n") == 0)
cof = {5678: 109, 1234: 105}.get
check("pmon games pid -> streaming", m.streaming_from("0", pmon, cof, 109))
check("pmon no games pid", not m.streaming_from("0", pmon, {1234: 105}.get, 109))
check("encoder session -> streaming", m.streaming_from("1", "", cof, 109))
check("games CT stopped -> not streaming", not m.streaming_from("1", pmon, cof, 109, games_up=False))
check("no games CT, no encoder", not m.streaming_from("0", pmon, cof, 0))
check("oom detect", m.oom("CUDA out of memory. Tried") and m.oom("torch.OutOfMemoryError") and not m.oom("bad input"))

# gen.py workflows
check("turbo size", gen.turbo_size(1024, 1024) == (512, 512) and gen.turbo_size(832, 1216) == (352, 512) and gen.turbo_size(1216, 832) == (512, 352))
wf = gen.build("x", "anime", "portrait", False, 7)
check("anime graph", wf["1"]["inputs"]["ckpt_name"] == "noobai-xl-1.1.safetensors" and wf["4"]["inputs"]["width"] == 832 and wf["4"]["inputs"]["height"] == 1216
      and "anime illustration" in wf["2"]["inputs"]["text"] and wf["6"]["class_type"] == "VAEDecodeTiled")
k = wf["5"]["inputs"]
check("anime sampler", k["sampler_name"] == "euler_ancestral" and k["scheduler"] == "normal" and k["steps"] == 28 and k["cfg"] == 5.5
      and not any(n["class_type"] == "CLIPSetLastLayer" for n in wf.values()) and wf["2"]["inputs"]["clip"] == ["1", 1])
POS_SAFE = "masterpiece, best quality, newest, absurdres, highres, safe, x, anime illustration, clean line art, vibrant colors"
NEG_SAFE = "nsfw, worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands, mammal, anthro, furry, ambiguous form, feral, semi-anthro"
check("anime safe prompts", wf["2"]["inputs"]["text"] == POS_SAFE and wf["3"]["inputs"]["text"] == NEG_SAFE)
wa = gen.build("x", "anime", "square", False, 7, True)
check("anime adult drops safe + nsfw only", wa["2"]["inputs"]["text"] == POS_SAFE.replace(" safe,", "") and wa["3"]["inputs"]["text"] == NEG_SAFE.replace("nsfw, ", "")
      and "safe" not in wa["2"]["inputs"]["text"] and "worst quality" in wa["3"]["inputs"]["text"] and wa["4"]["inputs"]["width"] == 1024)
for st in ("photo", "pixel", "logo"):
    check(f"adult ignored for {st}", gen.build("x", st, "square", False, 7, True) == gen.build("x", st, "square", False, 7, False))
    check(f"no anime tags on {st}", "masterpiece" not in json.dumps(gen.build("x", st, "square", False, 7, True)))
check("draft anime ignores adult", gen.build("x", "anime", "square", True, 7, True) == gen.build("x", "anime", "square", True, 7, False)
      and gen.build("x", "anime", "square", True, 7, True)["1"]["inputs"]["ckpt_name"].startswith("sd_xl_turbo") and "safe" not in gen.build("x", "anime", "square", True, 7, True)["2"]["inputs"]["text"])
check("anime landscape bucket", gen.build("x", "anime", "landscape", False, 1)["4"]["inputs"]["width"] == 1216)
wf = gen.build("x", "pixel", "portrait", False, 7)
check("flux graph", wf["1"]["class_type"] == "UnetLoaderGGUF" and wf["1"]["inputs"]["unet_name"] == "flux1-schnell-Q5_K_S.gguf" and wf["6"]["inputs"]["width"] == 832 and wf["7"]["inputs"]["steps"] == 4 and "pixel art" in wf["4"]["inputs"]["text"])
check("logo uses Q5", gen.build("x", "logo", "square", False, 1)["1"]["inputs"]["unet_name"] == "flux1-schnell-Q5_K_S.gguf")
check("required files", "unet/flux1-schnell-Q5_K_S.gguf" in m.REQUIRED_FILES and "checkpoints/noobai-xl-1.1.safetensors" in m.REQUIRED_FILES and not any("Q4" in f for f in m.REQUIRED_FILES))
check("validate adult", m.validate({**good, "adult": True})["adult"] is True and m.validate({**good, "style": "photo", "adult": True})["adult"] is False and m.validate(good)["adult"] is False)
wf = gen.build("x", "photo", "square", False, 7)
check("sdxl graph", wf["1"]["inputs"]["ckpt_name"] == "juggernautXL.safetensors" and wf["5"]["inputs"]["steps"] == 25 and wf["6"]["class_type"] == "VAEDecodeTiled")
wf = gen.build("x", "logo", "landscape", True, 7)
check("turbo graph", wf["1"]["inputs"]["ckpt_name"].startswith("sd_xl_turbo") and wf["4"]["inputs"]["width"] == 512 and wf["5"]["inputs"]["sampler_name"] == "euler_ancestral")

# models table: one place, same values as before
M = gen.MODELS
check("models table", M["draft"]["steps"] == 4 and M["draft"]["sampler"] == "euler_ancestral" and M["photo"]["steps"] == 25 and M["photo"]["cfg"] == 5.5
      and M["photo"]["scheduler"] == "karras" and M["flux"]["unet"] == "flux1-schnell-Q5_K_S.gguf" and M["anime"]["steps"] == 28 and M["flux"]["sampler"] == "euler")
check("flux files from table", gen.build("x", "pixel", "square", False, 1)["2"]["inputs"]["clip_name1"] == M["flux"]["clip_t5"])

# edit JSON: validation, compose
c = m.clean_json({"subject": " a fox ", "setting": "x" * 300, "bogus": "no", "details": ["a", "", "b" * 200] + ["d"] * 8, "mood": 5})
check("clean drops extra keys", set(c) == {*m.JSON_KEYS, "details"})
check("clean caps values", c["subject"] == "a fox" and len(c["setting"]) == 200 and c["mood"] == "5" and c["lighting"] == "")
check("clean details cap", len(c["details"]) == 6 and len(c["details"][1]) == 120 and "" not in c["details"])
check("clean details str", m.clean_json({"details": "snow"})["details"] == ["snow"])
check("clean not dict", raises(m.clean_json, ["x"]))
check("model reply bad json", raises(m.parse_model_json, "not json") and raises(m.parse_model_json, "[1]") and raises(m.parse_model_json, ""))
check("model reply empty", raises(m.parse_model_json, "{}") and raises(m.parse_model_json, '{"subject": ""}'))
check("model reply wrapper unwrapped", m.parse_model_json('{"description": {"subject": "fox"}, "instruction": "x"}')["subject"] == "fox")
check("model reply ok", m.parse_model_json('{"subject": "fox", "x": 1}')["subject"] == "fox")
j1 = {"subject": "a fox", "setting": "", "composition": "close up", "lighting": "dusk", "colors": "", "mood": "calm", "details": ["snow", "", "pines"]}
check("compose", m.compose_prompt(j1) == "a fox, close up, dusk, calm, snow, pines" and m.compose_prompt(j1) == m.compose_prompt(dict(reversed(list(j1.items())))))
check("compose empty", m.compose_prompt({}) == "")
check("seed: new by default, kept on request", m.pick_seed(42, False) != 42 and m.pick_seed(42, True) == 42 and m.pick_seed(None, True) > 0 and m.pick_seed("x", True) > 0)
check("seed: bad stored never kept", m.pick_seed(0, True) > 0 and m.pick_seed(2**53, True) != 2**53)

# routes on a temp store with a stubbed Ollama, engine and games probe
tmp = Path(tempfile.mkdtemp())
m.STATE, m.QUEUE, m.OUT = tmp / "state", tmp / "state" / "queue.json", tmp / "out"
m.streaming = lambda fresh=False: False
m._installed = lambda: True
day = m.OUT / "2026-01-01"
day.mkdir(parents=True)
(day / "aaaaaaaaaa-1.png").write_bytes(b"png")
side = day / "aaaaaaaaaa-1.json"
old_meta = {"prompt": "Ein Fuchs im Schnee", "style": "photo", "size": "square", "draft": True, "ts": 5}
side.write_text(json.dumps(old_meta))
calls = []
reply = {"subject": "Ein Fuchs", "setting": "im Schnee", "extra": "x"}


def fake_ollama(path, body=None, timeout=30):
    calls.append((path, body, m.GPU._is_owned()))
    return {"message": {"content": json.dumps(reply)}}


m._ollama = fake_ollama
ref = {"job": "aaaaaaaaaa", "n": 1}
r = m.image_json(ref)
b = calls[0][1]
check("json from prompt", r["json"]["subject"] == "Ein Fuchs" and "extra" not in r["json"] and "Ein Fuchs im Schnee" in b["messages"][1]["content"])
check("qwen call options", calls[0][0] == "/api/chat" and b["model"] == "qwen3.5:9b" and b["think"] is False and b["format"] == "json"
      and b["options"]["temperature"] == 0 and "keep_alive" not in b and calls[0][2])
check("json saved to sidecar", json.loads(side.read_text())["json"] == r["json"] and json.loads(side.read_text())["prompt"] == old_meta["prompt"])
m.image_json(ref)
check("json cached, no second call", len(calls) == 1)
check("old sidecar: no seed", "seed" not in json.loads(side.read_text()))
check("bad image refs", raises(m.image_json, {"job": "zz", "n": 1}) and raises(m.image_json, {"job": "bbbbbbbbbb", "n": 1}) and raises(m.image_json, {"job": "aaaaaaaaaa", "n": 9}))

tj = {**r["json"], "lighting": "Nacht", "colors": "blau"}  # the owner edits the fields by hand
check("tweak route is gone", not hasattr(m, "tweak") and not hasattr(m, "diff_json") and not hasattr(m, "SYS_TWEAK"))
check("json only calls qwen once so far", len(calls) == 1)

# regenerate: new queued job, same style/size/draft, parent + seed
res = m.regenerate({**ref, "json": tj, })
q = json.loads(m.QUEUE.read_text())
jb = q[-1]
check("regenerate queued", res["ok"] and jb["id"] == res["id"] and jb["status"] == "queued" and jb["count"] == 1 and jb["style"] == "photo" and jb["size"] == "square" and jb["draft"] is True)
check("regenerate prompt in code", jb["prompt"] == "Ein Fuchs, im Schnee, Nacht, blau" and jb["parent"] == {"job": "aaaaaaaaaa", "n": 1} and jb["json"] == tj)
check("old sidecar -> adult false", jb["adult"] is False and jb["style"] == "photo")
check("old sidecar -> random seed", isinstance(jb["seed"], int) and jb["seed"] > 0)
# the saved sidecar carries seed, parent and json
m._save_image(jb, 1, b"png2", 777)
nm = json.loads((m.OUT / f"{date.fromtimestamp(jb['created']).isoformat()}" / f"{jb['id']}-1.json").read_text())
check("new sidecar fields", nm["seed"] == 777 and nm["parent"] == jb["parent"] and nm["json"] == jb["json"] and nm["draft"] is True)
gal = [i for i in m._gallery() if i["job"] == jb["id"]]
check("gallery parent", gal and gal[0]["parent"] == {"job": "aaaaaaaaaa", "n": 1})
asrc = day / "aaaaaaaaaa-2.json"
(day / "aaaaaaaaaa-2.png").write_bytes(b"png")
asrc.write_text(json.dumps({"prompt": "p", "style": "anime", "size": "square", "draft": False, "adult": True, "ts": 6, "json": tj}))
ref2 = {"job": "aaaaaaaaaa", "n": 2}
check("regenerate carries adult from sidecar", m.regenerate({**ref2, "json": tj}) and json.loads(m.QUEUE.read_text())[-1]["adult"] is True)
m.regenerate({**ref2, "json": tj, "adult": False})
check("regenerate editor flips adult", json.loads(m.QUEUE.read_text())[-1]["adult"] is False)
aj = json.loads(m.QUEUE.read_text())[-1] | {"adult": True}
m._save_image(aj, 2, b"p", 1)
check("adult stored in sidecar", json.loads((m.OUT / date.fromtimestamp(aj["created"]).isoformat() / f"{aj['id']}-2.json").read_text())["adult"] is True)
# a source with a seed: new seed by default, the same one with keep_seed
meta2 = json.loads(side.read_text()) | {"seed": 4242}
side.write_text(json.dumps(meta2))
m.regenerate({**ref, "json": tj})
m.regenerate({**ref, "json": tj, "keep_seed": True})
m.regenerate({**ref, "json": tj, "fresh_seed": True})  # the old flag means nothing now
q = json.loads(m.QUEUE.read_text())
check("new seed by default", q[-3]["seed"] != 4242 and q[-1]["seed"] != 4242 and q[-3]["seed"] != q[-1]["seed"])
check("keep_seed reuses the source seed", q[-2]["seed"] == 4242)
check("parent recorded on each", all(x["parent"] == {"job": "aaaaaaaaaa", "n": 1} for x in q[-3:]))
check("edited fields cap on regenerate", m.regenerate({**ref, "json": {"subject": "y" * 500, "details": ["d"] * 9, "bogus": "x"}})["ok"]
      and len(json.loads(m.QUEUE.read_text())[-1]["json"]["subject"]) == 200 and len(json.loads(m.QUEUE.read_text())[-1]["json"]["details"]) == 6)
check("regenerate empty json", raises(m.regenerate, {**ref, "json": {}}))
m.streaming = lambda fresh=False: True
check("regenerate games guard", raises(m.regenerate, {**ref, "json": tj}))
m.streaming = lambda fresh=False: False
m._installed = lambda: False
check("regenerate engine check", raises(m.regenerate, {**ref, "json": tj}))
m._installed = lambda: True

# busy guard: queued jobs are in the file now
n_calls = len(calls)
side.write_text(json.dumps({k: v for k, v in meta2.items() if k != "json"}))
try:
    m.image_json(ref)
    busy_ok = False
except ValueError as e:
    busy_ok = str(e) == "An image is being made, try again when it is done"
check("busy 400 on json", busy_ok and len(calls) == n_calls)
check("busy guard on regenerate is not the qwen one: it queues", m.regenerate({**ref, "json": tj})["ok"] and len(calls) == n_calls)
check("cached json still served while busy", m.image_json({"job": jb["id"], "n": 1}) is not None)

# GPU lock: a qwen call and the worker never hold the GPU together
m._save([])
inside, release = threading.Event(), threading.Event()


def slow_ollama(path, body=None, timeout=30):
    inside.set()
    release.wait(5)
    return {"message": {"content": json.dumps({"subject": "fox"})}}


m._ollama = slow_ollama
th = threading.Thread(target=lambda: m.image_json(ref))
th.start()
inside.wait(5)
check("qwen call holds the GPU", not m.GPU.acquire(blocking=False) if threading.current_thread() else False)
ran = []


def fake_process(job):
    ran.append((job["id"], m.GPU._is_owned()))


m._process = fake_process
m._save([m.new_job(m.validate({"prompt": "p", "style": "anime", "size": "square", "count": 1}))])  # queued while qwen is in flight
wt = threading.Thread(target=m._step)
wt.start()
wt.join(0.4)
check("worker waits for qwen", wt.is_alive() and not ran)
release.set()
th.join(5)
wt.join(5)
check("worker runs after qwen, holding the GPU", len(ran) == 1 and ran[0][1] and not wt.is_alive())
check("lock free again", m.GPU.acquire(blocking=False) and not m.GPU.release())
# the other way round: while the worker has a job, qwen is refused and never reaches Ollama
m._ollama = fake_ollama
n_calls = len(calls)
side.write_text(json.dumps({k: v for k, v in meta2.items() if k != "json"}))  # no cached json, so qwen would be needed
m._save([{**m.new_job(m.validate({"prompt": "p", "style": "anime", "size": "square", "count": 1})), "status": "running"}])
check("qwen refused while a job runs", raises(m.image_json, ref) and len(calls) == n_calls)

# --- characters ---------------------------------------------------------------------------------------------------------
m.CHARS = m.STATE / "characters.json"
m.streaming = lambda fresh=False: False
m._installed = lambda: True
m._save([])
okc = {"name": " Test ", "gender": "girl", "age": 25, "hair": "black hair", "eyes": "blue eyes", "build": "", "outfit": "white shirt", "extras": "glasses", "note": "n", "adult": False}
check("char valid", m.validate_character(okc)["name"] == "Test" and m.validate_character(okc)["age"] == 25 and m.validate_character(okc)["adult"] is False)
check("age 18 accepted", m.validate_character({**okc, "age": 18})["age"] == 18)
for label, bad_age in (("17", 17), ("'18' string", "18"), ("18.5", 18.5), ("None", None), ("True", True), ("0", 0), ("-20", -20), ("1000", 1000)):
    check(f"age {label} rejected", raises(m.validate_character, {**okc, "age": bad_age}))
nob = {k: v for k, v in okc.items() if k != "age"}
check("age missing rejected", raises(m.validate_character, nob))
try:
    m.validate_character({**okc, "age": 17})
except ValueError as e:
    check("age message is clear", "18 or older" in str(e) and "whole number" in str(e))
check("name required", raises(m.validate_character, {**okc, "name": "  "}) and raises(m.validate_character, {**okc, "name": 5}))
check("gender checked", raises(m.validate_character, {**okc, "gender": "x"}) and raises(m.validate_character, {**okc, "gender": None}))
check("caps: look 120 / note 300 / name 60", m.validate_character({**okc, "hair": "h" * 120, "note": "n" * 300, "name": "a" * 60})["note"] == "n" * 300
      and raises(m.validate_character, {**okc, "hair": "h" * 121}) and raises(m.validate_character, {**okc, "extras": "e" * 121})
      and raises(m.validate_character, {**okc, "note": "n" * 301}) and raises(m.validate_character, {**okc, "name": "a" * 61}))
check("non-text look refused", raises(m.validate_character, {**okc, "eyes": 5}) and raises(m.validate_character, {**okc, "adult": "yes"}))
check("body not dict", raises(m.validate_character, None))
check("adult flag kept", m.validate_character({**okc, "adult": True})["adult"] is True)

cv = m.validate_character(okc)
check("compose is deterministic and ordered", m.compose_character(cv) == "1girl, solo, adult, black hair, blue eyes, white shirt, glasses"
      and m.compose_character(cv) == m.compose_character(dict(reversed(list(cv.items())))))
check("compose gender tags", m.compose_character({**cv, "gender": "boy"}).startswith("1boy, solo, adult") and m.compose_character({**cv, "gender": "other"}).startswith("1other, solo, adult"))
check("compose never carries age or note", "25" not in m.compose_character(cv) and "n," not in m.compose_character(cv).replace("blue eyes", ""))
check("compose empties skipped", m.compose_character({**cv, "hair": "", "eyes": " ", "outfit": "", "extras": ""}) == "1girl, solo, adult")
wsafe = gen.build(m.compose_character(cv), "anime", "portrait", False, 5, False)["2"]["inputs"]["text"]
wadult = gen.build(m.compose_character(cv), "anime", "portrait", False, 5, True)["2"]["inputs"]["text"]
check("adult flag reaches the anime prompt", " safe, 1girl" in wsafe and "safe" not in wadult and wadult.startswith("masterpiece, best quality, newest, absurdres, highres, 1girl"))

r1 = m.character_save(okc)
cid = r1["character"]["id"]
check("save creates", r1["ok"] and m.ID_RE.fullmatch(cid) and r1["character"]["reference"] is None and json.loads(m.CHARS.read_text())[0]["name"] == "Test")
check("no tmp left", not m.CHARS.with_suffix(".tmp").exists())
m.character_save({**okc, "id": cid, "name": "Test2", "adult": True})
cl = json.loads(m.CHARS.read_text())
check("save updates in place", len(cl) == 1 and cl[0]["name"] == "Test2" and cl[0]["adult"] is True and cl[0]["created"] == r1["character"]["created"])
check("save refuses bad age and unknown id", raises(m.character_save, {**okc, "age": 17}) and raises(m.character_save, {**okc, "id": "0123456789"}) and raises(m.character_save, {**okc, "id": "zz"}))
check("age 17 on update did not change the file", json.loads(m.CHARS.read_text())[0]["age"] == 25)

# looks job
sub = m.character_looks({"id": cid})
lj = next(j for j in json.loads(m.QUEUE.read_text()) if j["id"] == sub["id"])
check("looks job params", lj["count"] == 4 and lj["style"] == "anime" and lj["size"] == "portrait" and lj["draft"] is False and lj["character"] == cid
      and lj["adult"] is True and lj["prompt"] == m.compose_character(m.character_save({**okc, "id": cid, "name": "Test2", "adult": True})["character"]) + m.LOOKS_FRAMING and lj["status"] == "queued")
check("hair and eyes get their noun", m.compose_character({"gender": "boy", "hair": "black, long smooth", "eyes": "black", "build": "slim", "outfit": "", "extras": ""}) == "1boy, solo, adult, black hair, long smooth hair, black eyes, slim")
check("hair/eyes words are not doubled", m.compose_character({"gender": "girl", "hair": "black hair", "eyes": "blue eyes"}) == "1girl, solo, adult, black hair, blue eyes")
check("looks framing is face-forward", "looking at viewer" in m.LOOKS_FRAMING and "upper body" in m.LOOKS_FRAMING)
check("looks route validates id", raises(m.character_looks, {"id": "zz"}) and raises(m.character_looks, {"id": "0123456789"}) and raises(m.character_looks, None))
m.streaming = lambda fresh=False: True
check("looks: games guard", raises(m.character_looks, {"id": cid}))
m.streaming = lambda fresh=False: False
m._installed = lambda: False
check("looks: engine check", raises(m.character_looks, {"id": cid}))
m._installed = lambda: True
m._save([])
# sidecars carry the character
lj2 = {**lj, "created": 1767225600}
m._save_image(lj2, 1, b"look1", 111)
m._save_image(lj2, 2, b"look2", 222)
dd = m.OUT / date.fromtimestamp(lj2["created"]).isoformat()
check("looks sidecar carries character", json.loads((dd / f"{lj2['id']}-1.json").read_text())["character"] == cid)
lst = m.characters({})["characters"]
check("characters list has looks", len(lst) == 1 and sorted(i["n"] for i in lst[0]["looks"]) == [1, 2] and all(i["character"] == cid for i in lst[0]["looks"]))
check("gallery items carry character", all(i["character"] is None for i in m._gallery() if i["job"] == "aaaaaaaaaa") and any(i["character"] == cid for i in m._gallery()))

# reference: copy + seed; old sidecar without seed
rr = m.character_reference({"id": cid, "job": lj2["id"], "n": 2})
refp = m.OUT / "characters" / cid / "reference.png"
check("reference copied", refp.read_bytes() == b"look2" and rr["character"]["reference"] == {"job": lj2["id"], "n": 2, "seed": 222, "file": f"imagine/characters/{cid}/reference.png"})
check("reference stored in file", json.loads(m.CHARS.read_text())[0]["reference"]["seed"] == 222 and m.character_seed(json.loads(m.CHARS.read_text())[0]) == 222)
check("gallery ignores the characters dir", all("characters" not in i["file"] for i in m._gallery()))
rr = m.character_reference({"id": cid, "job": "aaaaaaaaaa", "n": 2})  # old sidecar, no seed
check("old sidecar -> seed None", rr["character"]["reference"]["seed"] is None and refp.read_bytes() == b"png" and m.character_seed(rr["character"]) is None)
check("reference input checks", raises(m.character_reference, {"id": cid, "job": "bbbbbbbbbb", "n": 1}) and raises(m.character_reference, {"id": "0123456789", "job": lj2["id"], "n": 1})
      and raises(m.character_reference, {"id": cid, "job": "zz", "n": 1}) and raises(m.character_reference, {"id": cid, "job": lj2["id"], "n": 9}))
m.character_reference({"id": cid, "job": lj2["id"], "n": 1})  # seed 111 for the Create tests below

# Create tab with a character: tags first, then the scene; adult follows the character unless flipped; same look reuses the seed
base = {"prompt": "sitting in a cafe", "style": "anime", "size": "square", "draft": True, "count": 1}
m.submit({**base, "character": cid, "same_look": True})
cj = json.loads(m.QUEUE.read_text())[-1]
check("submit composes count tags, scene, then character details", cj["prompt"] == "1girl, solo, adult, sitting in a cafe, black hair, blue eyes, white shirt, glasses" and cj["scene"] == "sitting in a cafe" and cj["character"] == cid)
check("submit: adult follows the character, Draft never uses the reference", cj["adult"] is True and "seed" not in cj and "ipadapter" not in cj and cj["style"] == "anime" and cj["size"] == "square")
m.submit({**base, "character": cid, "same_look": False, "adult": False, "draft": False})
cj = json.loads(m.QUEUE.read_text())[-1]
check("submit: owner flips adult off, Match reference off = plain job", cj["adult"] is False and "seed" not in cj and "ipadapter" not in cj)
m.submit({**base, "character": cid})
check("submit: same_look absent = random seed", "seed" not in json.loads(m.QUEUE.read_text())[-1])
check("submit: character needs anime + existing id", raises(m.submit, {**base, "style": "photo", "character": cid}) and raises(m.submit, {**base, "character": "0123456789"})
      and raises(m.submit, {**base, "character": "zz"}) and raises(m.submit, {**base, "character": cid, "same_look": "yes"}) and raises(m.submit, {**base, "character": cid, "prompt": " "}))
m.submit(base)
pj = json.loads(m.QUEUE.read_text())[-1]
check("submit without character is unchanged", pj["prompt"] == "sitting in a cafe" and "character" not in pj and pj["adult"] is False)
cs = json.loads(m.QUEUE.read_text())[-2] | {"created": 1767225600, "id": "cccccccccc"}
m._save_image({**cs, "character": cid}, 1, b"x", 111)
check("Create sidecar stores character + scene", json.loads((dd / "cccccccccc-1.json").read_text())["character"] == cid and json.loads((dd / "cccccccccc-1.json").read_text())["scene"] == "sitting in a cafe")
# seeds in the worker request: a character's seed is used for image 1 only
reqs = []
m._gen = lambda req, timeout=60: (reqs.append(req), {"event": "saved", "png_b64": "eA==", "seed": 9})[1]
m._one({**cs, "character": cid, "seed": 111, "count": 4}, 1)
m._one({**cs, "character": cid, "seed": 111, "count": 4}, 2)
check("same-look seed only on image 1", reqs[0].get("seed") == 111 and "seed" not in reqs[1])
m._one({k: v for k, v in cs.items() if k != "character"} | {"seed": 5}, 2)
check("regenerate seed unchanged (any image)", reqs[2].get("seed") == 5)

# limit and delete
m._save([])
chars = json.loads(m.CHARS.read_text())
m._chars_save(chars + [{**chars[0], "id": f"{i:010x}"} for i in range(1, 50)])
check("50 characters stored", len(m._chars_load()) == 50)
check("51st refused", raises(m.character_save, okc) and len(m._chars_load()) == 50)
check("update still fine at the limit", m.character_save({**okc, "id": cid})["ok"])
m._chars_save(chars)
n_png = len(list(m.OUT.glob("*/*.png")))
check("delete route checks", raises(m.character_delete, {"id": "zz"}) and raises(m.character_delete, {"id": "0123456789"}) and raises(m.character_delete, None))
check("delete ok", m.character_delete({"id": cid})["ok"] and m._chars_load() == [])
check("delete removes the reference copy only", not refp.exists() and not refp.parent.exists() and len(list(m.OUT.glob("*/*.png"))) == n_png - 0 and (dd / f"{lj2['id']}-1.png").is_file() and (dd / f"{lj2['id']}-2.png").is_file())
check("gallery images stay, character link stays in the sidecar", any(i["character"] == cid for i in m._gallery()))
check("submit with a deleted character refused", raises(m.submit, {**base, "character": cid}))

# --- stage A: batch, rating, set, cleanup ---------------------------------------------------------------------------------
import random as _rnd
m._ollama = fake_ollama
m._save([])
sc = m.character_save({**okc, "name": "Stage"})["character"]["id"]
other = m.character_save({**okc, "name": "Other"})["character"]["id"]
check("batch needs a reference", raises(m.character_batch, {"id": sc}) and m._load() == [])
check("batch bad id", raises(m.character_batch, {"id": "zz"}) and raises(m.character_batch, None) and raises(m.character_batch, {"id": "0123456789"}))
for seed in range(40):
    ps = m.batch_prompts("base", _rnd.Random(seed))
    ok = len(set(ps)) == 4
    for axis in m.VARIATIONS.values():
        ok = ok and sorted(next(a for a in axis if a in p) for p in ps) == sorted(axis)
    if not ok:
        break
check("batch_prompts: 4 distinct, every axis differs per image (40 seeds)", ok and all(p.startswith("base, ") for p in ps))
dA = m.OUT / "2026-02-01"
dA.mkdir(parents=True, exist_ok=True)


def mkimg(jid, n, cid, prompt="p"):
    (dA / f"{jid}-{n}.png").write_bytes(b"png-" + jid.encode() + str(n).encode())
    (dA / f"{jid}-{n}.json").write_text(json.dumps({"prompt": prompt, "style": "anime", "size": "portrait", "draft": False, "ts": 9, "seed": 3, "character": cid, "scene": ""}))


mkimg("1111111111", 1, sc, "look one")
m.character_reference({"id": sc, "job": "1111111111", "n": 1})
n0 = len(m._load())
r = m.character_batch({"id": sc})
bj = m._load()[-1]
check("batch queues ONE job of 4 anime non-draft", len(m._load()) == n0 + 1 and bj["id"] == r["id"] and bj["count"] == 4 and bj["style"] == "anime" and bj["draft"] is False
      and bj["batch"] is True and bj["character"] == sc and len(bj["variants"]) == 4 and len(set(bj["variants"])) == 4 and "seed" not in bj)
check("batch prompts carry character + framing", all(v.startswith(m.compose_character(m._char(sc)) + m.LOOKS_FRAMING + ", ") for v in bj["variants"]))
m.streaming = lambda fresh=False: True
check("batch obeys the games guard", raises(m.character_batch, {"id": sc}))
m.streaming = lambda fresh=False: False
m._installed = lambda: False
check("batch obeys the engine check", raises(m.character_batch, {"id": sc}))
m._installed = lambda: True
# worker path: image n gets variants[n-1]; saved sidecar holds the exact prompt + batch flag
sent = []
m._gen = lambda req, timeout=60: (sent.append(req), {"event": "saved", "png_b64": "eA==", "seed": 100 + len(sent)})[1]
bjob = {**bj, "created": 1770000000}
for i in range(1, 5):
    m._one(bjob, i)
check("worker sends variants[n-1] per image", [q["prompt"] for q in sent] == bj["variants"] and all("seed" not in q for q in sent))
d0 = m.OUT / "2026-02-02"
sc1 = json.loads((d0 / f"{bj['id']}-3.json").read_text())
check("sidecar: exact prompt, batch, character", sc1["prompt"] == bj["variants"][2] and sc1["batch"] is True and sc1["character"] == sc)
old = {k: v for k, v in bj.items() if k not in ("variants", "batch")}
sent.clear()
m._one({**old, "created": 1770000000}, 2)
check("old job without variants keeps working", sent[0]["prompt"] == bj["prompt"])
dA = d0  # the batch images were saved here by the worker path
J = bj["id"]
sd = m._set_dir(sc)
pub = lambda cid=sc: next(c for c in m.characters(None)["characters"] if c["id"] == cid)
p0 = pub()
check("reference is the first set image, rest unrated", p0["set"][0]["reference"] is True and len(p0["set"]) == 1 and len(p0["unrated"]) == 4 and p0["rejected_n"] == 0
      and p0["target"]["have"] == 1 and p0["target"]["min"] == 8 and p0["target"]["max"] == 12)
m.character_rate({"id": sc, "job": J, "n": 1, "verdict": "good"})
check("good copies png + sidecar", (sd / f"{J}-1.png").read_bytes() == (dA / f"{J}-1.png").read_bytes() and (sd / f"{J}-1.json").is_file())
p1 = pub()
check("good: in set with file + prompt, not unrated", [e["n"] for e in p1["set"]] == [1, 1] and p1["set"][1]["file"] == f"imagine/characters/{sc}/set/{J}-1.png"
      and p1["set"][1]["prompt"] == bj["variants"][0] and len(p1["unrated"]) == 3 and p1["target"]["have"] == 2)
m.character_rate({"id": sc, "job": J, "n": 2, "verdict": "bad"})
p2 = pub()
check("bad: rejected, no copy, not unrated", not (sd / f"{J}-2.png").exists() and p2["rejected_n"] == 1 and len(p2["unrated"]) == 2 and (dA / f"{J}-2.png").is_file())
m.character_rate({"id": sc, "job": J, "n": 1, "verdict": "bad"})
check("good -> bad removes the set copy", not (sd / f"{J}-1.png").exists() and pub()["rejected_n"] == 2 and len(pub()["set"]) == 1)
m.character_rate({"id": sc, "job": J, "n": 1, "verdict": "good"})
check("bad -> good leaves rejected", pub()["rejected_n"] == 1 and len(pub()["set"]) == 2)
m.character_rate({"id": sc, "job": J, "n": 1, "verdict": "clear"})
m.character_rate({"id": sc, "job": J, "n": 2, "verdict": "clear"})
p3 = pub()
check("clear: back to unrated, copy gone", p3["rejected_n"] == 0 and len(p3["set"]) == 1 and len(p3["unrated"]) == 4 and not (sd / f"{J}-1.png").exists())
check("rating validation", raises(m.character_rate, {"id": sc, "job": J, "n": 1, "verdict": "meh"}) and raises(m.character_rate, {"id": sc, "job": J, "n": 1})
      and raises(m.character_rate, {"id": sc, "job": "zz", "n": 1, "verdict": "good"}) and raises(m.character_rate, {"id": sc, "job": J, "n": 9, "verdict": "good"})
      and raises(m.character_rate, {"id": "zz", "job": J, "n": 1, "verdict": "good"}) and raises(m.character_rate, {"id": "0123456789", "job": J, "n": 1, "verdict": "good"})
      and raises(m.character_rate, {"id": sc, "job": "2222222222", "n": 1, "verdict": "good"}) and raises(m.character_rate, None))
check("the reference itself cannot be rated", raises(m.character_rate, {"id": sc, "job": "1111111111", "n": 1, "verdict": "bad"}))
mkimg("3333333333", 1, other)
check("another character's image cannot go in the set", raises(m.character_rate, {"id": sc, "job": "3333333333", "n": 1, "verdict": "good"}))
# set limit (reference counts)
cs_ = m._chars_load()
for c_ in cs_:
    if c_["id"] == sc:
        c_["set"] = [{"job": f"{i:010x}", "n": 1, "file": "x", "prompt": ""} for i in range(1, 59)]
m._chars_save(cs_)
m.character_rate({"id": sc, "job": J, "n": 3, "verdict": "good"})
check("set holds 60 with the reference", len(pub()["set"]) == 60)
check("set limit: 61st refused", raises(m.character_rate, {"id": sc, "job": J, "n": 4, "verdict": "good"}) and len(pub()["set"]) == 60)
check("bad still works when full", m.character_rate({"id": sc, "job": J, "n": 4, "verdict": "bad"})["ok"])
# cleanup
mkimg("4444444444", 1, other)
cs_ = m._chars_load()
for c_ in cs_:
    if c_["id"] == other:
        c_["rejected"] = [{"job": "4444444444", "n": 1}]
    if c_["id"] == sc:
        c_["rejected"] = [{"job": J, "n": 4}, {"job": "4444444444", "n": 1}]  # the second is not this character's: must survive
m._chars_save(cs_)
check("cleanup deletes only this character's rejected files", m.character_cleanup({"id": sc})["deleted"] == 1 and not (dA / f"{J}-4.png").exists() and not (dA / f"{J}-4.json").exists()
      and (dA / f"{J}-3.png").is_file() and (dA / "4444444444-1.png").is_file() and (dA / "3333333333-1.png").is_file() and (sd / f"{J}-3.png").is_file())
check("cleanup empties the list, leaves the other's", pub()["rejected_n"] == 0 and pub(other)["rejected_n"] == 1)
check("cleanup bad id", raises(m.character_cleanup, {"id": "zz"}) and raises(m.character_cleanup, {"id": "0123456789"}) and raises(m.character_cleanup, None))
# --- uploads (own pictures) ---------------------------------------------------------------------------------------------
import io
import re
from PIL import Image
up_id = m.character_save({**okc, "name": "Up"})["character"]["id"]
up_id2 = m.character_save({**okc, "name": "Up2"})["character"]["id"]


def png_bytes(size=(64, 48), color=(200, 30, 30), fmt="PNG", **kw):
    b = io.BytesIO()
    Image.new("RGB", size, color).save(b, fmt, **kw)
    return b.getvalue()


def up(raw, name="a.png", cid=None, **kw):
    return m.character_upload({"id": cid or up_id, "name": name, "data": base64.b64encode(raw).decode(), "ack": True, **kw})


upset = lambda cid=up_id: next(c for c in m.characters(None)["characters"] if c["id"] == cid)["set"]
good_png = png_bytes()
check("upload: ack required", raises(m.character_upload, {"id": up_id, "name": "a.png", "data": base64.b64encode(good_png).decode()})
      and raises(m.character_upload, {"id": up_id, "name": "a.png", "data": base64.b64encode(good_png).decode(), "ack": "true"})
      and raises(m.character_upload, {"id": up_id, "name": "a.png", "data": base64.b64encode(good_png).decode(), "ack": 1}) and upset() == [])
check("upload: bad id / missing data / bad base64", raises(m.character_upload, {"id": "zz", "data": "AAAA", "ack": True}) and raises(m.character_upload, {"id": "0123456789", "data": "AAAA", "ack": True})
      and raises(m.character_upload, {"id": up_id, "ack": True}) and raises(m.character_upload, {"id": up_id, "data": "!!!", "ack": True}) and raises(m.character_upload, None))
check("upload: text file named .png rejected", raises(up, b"hello, I am not a picture at all", "fake.png"))
gif = io.BytesIO()
Image.new("P", (8, 8)).save(gif, "GIF")
check("upload: GIF rejected", raises(up, gif.getvalue(), "a.gif") and upset() == [])
check("upload: right magic, broken body rejected", raises(up, b"\x89PNG\r\n\x1a\n" + b"junk" * 20) and raises(up, b"\xff\xd8\xff" + b"junk" * 20))
anim = io.BytesIO()
Image.new("RGB", (16, 16), "red").save(anim, "WEBP", save_all=True, append_images=[Image.new("RGB", (16, 16), "blue")], duration=100)
check("upload: animated WebP rejected", raises(up, anim.getvalue(), "a.webp"))
r1 = up(png_bytes(fmt="JPEG"), "../../etc/pa<ss>wd\n.jpg")
check("upload: JPEG accepted, entry shape", r1["entry"]["source"] == "upload" and r1["entry"]["prompt"] == "" and re.fullmatch(r"up-[a-f0-9]{10}\.png", r1["entry"]["file"].split("/")[-1])
      and r1["entry"]["file"].startswith(f"imagine/characters/{up_id}/set/") and (m.OUT / "characters" / up_id / "set" / r1["entry"]["file"].split("/")[-1]).is_file())
check("upload: WebP accepted", up(png_bytes(fmt="WEBP"), "b.webp")["ok"])
# metadata stripped
ex = Image.Exif()
ex[0x010F] = "SecretCam"
ex[0x0112] = 1
rm_ = io.BytesIO()
Image.new("RGB", (40, 30), (1, 2, 3)).save(rm_, "JPEG", exif=ex, icc_profile=b"x" * 40, comment=b"hidden")
check("fixture really has EXIF", Image.open(io.BytesIO(rm_.getvalue())).getexif().get(0x010F) == "SecretCam")
fn = up(rm_.getvalue(), "cam.jpg")["entry"]["file"]
sv = Image.open(m.OUT / fn.replace("imagine/", "", 1))
check("upload: saved as PNG without EXIF / ICC / text", sv.format == "PNG" and len(sv.getexif()) == 0 and not sv.info and sv.size == (40, 30))
pngm = io.BytesIO()
from PIL import PngImagePlugin
pi = PngImagePlugin.PngInfo()
pi.add_text("prompt", "secret workflow")
Image.new("RGB", (10, 10)).save(pngm, "PNG", pnginfo=pi)
fn2 = up(pngm.getvalue(), "t.png")["entry"]["file"]
check("upload: PNG text chunks dropped", not Image.open(m.OUT / fn2.replace("imagine/", "", 1)).info)
# resize
fn3 = up(png_bytes((5000, 1000)), "wide.png")["entry"]["file"]
check("upload: longest side shrunk to 2048", Image.open(m.OUT / fn3.replace("imagine/", "", 1)).size == (2048, 410))
fn4 = up(png_bytes((300, 200)), "small.png")["entry"]["file"]
check("upload: small stays small", Image.open(m.OUT / fn4.replace("imagine/", "", 1)).size == (300, 200))
# limits
big = b"\x89PNG\r\n\x1a\n" + b"\0" * (m.UP_MAX_BYTES + 1)
check("upload: over 10 MB rejected", raises(up, big, "big.png"))
check("upload: base64 over the cap rejected before decoding", raises(m.character_upload, {"id": up_id, "data": "A" * (m.UP_MAX_BYTES * 4 // 3 + 100), "ack": True}))
check("upload: 8001 px side rejected (decompression bomb)", raises(up, png_bytes((8001, 8)), "bomb.png") and raises(up, png_bytes((8000, 8000)), "bomb2.png"))
n_before = len(upset())
check("upload: nothing saved by the refusals", n_before == 6 and len(list((m.OUT / "characters" / up_id / "set").glob("*"))) == 6)
# listing + counter
ls = upset()
check("upload: listed in set with source upload, counted", [e.get("source") for e in ls] == ["upload"] * 6 and all(e["reference"] is False for e in ls)
      and next(c for c in m.characters(None)["characters"] if c["id"] == up_id)["target"]["have"] == 6)
check("name sanitising", m.clean_name("../../etc/pa<ss>wd\n.jpg") == "pa<ss>wd.jpg" and m.clean_name("a" * 90) == "a" * 60 and m.clean_name(None) == "" and m.clean_name("x\\y\\z.png") == "z.png"
      and m.clean_name("  a \t b\x00.png ") == "a b.png" and ls[0]["name"] == "pa<ss>wd.jpg")
# shared limit
cs_ = m._chars_load()
for c_ in cs_:
    if c_["id"] == up_id2:
        c_["set"] = [{"job": f"{i:010x}", "n": 1, "file": "x", "prompt": ""} for i in range(1, 60)]
m._chars_save(cs_)
check("upload: 60th fits", up(good_png, cid=up_id2)["ok"] and len(upset(up_id2)) == 60)
check("upload: set limit shared, 61st refused", raises(up, good_png, "a.png", up_id2) and len(upset(up_id2)) == 60)
# delete
fnu = ls[0]["file"].split("/")[-1]
check("delete: not an upload / bad name / other character", raises(m.character_upload_delete, {"id": up_id, "file": "up-0000000000.png"})
      and raises(m.character_upload_delete, {"id": up_id, "file": "../reference.png"}) and raises(m.character_upload_delete, {"id": up_id, "file": 5})
      and raises(m.character_upload_delete, {"id": up_id2, "file": fnu}) and raises(m.character_upload_delete, {"id": "zz", "file": fnu}) and raises(m.character_upload_delete, None))
check("delete: a rated (non-upload) set picture cannot be deleted here", raises(m.character_upload_delete, {"id": up_id2, "file": "x"}))
m.character_reference({"id": up_id, "job": "1111111111", "n": 1})
refp2 = m.OUT / "characters" / up_id / "reference.png"
check("delete: reference protected", refp2.is_file() and raises(m.character_upload_delete, {"id": up_id, "file": "reference.png"}) and refp2.is_file()
      and upset()[0]["reference"] is True)
check("delete: upload removed with its file", m.character_upload_delete({"id": up_id, "file": fnu})["ok"] and not (m.OUT / "characters" / up_id / "set" / fnu).exists()
      and fnu not in [e["file"] for e in upset()] and len(upset()) == 6 and (m.OUT / "characters" / up_id / "set" / ls[1]["file"].split("/")[-1]).is_file())
check("delete: twice refused", raises(m.character_upload_delete, {"id": up_id, "file": fnu}))
check("rating an upload's slot does not touch uploads", m.character_rate({"id": up_id, "job": J, "n": 1, "verdict": "clear"})["ok"] and len(upset()) == 6)
check("character delete removes uploads", m.character_delete({"id": up_id})["ok"] and not (m.OUT / "characters" / up_id).exists())
m.character_delete({"id": up_id2})
# proxy-equivalent validation (web/server/api/imagine/[...path].ts): same enums and id shapes as the agent
ts = (root / "addons/imagine/web/server/api/imagine/[...path].ts").read_text()
check("proxy: verdict enum + new routes", "const VERDICTS = ['good', 'bad', 'clear']" in ts and "character/batch" in ts and "character/cleanup" in ts and "character/rate" in ts
      and "const ID = /^[a-f0-9]{10}$/" in ts and m.VERDICTS == ("good", "bad", "clear") and m.ID_RE.pattern == "[a-f0-9]{10}")

# --- IP-Adapter: graph, agent flags, memory rules --------------------------------------------------------------------------
IPM = gen.MODELS["ipadapter"]
check("ipadapter table", IPM["adapter"] == "ip-adapter-plus_sdxl_vit-h.safetensors" and IPM["vision"] == "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors" and IPM["weight"] == 0.25)
wi = gen.build("x", "anime", "square", False, 7, False, "ref_abc.png")
ipn = {n["class_type"]: n["inputs"] for n in wi.values()}
check("ip graph: loaders + advanced node", ipn["LoadImage"] == {"image": "ref_abc.png"} and ipn["IPAdapterModelLoader"]["ipadapter_file"] == IPM["adapter"] and ipn["CLIPVisionLoader"]["clip_name"] == IPM["vision"])
a = ipn["IPAdapterAdvanced"]
check("ip graph: weight + settings", a["weight"] == 0.25 and a["weight_type"] == "linear" and a["start_at"] == 0.0 and a["end_at"] == 1.0 and a["combine_embeds"] == "concat" and a["embeds_scaling"] == "V only")
check("ip graph: wired to NoobAI before the KSampler", a["model"] == ["1", 0] and a["image"] == ["20", 0] and a["ipadapter"] == ["21", 0] and a["clip_vision"] == ["22", 0]
      and wi["5"]["inputs"]["model"] == ["23", 0] and wi["1"]["inputs"]["ckpt_name"] == "noobai-xl-1.1.safetensors" and wi["5"]["inputs"]["steps"] == 28)
check("ip graph: custom weight", gen.build("x", "anime", "square", False, 7, False, "r.png", 0.5)["23"]["inputs"]["weight"] == 0.5)
plain = gen.build("x", "anime", "square", False, 7, False)
check("ip graph: rest equals the plain graph", {k: v for k, v in wi.items() if k not in "20 21 22 23".split() and k != "5"} == {k: v for k, v in plain.items() if k != "5"}
      and {**wi["5"]["inputs"], "model": ["1", 0]} == plain["5"]["inputs"])
IPN = {"LoadImage", "IPAdapterModelLoader", "CLIPVisionLoader", "IPAdapterAdvanced"}
def has_ip(w):
    return bool(IPN & {n["class_type"] for n in w.values()})
check("no ip nodes: plain anime, Draft, photo, flux", not has_ip(plain) and not has_ip(gen.build("x", "anime", "square", True, 7, False, "r.png"))
      and not has_ip(gen.build("x", "photo", "square", False, 7, False, "r.png")) and not has_ip(gen.build("x", "pixel", "square", False, 7, False, "r.png")))
# gen.image(): reference upload, Draft / no reference never uploads
up, posted = [], []
gen.upload_reference = lambda cid, png: (up.append((cid, png)), f"ref_{cid}_u.png")[1]
gen._json = lambda path, data=None, timeout=30: (posted.append((path, data)), {"prompt_id": "p1"})[0] if path == "/prompt" else {"p1": {"status": {"status_str": "success", "completed": True}, "outputs": {}}}
gen.time.sleep = lambda s: None
rq = {"prompt": "x", "style": "anime", "size": "square", "draft": False, "reference_b64": "cG5n", "reference_id": "d21be05a53"}
gen.image(rq)
check("gen.image uploads the reference once and wires it", up == [("d21be05a53", b"png")] and posted[0][1]["prompt"]["20"]["inputs"]["image"] == "ref_d21be05a53_u.png")
posted.clear(); up.clear()
gen.image({**rq, "draft": True})
gen.image({k: v for k, v in rq.items() if k != "reference_b64"})
gen.image({**rq, "style": "photo"})
check("gen.image: Draft / no reference / not anime = no upload, no ip nodes", not up and len(posted) == 3 and not any(has_ip(p[1]["prompt"]) for p in posted))
# agent: which jobs carry ipadapter
m._save([])
ic = m.character_save({**okc, "name": "Ipc"})["character"]["id"]
check("batch needs the reference file", raises(m.character_batch, {"id": ic}))
dI = m.OUT / "2026-03-01"
dI.mkdir(parents=True, exist_ok=True)
(dI / "5555555555-1.png").write_bytes(b"REFPNG")
(dI / "5555555555-1.json").write_text(json.dumps({"prompt": "p", "style": "anime", "size": "portrait", "draft": False, "ts": 9, "seed": 321, "character": ic, "scene": ""}))
m.character_reference({"id": ic, "job": "5555555555", "n": 1})
m.character_batch({"id": ic})
bi = m._load()[-1]
check("batch job carries ipadapter + weight", bi["ipadapter"] is True and bi["ip_weight"] == 0.25 and bi["draft"] is False)
nd = {"prompt": "sitting on bench", "style": "anime", "size": "square", "draft": False, "count": 1, "character": ic}
m.submit({**nd, "same_look": True})
si = m._load()[-1]
check("Create + Match reference: ipadapter, no reference seed", si["ipadapter"] is True and si["ip_weight"] == 0.25 and "seed" not in si)
m.submit({**nd, "same_look": False})
check("Match reference off: plain", "ipadapter" not in m._load()[-1])
m.submit({**nd, "same_look": True, "draft": True})
check("Draft: never ipadapter", "ipadapter" not in m._load()[-1])
nref = m.character_save({**okc, "name": "NoRef"})["character"]["id"]
m.submit({**nd, "character": nref, "same_look": True})
check("character without reference: plain", "ipadapter" not in m._load()[-1])
m.submit({k: v for k, v in nd.items() if k != "character"})
check("job without a character: plain", "ipadapter" not in m._load()[-1])
m.character_looks({"id": ic})
check("looks job never ipadapter", "ipadapter" not in m._load()[-1])
reqs.clear()
m._gen = lambda req, timeout=60: (reqs.append(req), {"event": "saved", "png_b64": "eA==", "seed": 9})[1]
m._one({**si, "created": 1772323200}, 1)
check("worker sends the reference PNG + weight", base64.b64decode(reqs[0]["reference_b64"]) == b"REFPNG" and reqs[0]["reference_id"] == ic and reqs[0]["ip_weight"] == 0.25)
sj = json.loads((m.OUT / date.fromtimestamp(1772323200).isoformat() / f"{si['id']}-1.json").read_text())
check("sidecar stores ipadapter + weight", sj["ipadapter"] is True and sj["ip_weight"] == 0.25)
m._one({**si, "id": "dddddddddd", "created": 1772323200, "draft": True}, 1)
m._one({k: v for k, v in si.items() if k not in ("ipadapter", "ip_weight")} | {"id": "eeeeeeeeee", "created": 1772323200}, 1)
check("Draft / plain jobs send no reference", "reference_b64" not in reqs[1] and "reference_b64" not in reqs[2])
sp = json.loads((m.OUT / date.fromtimestamp(1772323200).isoformat() / "eeeeeeeeee-1.json").read_text())
check("plain sidecar: ipadapter false", sp["ipadapter"] is False and sp["ip_weight"] is None)

# memory: 9500 vs 7700, only kokoro / subgen, stopped.json before the stop, restored in the release path
check("requirements 9500 / 7700", m.need_mib({"ipadapter": True}) == 9500 and m.need_mib({}) == 7700 and m.FREE_MIB == 7700 and m.FREE_MIB_IP == 9500)
check("only kokoro and subgen may ever be stopped", m.OTHERS == ("kokoro", "subgen"))
m.STOPPED = m.STATE / "stopped.json"
cmds, running, free = [], {"kokoro", "subgen", "searxng"}, [4000]
snap = []


class R:
    def __init__(self, out="", rc=0):
        self.stdout, self.returncode, self.stderr = out, rc, ""


def fake_ai(*argv, timeout=60, stdin=None):
    cmds.append(argv)
    if argv[:2] == ("docker", "ps"):
        return R("\n".join(sorted(running)))
    if argv[:2] == ("docker", "stop"):
        snap.append(list(json.loads(m.STOPPED.read_text())))  # what stopped.json said at the moment of the stop
        running.discard(argv[2])
        free[0] += 3000
    if argv[:2] == ("docker", "start"):
        running.add(argv[2])
    return R()


m._ai, m._free_mib, m.OTHERS_WAIT, m.ROOM_WAIT = fake_ai, lambda: free[0], 0, 0
m.time.sleep = lambda s: None
m._save([{**m.new_job(m.validate({"prompt": "p", "style": "anime", "size": "square", "count": 1})), "id": "ffffffffff", "status": "running"}])
m._make_room("ffffffffff", 9500)
stops = [c[2] for c in cmds if c[:2] == ("docker", "stop")]
check("frees kokoro then subgen, one at a time, until enough", stops == ["kokoro", "subgen"] and free[0] == 10000)
check("stopped.json written BEFORE each stop", snap == [["kokoro"], ["kokoro", "subgen"]])
check("job phase cleared after", m._load()[0].get("phase") == "")
check("state tells voice is paused", m.state({})["voice_paused"] is True)
m._restore_others()
check("restore starts only what it stopped, searxng untouched", running == {"kokoro", "subgen", "searxng"} and not any(c[:2] == ("docker", "start") and c[2] == "searxng" for c in cmds)
      and json.loads(m.STOPPED.read_text()) == [] and not m.STOPPED.with_suffix(".tmp").exists())
check("state: voice not paused after restore", m.state({})["voice_paused"] is False)
# enough memory already: nothing is stopped
cmds.clear()
free[0] = 9600
m._make_room("ffffffffff", 9500)
check("nothing stopped when memory is enough", not [c for c in cmds if c[:2] == ("docker", "stop")] and m._stopped_load() == [])
# plain job needs 7700: kokoro alone is enough here
free[0] = 6000
m._make_room("ffffffffff", 7700)
check("plain job: stops only what it needs (kokoro)", [c[2] for c in cmds if c[:2] == ("docker", "stop")] == ["kokoro"] and m._stopped_load() == ["kokoro"])
m._restore_others()
# a container that was not running is never recorded or started
running.discard("subgen")
cmds.clear()
free[0] = 3000
try:
    m._make_room("ffffffffff", 9500)
except RuntimeError as e:
    short = "Not enough free GPU memory" in str(e)
check("subgen already stopped by someone else: not recorded; short on memory fails", short and m._stopped_load() == ["kokoro"])
m._restore_others()
check("never started what it did not stop", "subgen" not in running)
running.add("subgen")
# stopped.json can only ever name kokoro / subgen
m.STOPPED.write_text(json.dumps(["searxng", "kokoro", "rm -rf"]))
check("stopped.json filtered to the two names", m._stopped_load() == ["kokoro"])
check("stop refuses other names", m._stop_other("searxng") is False and not any(c[:3] == ("docker", "stop", "searxng") for c in cmds))
# restart recovery: listed + not running -> started; running ones untouched
running.discard("kokoro")
running.discard("subgen")
m._stopped_save(["kokoro", "subgen"])
cmds.clear()
m.sh = lambda *a, **k: ""
m.threading.Thread = lambda **k: type("T", (), {"start": lambda self: None})()
m._start()
starts = [c[2] for c in cmds if c[:2] == ("docker", "start")]
check("recovery on restart starts what stopped.json lists", starts == ["kokoro", "subgen"] and {"kokoro", "subgen"} <= running and m._stopped_load() == [])
# the release path restores even when the chat model restart fails
m._stopped_save(["subgen"])
running.discard("subgen")
m._comfy_free = lambda: None
def boom(*a, **k):
    raise RuntimeError("pct failed")
m.sh = boom
W_ok = False
try:
    m._release()
except RuntimeError:
    W_ok = True
check("release restores containers even if the warm-model step fails", W_ok and "subgen" in running and m._stopped_load() == [] and m.W["engaged"] is False)
# a container that will not start stays listed
m._stopped_save(["subgen"])
running.discard("subgen")
m._ai = lambda *argv, timeout=60, stdin=None: R("" , 1) if argv[:2] == ("docker", "start") else R("")
m._restore_others()
check("failed start stays listed for the next try", m._stopped_load() == ["subgen"])
# proxy: upload routes validate like the agent
check("proxy: upload routes", "character/upload/delete" in ts and "const UPLOAD = /^up-[a-f0-9]{10}\\.png$/" in ts and "b?.ack !== true" in ts and "UPLOAD_B64" in ts
      and str(-(-m.UP_MAX_BYTES // 3) * 4) in str(-(-10 * 1024 * 1024 // 3) * 4))
# the ui strings
en = json.loads((root / "addons/imagine/web/i18n/locales/en.json").read_text())["imagine"]
check("i18n: upload rule line", en["chars"]["ownOnly"] == "My own pictures of an original character. No real people, no art of published characters." and en["chars"]["addPics"] == "Add pictures")
check("i18n: freeing, voice note, Match reference", en["freeing"] == "Freeing memory" and "Voice and subtitles are paused" in en["voicePaused"] and en["chars"]["sameLook"] == "Match reference")

print("FAILED: " + ", ".join(fails) if fails else "all passed")
sys.exit(1 if fails else 0)
