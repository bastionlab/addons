"""Extra public data for the model ranking, none of it needs a key: the LMArena human-preference leaderboard (the
lmarena-ai/leaderboard-dataset on Hugging Face, read through the datasets-server JSON API, `latest` splits only) and
OpenRouter's public model list (price, context, release, capabilities). Each is fetched at most once a day, cached under
/var/lib/dash-ai and served stale when the source is down. One name normaliser matches them to the ZeroEval rows."""
import json, re, threading, time, urllib.parse, urllib.request

from cookbook import DIR, _atomic, _read

UA = "bastion-dash (self-hosted dashboard; one fetch per day)"
TTL = 24 * 3600
RETRY = 1800  # after a failed refresh, wait this long before trying again
ARENA = DIR / "arena.json"
ARENA_URL = "https://datasets-server.huggingface.co/rows?dataset=lmarena-ai/leaderboard-dataset&config=text&split=latest"
ARENA_CATS = ("overall", "coding")  # rows are sorted by category in the dataset
OR = DIR / "openrouter.json"
OR_URL = "https://openrouter.ai/api/v1/models"
_busy, _tried = set(), {}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read(12_000_000))


# ---------------------------------------------------------------- name normaliser
QUAL = {"high", "medium", "low", "xhigh", "max", "thinking", "reasoning", "instant", "preview", "latest", "exp"}


def norm(s):
    """'anthropic/claude-sonnet-4.5:free', 'Claude Sonnet 4.5 (20250929)' and 'claude-sonnet-4-5-20250929' all give
    'claude-sonnet-4-5'. Qualifiers in brackets (High, Thinking 16K) are dropped; variants are told apart elsewhere."""
    s = re.sub(r"\([^)]*\)", " ", str(s).lower().split(":")[0])
    s = s.split("/", 1)[-1]
    s = re.sub(r"[\s._]+", "-", s.strip())
    s = re.sub(r"-(latest|preview|instruct|chat)(?=-|$)", "", s)
    s = re.sub(r"-\d{4}-\d{2}-\d{2}(?=-|$)|-\d{8}(?=-|$)|-2[0-9](?:0[1-9]|1[0-2])$", "", s)
    s = re.sub(r"^(gemma|llama|phi|qwen|mistral)(\d)", r"\1-\2", s)
    return re.sub(r"-+", "-", s).strip("-")


def _date(s):
    m = re.search(r"(20\d{6})", str(s))
    return m.group(1) if m else None


def _prefix_ok(rest):
    # what may follow a shared prefix: only qualifiers and version dates, so 'gpt-5' never grabs 'gpt-5-mini'
    return all(p in QUAL or p.isdigit() for p in rest.split("-") if p)


def pick(index, key, raw_id=None, dup=False):
    """Entry of `index` (norm key -> [entries with .name .date .plain]) for a model, or None. Exact normalised key
    first, then a unique prefix match; ambiguous means unmatched. `dup` = several rows of the other source share this
    key, so only an entry with the same date counts."""
    cands = index.get(key)
    how = "exact"
    if not cands:
        hits = [k for k in index if k.startswith(key + "-") and _prefix_ok(k[len(key) + 1:])]
        if len(hits) != 1:
            return None, ""
        cands, how = index[hits[0]], "prefix"
    d = _date(raw_id) if raw_id else None
    if d and any(e.get("date") == d for e in cands):
        cands = [e for e in cands if e.get("date") == d]
    elif dup:
        return None, ""
    plain = [e for e in cands if e.get("plain")]
    pool = plain or cands
    return max(pool, key=lambda e: e.get("elo") or e.get("created") or 0), how


# ---------------------------------------------------------------- cached fetch (background refresh when stale)
def _cached(path, fetch):
    c = _read(path, {})
    fresh = c.get("data") and time.time() - c.get("at", 0) < TTL
    if fresh or (path in _busy) or time.time() - _tried.get(path, 0) < RETRY:
        return c.get("data"), c.get("at", 0)

    def run():
        _tried[path] = time.time()
        try:
            _atomic(path, {"at": time.time(), "data": fetch()})
        except Exception:
            pass
        finally:
            _busy.discard(path)

    _busy.add(path)
    if c.get("data"):  # stale beats waiting
        threading.Thread(target=run, daemon=True).start()
        return c["data"], c.get("at", 0)
    run()  # nothing cached yet: wait for it once
    c = _read(path, {})
    return c.get("data"), c.get("at", 0)


# ---------------------------------------------------------------- LMArena
def _page(off, n=100):
    time.sleep(0.3)
    d = _get(f"{ARENA_URL}&offset={off}&length={n}")
    return [r["row"] for r in d.get("rows", [])], d.get("num_rows_total", 0)


def _arena_fetch():
    rows, total = _page(0)
    out = {}
    for cat in ARENA_CATS:
        lo, hi = 0, total  # first offset whose category is >= cat (sorted by category)
        if cat != ARENA_CATS[0]:
            while lo < hi:
                mid = (lo + hi) // 2
                r, _ = _page(mid, 1)
                if r and r[0]["category"] < cat:
                    lo = mid + 1
                else:
                    hi = mid
        got, off = [], lo
        while off < total:
            r, _ = (rows, 0) if (off == 0 and rows) else _page(off)
            mine = [x for x in r if x["category"] == cat]
            got += mine
            if len(mine) < len(r) or not r:
                break
            off += 100
        out[cat] = [{"name": x["model_name"], "org": x.get("organization"), "elo": round(x["rating"]),
                     "rank": int(x["rank"]) if x.get("rank") is not None else None,
                     "votes": int(x["vote_count"]) if x.get("vote_count") is not None else None,
                     "date": x.get("leaderboard_publish_date")} for x in got if x.get("rating") is not None]
    if len(out["overall"]) < 20:
        raise ValueError("unexpected arena shape")
    return out


def arena():
    """({category: {norm key: [entries]}}, fetched_at, entry count) or ({}, 0, 0)"""
    data, at = _cached(ARENA, _arena_fetch)
    res = {}
    for cat, lst in (data or {}).items():
        idx = {}
        for e in lst:
            m = re.search(r"\(([^)]*)\)", e["name"])
            qual = re.sub(r"20\d{6}|[,\s]", "", m.group(1)) if m else ""
            idx.setdefault(norm(e["name"]), []).append({**e, "date": _date(e["name"]), "plain": not qual})
        res[cat] = idx
    return res, at, len((data or {}).get("overall", []))


# ---------------------------------------------------------------- OpenRouter
def _per_m(v):
    try:
        x = float(v) * 1e6
    except (TypeError, ValueError):
        return None
    return round(x, 4) if x >= 0 else None  # -1e6 marks routers with no fixed price


def _or_fetch():
    data = _get(OR_URL, 60).get("data", [])
    if len(data) < 20:
        raise ValueError("unexpected openrouter shape")
    out = []
    for m in data:
        mid = m.get("id") or ""
        if not mid or mid.startswith("~") or mid.endswith(":batch"):
            continue
        sp = m.get("supported_parameters") or []
        mods = (m.get("architecture") or {}).get("input_modalities") or []
        pr = m.get("pricing") or {}
        out.append({"id": mid, "name": re.sub(r"^[^:]+:\s*", "", m.get("name") or mid), "created": m.get("created"),
                    "context": m.get("context_length"), "pin": _per_m(pr.get("prompt")), "pout": _per_m(pr.get("completion")),
                    "tools": "tools" in sp, "vision": "image" in mods, "reasoning": "reasoning" in sp or "include_reasoning" in sp,
                    "open": bool(m.get("hugging_face_id")), "free": mid.endswith(":free")})
    return out


def openrouter():
    """(norm key -> entry, fetched_at); a plain id wins over its ':free' twin"""
    data, at = _cached(OR, _or_fetch)
    idx = {}
    for e in sorted(data or [], key=lambda e: (e["free"], len(e["id"]))):
        idx.setdefault(norm(e["id"]), [{**e, "plain": True}])
    return idx, at
