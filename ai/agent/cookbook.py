"""Local AI cookbook on the host: what fits the GPU (live ollama.com catalogue, curated fallback), installed models
and disk, a per-model speed benchmark, which model each job uses, and what sits in VRAM. Pull / delete / unload stay
approve-then-run actions in localai.py; nothing here changes a model."""
import json, os, re, threading, time, urllib.request
from pathlib import Path

from dash_sdk import CFG, ct, get, ip, post, sh

from localai import MODEL_RE

DIR = Path("/var/lib/dash-ai")
UNCENSORED = re.compile(r"abliterated|uncensored|heretic", re.I)
VRAM_GB = 12.0     # RTX 3060
RESERVE_GB = 1.0   # desktop, Kokoro and CUDA context stay resident next to the model
RAM_GB = 32.0      # the CPU-offload budget is what is left of this after the box itself
RAM_RESERVE_GB = 10.0
DEFAULT_CTX = 8192
CATALOGUE_TTL = 24 * 3600
JOBS = ["ask", "notes", "voice", "gist", "chat", "research", "trending", "hunters", "money"]
BENCH_PROMPT = "Explain in about 120 words how a hash table handles collisions, then give one short Python example."
BENCH_TOKENS = 160

# kept if ollama.com is unreachable: name, size tag, params (B), size at the default Q4 (GB), context, year, family
FALLBACK = [
    ("qwen3.6", "35b-a3b", 35, 22.0, 262144, 2026, "Qwen"),
    ("qwen3.5", "9b", 9.7, 6.6, 262144, 2026, "Qwen"),
    ("qwen3.5", "4b", 4.5, 3.4, 262144, 2026, "Qwen"),
    ("gemma4", "12b", 12, 7.6, 131072, 2026, "Gemma"),
    ("gpt-oss", "20b", 21, 13.0, 131072, 2025, "gpt-oss"),
    ("qwen3-coder", "30b", 30, 19.0, 262144, 2025, "Qwen"),
    ("mistral-small3.2", "24b", 24, 15.0, 131072, 2025, "Mistral"),
    ("gemma3", "12b", 12, 8.1, 131072, 2025, "Gemma"),
    ("gemma3", "4b", 4, 3.3, 131072, 2025, "Gemma"),
    ("qwen3", "14b", 14.8, 9.3, 40960, 2025, "Qwen"),
    ("qwen3", "8b", 8.2, 5.2, 40960, 2025, "Qwen"),
    ("phi4", "14b", 14.7, 9.1, 16384, 2024, "Phi"),
    ("llama3.2", "3b", 3.2, 2.0, 131072, 2024, "Llama"),
    ("llama3.1", "8b", 8, 4.9, 131072, 2024, "Llama"),
]
SIZE_TAG = re.compile(r"^(?:e?(\d+(?:\.\d+)?)b|(\d+)x(\d+(?:\.\d+)?)b)$")


def ollama_url():
    return f"http://{ip('ai')}:11434"


def _atomic(path, data):
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    os.replace(tmp, path)


def _read(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _api(path, data=None, timeout=10):
    req = urllib.request.Request(ollama_url() + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json", "X-Job": "dash"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


# ---------- catalogue + fit

def _kv_gb(params, ctx):
    """rough KV cache at `ctx` tokens: about 1 GB per 8k tokens for an 8B model with grouped-query attention"""
    return ctx / 8192 * 0.9 * (max(params, 1) / 8) ** 0.7


def _row(name, tag, params, size, ctx_max, year, family, ctx, order, caps=None):
    usable = VRAM_GB - RESERVE_GB
    kv = _kv_gb(params, min(ctx, ctx_max or ctx))
    need = size + kv + 0.4
    if need <= usable:
        verdict = "fits"
    elif size <= usable + RAM_GB - RAM_RESERVE_GB:
        verdict = "partial"
    else:
        verdict = "no"
    return {"model": f"{name}:{tag}", "name": name, "tag": tag, "family": family, "params": params,
            "size_gb": round(size, 1), "kv_gb": round(kv, 1), "need_gb": round(need, 1), "ctx_max": ctx_max,
            "year": year, "verdict": verdict, "gpu_pct": min(100, round(usable / need * 100)) if need else 100,
            "caps": caps or [], "order": order}


def _parse_library(html):
    """one entry per model card on ollama.com/library (sorted newest): name, capability tags, size tags, updated"""
    out = []
    for card in re.split(r'<li\s+class="flex items-baseline', html)[1:]:
        m = re.search(r'href="/library/([\w.-]+)"', card)
        if not m:
            continue
        sizes = re.findall(r'text-blue-600[^>]*>\s*([\w.]+)\s*</span>', card)
        caps = re.findall(r'text-indigo-600[^>]*>\s*([\w-]+)\s*</span>', card)
        upd = re.search(r'title="([A-Z][a-z]{2} \d+, (\d{4}) [^"]*)"', card)
        out.append({"name": m.group(1), "sizes": sizes, "caps": caps, "year": int(upd.group(2)) if upd else 0})
    return out


def _build(entries, ctx):
    rows = []
    for i, e in enumerate(entries):
        if "embedding" in e["caps"] or "cloud" in e["caps"]:
            continue
        for s in e["sizes"]:
            t = SIZE_TAG.match(s)
            if not t:
                continue
            params = float(t.group(1)) if t.group(1) else float(t.group(2)) * float(t.group(3))
            if params < 1 or params > 130:
                continue
            rows.append(_row(e["name"], s, params, params * 0.6 + 0.2, 0, e["year"], e["name"], ctx, i, e["caps"]))
    return rows


def _fallback(ctx):
    return [_row(n, t, p, s, c, y, f, ctx, i) for i, (n, t, p, s, c, y, f) in enumerate(FALLBACK)]


def _live_entries():
    cache = DIR / "catalogue.json"
    c = _read(cache, {})
    if c.get("entries") and time.time() - c.get("at", 0) < CATALOGUE_TTL:
        return c["entries"], "live", c["at"]
    try:
        req = urllib.request.Request("https://ollama.com/library?sort=newest", headers={"User-Agent": "bastion-dash"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read(3_000_000).decode("utf-8", "replace")
        entries = _parse_library(html)[:60]
        if len(entries) < 5:
            raise ValueError("library page changed")
        _atomic(cache, {"at": time.time(), "entries": entries})
        return entries, "live", time.time()
    except Exception:
        if c.get("entries"):  # an old copy beats the baked-in list
            return c["entries"], "cached", c.get("at", 0)
        return None, "fallback", 0


RANK = {"fits": 0, "partial": 1, "no": 2}


@get("/ai/catalogue")
def catalogue(q):
    ctx = max(2048, min(int(q.get("ctx") or DEFAULT_CTX), 131072))
    entries, source, at = _live_entries()
    rows = _build(entries, ctx) if entries else []
    if not rows:
        rows, source = _fallback(ctx), "fallback"
    # fit first, then the newest first (the library is sorted newest; the fallback lists newest first too)
    rows.sort(key=lambda r: (RANK[r["verdict"]], -r["year"], r["order"], -r["params"]))
    return {"source": source, "at": at, "ctx": ctx, "vram_gb": VRAM_GB, "reserve_gb": RESERVE_GB,
            "usable_gb": VRAM_GB - RESERVE_GB, "rows": rows[:120]}


# ---------- disk

@get("/ai/disk")
def disk(q):
    tags = _api("/api/tags").get("models", [])
    models = sorted(({"name": m["name"], "size": m.get("size", 0), "uncensored": bool(UNCENSORED.search(m["name"])),
                      "modified": m.get("modified_at", "")} for m in tags), key=lambda m: -m["size"])
    total = used = free = 0
    parts = sh("pct", "exec", str(ct("ai")), "--", "df", "-B1", "--output=size,used,avail", "/").split("\n")
    if len(parts) > 1 and len(parts[1].split()) == 3:
        total, used, free = (int(x) for x in parts[1].split())
    return {"models": models, "models_bytes": sum(m["size"] for m in models), "disk": {"total": total, "used": used, "free": free}}


# ---------- benchmark

BENCH = DIR / "bench.json"
BSTATE = {"running": False, "current": "", "error": ""}
BLOCK = threading.Lock()


def _bench_one(model):
    body = json.dumps({"model": model, "prompt": BENCH_PROMPT, "stream": True, "think": False, "keep_alive": 0,
                       "options": {"num_predict": BENCH_TOKENS, "temperature": 0}}).encode()
    req = urllib.request.Request(ollama_url() + "/api/generate", data=body, headers={"Content-Type": "application/json", "X-Job": "dash-bench"})
    t0 = time.time()
    ttft = None
    last = {}
    with urllib.request.urlopen(req, timeout=900) as r:
        for line in r:
            d = json.loads(line)
            if ttft is None and (d.get("response") or d.get("thinking")):
                ttft = time.time() - t0
            if d.get("done"):
                last = d
    n, dur = last.get("eval_count", 0), last.get("eval_duration", 0)
    return {"model": model, "ttft_ms": round((ttft or 0) * 1000), "tps": round(n / (dur / 1e9), 1) if dur else 0,
            "tokens": n, "load_ms": round(last.get("load_duration", 0) / 1e6)}


def _bench_run():
    warm = None
    try:
        ps = _api("/api/ps").get("models", [])
        warm = next((m["name"] for m in ps if _far(m.get("expires_at"))), None)
        names = [m["name"] for m in _api("/api/tags").get("models", []) if not UNCENSORED.search(m["name"])]
        res = []
        for n in names:
            BSTATE["current"] = n
            try:
                res.append(_bench_one(n))
            except Exception as e:
                res.append({"model": n, "error": str(e)[:120]})
            _atomic(BENCH, {"at": time.time(), "prompt_tokens": BENCH_TOKENS, "results": res, "partial": True})
        _atomic(BENCH, {"at": time.time(), "prompt_tokens": BENCH_TOKENS, "results": res})
    except Exception as e:
        BSTATE["error"] = str(e)[:200]
    finally:
        if warm:  # put the warm model back, as the warm-model timer would
            try:
                _api("/api/generate", {"model": warm, "keep_alive": -1}, timeout=300)
            except Exception:
                pass
        BSTATE.update(running=False, current="")


def _far(ts):
    """expires_at more than a day out = the warm model (keep_alive -1)"""
    try:
        from datetime import datetime
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() - time.time() > 86400
    except Exception:
        return False


@post("/ai/bench/start")
def bench_start(body):
    with BLOCK:
        if BSTATE["running"]:
            raise ValueError("a benchmark is already running")
        BSTATE.update(running=True, current="", error="")
    threading.Thread(target=_bench_run, daemon=True).start()
    return {"ok": True}


@get("/ai/bench", quiet=True)
def bench(q):
    return {**_read(BENCH, {"results": []}), **BSTATE}


# ---------- VRAM

def _gpu_label(pid, docker_names, ct_names):
    try:
        cg = Path(f"/proc/{pid}/cgroup").read_text()
        comm = Path(f"/proc/{pid}/comm").read_text().strip()
    except OSError:
        return "?"
    m = re.search(r"/lxc/(\d+)/", cg)
    cid = int(m.group(1)) if m else 0
    if cid == ct("ai") and "ollama.service" in cg:
        return "Ollama"
    if cid == ct("ai"):
        d = re.search(r"docker-([0-9a-f]{64})", cg)
        name = docker_names.get(d.group(1)) if d else None
        return {"kokoro": "Kokoro (read-aloud)", "subgen": "Subgen (Whisper)"}.get(name, name or comm)
    if cid == ct("games"):
        return "Games streaming"
    return ct_names.get(cid) or comm


@get("/ai/vram", quiet=True)
def vram(q):
    g = sh("nvidia-smi", "--query-gpu=memory.total,memory.used", "--format=csv,noheader,nounits").strip().split(",")
    total, used = (int(x) for x in g) if len(g) == 2 else (int(VRAM_GB * 1024), 0)
    apps = [l.split(",") for l in sh("nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits").strip().splitlines() if "," in l]
    docker = {}
    for l in sh("pct", "exec", str(ct("ai")), "--", "docker", "ps", "--no-trunc", "--format", "{{.ID}} {{.Names}}").splitlines():
        p = l.split()
        if len(p) == 2:
            docker[p[0]] = p[1]
    ct_names = {v["id"]: k for k, v in (CFG.get("cts") or {}).items() if isinstance(v, dict) and "id" in v}
    users = {}
    for pid, mb in apps:
        label = _gpu_label(int(pid), docker, ct_names)
        users[label] = users.get(label, 0) + int(mb)
    try:
        loaded = [{"name": m["name"], "size": m.get("size", 0), "vram": m.get("size_vram", 0), "warm": _far(m.get("expires_at")),
                   "ctx": m.get("context_length")} for m in _api("/api/ps").get("models", [])]
    except Exception:
        loaded = []
    return {"total_mb": total, "used_mb": used, "free_mb": max(total - used, 0), "reserve_mb": int(RESERVE_GB * 1024),
            "users": [{"label": k, "mb": v} for k, v in sorted(users.items(), key=lambda x: -x[1])], "loaded": loaded}


# ---------- which model for which job

JOBS_FILE = DIR / "jobs.json"


def _jobs():
    d = _read(JOBS_FILE, {})
    out = {}
    for k in JOBS:
        v = d.get(k, "")
        out[k] = v.get("model", "") if isinstance(v, dict) else v  # an object may carry an engine later
        if not isinstance(out[k], str):
            out[k] = ""
    return out


@get("/ai/jobs")
def jobs(q):
    return {"jobs": _jobs(), "keys": JOBS}


@post("/ai/jobs")
def jobs_set(body):
    job, model = str(body.get("job", "")), str(body.get("model", ""))
    if job not in JOBS:
        raise ValueError("unknown job")
    if model and (not MODEL_RE.match(model) or UNCENSORED.search(model)):
        raise ValueError("invalid model name")
    d = _read(JOBS_FILE, {})
    d[job] = model
    _atomic(JOBS_FILE, d)
    return {"jobs": _jobs(), "keys": JOBS}
