"""Model ranking + head-to-head for the Models page: public benchmark scores from llm-stats.com (the ZeroEval API
behind it, no login), fetched at most once a day and cached. Each row also carries the 3060 fit verdict (the
cookbook's calc), whether the model is installed in Ollama and its own speed from the benchmark tab. LMArena Elo, price,
context and capabilities from OpenRouter are merged in by name (sources.py). Read-only."""
import json, re, time, urllib.request

from dash_sdk import get

from cookbook import BENCH, DIR, UNCENSORED, DEFAULT_CTX, _api, _atomic, _read, _row
from sources import arena, norm, openrouter, pick

URL = "https://api.zeroeval.com/leaderboard/models/full"
CACHE = DIR / "zeroeval.json"
TTL = 24 * 3600
SOURCE = "llm-stats.com (ZeroEval)"
UA = "bastion-dash (self-hosted dashboard; one fetch per day)"
# four headline indexes: mean of the benchmarks a model has (needs at least one), 0..1 like the source
INDEXES = {"reasoning": ["gpqa", "hle", "aime_2025"],
           "coding": ["swe_bench_verified", "swe_bench_pro", "terminal_bench"],
           "knowledge": ["mmmlu", "mmmu", "simpleqa"],
           "agents": ["tau_bench_retail", "mcp_atlas", "browsecomp", "toolathlon", "osworld"]}
MIN_INDEXES = 2  # Score = mean of the indexes a model has, only when it has at least this many
# Ollama name -> ZeroEval id where the generic normaliser cannot get there
ALIAS = {"qwen3.5:9b": "qwen3.5-9b", "gemma4:12b": "gemma-4-12b-it", "qwen3.6:35b-a3b": "qwen3.6-35b-a3b"}


def _fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read(8_000_000))
    if not isinstance(data, list) or len(data) < 20:
        raise ValueError("unexpected leaderboard shape")
    return data


def _models():
    c = _read(CACHE, {})
    if c.get("models") and time.time() - c.get("at", 0) < TTL:
        return c["models"], c["at"]
    try:
        data = _fetch()
        _atomic(CACHE, {"at": time.time(), "models": data})
        return data, time.time()
    except Exception:
        if c.get("models"):  # stale beats nothing
            return c["models"], c.get("at", 0)
        raise


def _norm(s):
    s = s.lower().split("/")[-1].replace(":", "-").replace("_", "-")
    s = re.sub(r"-(latest|instruct|it|chat|thinking|q\d\w*|fp16|bf16)(?=-|$)", "", s)
    return re.sub(r"^(gemma|llama|phi|qwen|mistral)(\d)", r"\1-\2", s)


def _installed():
    try:
        names = [m["name"] for m in _api("/api/tags").get("models", []) if not UNCENSORED.search(m["name"])]
    except Exception:
        return {}
    return {n: n for n in names}


def _open(lic):
    return bool(lic) and str(lic).lower() not in ("proprietary", "unknown")


@get("/ai/compare")
def compare(q):
    models, at = _models()
    have = _installed()
    by_id = {m["model_id"]: m for m in models}
    by_norm = {}
    for m in models:
        by_norm.setdefault(_norm(m["model_id"]), m["model_id"])
    got = {}  # ZeroEval id -> installed Ollama name
    for n in have:
        mid = ALIAS.get(n) or by_norm.get(_norm(n))
        if mid in by_id:
            got[mid] = n
    bench = {}
    for r in _read(BENCH, {}).get("results", []):
        if not r.get("error") and r.get("tps"):
            bench[r["model"]] = r
    ar, ar_at, ar_n = arena()
    orx, or_at = openrouter()
    ze_keys = {}
    for m in models:
        ze_keys[norm(m["model_id"])] = ze_keys.get(norm(m["model_id"]), 0) + 1

    def arena_of(key, raw, dup):
        out = {}
        for cat, field in (("overall", "arena"), ("coding", "arena_coding")):
            e, _ = pick(ar.get(cat, {}), key, raw, dup) if ar.get(cat) else (None, "")
            out[field] = {"elo": e["elo"], "rank": e["rank"], "votes": e["votes"], "category": cat} if e else None
        return out

    rows, used = [], set()
    for m in models:
        mid = m["model_id"]
        key = norm(mid)
        dup = ze_keys[key] > 1
        idx = {}
        for name, keys in INDEXES.items():
            v = [m.get(f"{k}_score") for k in keys if m.get(f"{k}_score") is not None]
            idx[name] = {"v": round(sum(v) / len(v), 4), "n": len(v)} if v else None
        have_idx = [i["v"] for i in idx.values() if i]
        raw = {k: m[f"{k}_score"] for ks in INDEXES.values() for k in ks if m.get(f"{k}_score") is not None}
        opn = _open(m.get("license"))
        pb = m["params"] / 1e9 if m.get("params") else None
        if not opn:
            fit = "cloud"
        elif pb:
            fit = _row(mid, "", pb, pb * 0.6 + 0.2, 0, 0, "", DEFAULT_CTX, 0)["verdict"]
        else:
            fit = "unknown"
        own = bench.get(got.get(mid, ""), {})
        o, _ = pick(orx, key, mid, dup)
        if o:
            used.add(o["id"])
        a = arena_of(key, mid, dup)
        src = ["llm-stats"] + (["lmarena"] if a["arena"] or a["arena_coding"] else []) + (["openrouter"] if o else [])
        rows.append({"id": mid, "name": m.get("name") or mid, "org": m.get("organization") or "",
                     "params_b": round(pb, 1) if pb else None, "context": m.get("context") or (o or {}).get("context"),
                     "release_date": m.get("release_date"), "license": m.get("license"), "open": opn,
                     "is_moe": bool(m.get("is_moe")), "multimodal": bool(m.get("multimodal")),
                     "price_in": m["input_price"] if m.get("input_price") is not None else (o or {}).get("pin"),
                     "price_out": m["output_price"] if m.get("output_price") is not None else (o or {}).get("pout"),
                     "indexes": idx, "bench": raw,
                     "score": round(sum(have_idx) / len(have_idx), 4) if len(have_idx) >= MIN_INDEXES else None,
                     **a, "caps": {k: o[k] for k in ("tools", "vision", "reasoning")} if o else None, "sources": src,
                     "fit": fit, "installed": mid in got, "ollama": got.get(mid),
                     "tokens_per_s": own.get("tps"), "ttft_ms": own.get("ttft_ms")})
    # OpenRouter models the benchmark source lacks: listed with price, context and release only
    for key, lst in orx.items():
        o = lst[0]
        if o["id"] in used:
            continue
        a = arena_of(key, o["id"], False)
        rows.append({"id": "or:" + o["id"], "name": o["name"], "org": o["id"].split("/")[0], "params_b": None,
                     "context": o["context"], "release_date": time.strftime("%Y-%m-%d", time.gmtime(o["created"])) if o.get("created") else None,
                     "license": None, "open": o["open"], "is_moe": False, "multimodal": o["vision"],
                     "price_in": o["pin"], "price_out": o["pout"], "indexes": {k: None for k in INDEXES}, "bench": {}, "score": None,
                     **a, "caps": {k: o[k] for k in ("tools", "vision", "reasoning")},
                     "sources": (["lmarena"] if a["arena"] or a["arena_coding"] else []) + ["openrouter"],
                     "fit": "unknown" if o["open"] else "cloud", "installed": False, "ollama": None,
                     "tokens_per_s": None, "ttft_ms": None})
    n_ar = sum(1 for r in rows if r["arena"])
    srcs = [{"id": "llm-stats", "name": SOURCE, "at": at, "rows": len(models)},
            {"id": "lmarena", "name": "LMArena", "at": ar_at, "rows": ar_n, "matched": n_ar},
            {"id": "openrouter", "name": "OpenRouter", "at": or_at, "rows": len(orx), "matched": len(used)}]
    return {"fetched_at": at, "source": SOURCE, "sources": srcs, "groups": INDEXES, "rows": rows}
