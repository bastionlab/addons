"""Cost add-on on the host: imports what Claude (chat turns + Learn lessons) cost, samples the plan windows,
and serves /cost/summary. GPU power lives in cost_gpu.py, the Ollama counting proxy in cost_proxy.py."""
import json, re, time, urllib.request
from pathlib import Path

from dash_sdk import get, on_start

import cost_gpu
from cost_db import DB, LOCK, day_of, db, num, prices

CHAT_DIR = Path("/var/lib/dash-claude")
LEARN_DIR = Path("/var/lib/dash-learn")
TURN = re.compile(r"[a-z0-9]+-(\d{13})\.jsonl")
SETTLE = 30  # s: a file touched this recently may still be written
GIVE_UP = 3600  # s: an old file without a result line is an aborted turn, remember it as empty
STATE = {"claude": None, "plan": None, "imported": 0}


def _result(f):
    """the last top-level {"type":"result"} object of a stream-json file"""
    last = None
    with open(f, errors="replace") as fh:
        for line in fh:
            if '"type":"result"' in line or '"type": "result"' in line:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("type") == "result":
                    last = d
    return last


FIELDS = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens", "costUSD")


def _rows(turn, kind, day, d, prev=None):
    """one row per model in modelUsage; ('' model, zeros) when there is none, so the file is not read again.
    modelUsage is a running total for the whole resumed session: with `prev` ({model: [5 fields]} of the turn
    before) the row holds the increase; a total that went down means the session was not restored: take it as is."""
    mu = (d or {}).get("modelUsage") or {}
    rows = []
    for m, u in mu.items():
        if not isinstance(u, dict):
            continue
        cur = [float(u.get(k) or 0) for k in FIELDS]
        old = (prev or {}).get(m)
        v = cur if not old or any(c < o for c, o in zip(cur, old)) else [c - o for c, o in zip(cur, old)]
        rows.append((turn, kind, day, m, *[int(x) for x in v[:4]], v[4]))
        if prev is not None:
            prev[m] = cur
    return rows or [(turn, kind, day, "", 0, 0, 0, 0, 0.0)]


def import_claude(chat_dir=CHAT_DIR, learn_dir=LEARN_DIR, now=None):
    """store every finished turn/lesson not stored yet; returns how many were added"""
    now = now or time.time()
    c = db()
    have = {r[0] for r in c.execute("SELECT DISTINCT turn FROM claude")}
    run = {}  # session id -> {model: last running total}, loaded lazily from claude_run
    new, runs, blocked = [], {}, set()
    for f in sorted(chat_dir.glob("*.jsonl"), key=lambda f: (f.name.split("-")[-1], f.name)):
        m = TURN.fullmatch(f.name)
        chat = f.name.rsplit("-", 1)[0]
        if not m or f.stem in have:
            continue
        age = now - f.stat().st_mtime
        res = _result(f) if age >= SETTLE and chat not in blocked else None
        if res is None and age < GIVE_UP:
            blocked.add(chat)  # a later turn of this chat must not be booked before this one (it needs its total)
            continue
        sid = (res or {}).get("session_id")
        if sid and sid not in run:
            run[sid] = {mo: [float(v) for v in vals] for mo, vals in
                        ((r[0], r[1:]) for r in c.execute("SELECT model,t_in,t_out,cache_read,cache_write,usd FROM claude_run WHERE session=?", (sid,)))}
        new.append(_rows(f.stem, "chat", day_of(int(m[1]) / 1000), res, run[sid] if sid else None))
        if sid:
            runs[sid] = run[sid]
    for f in sorted(learn_dir.glob("*.out")):
        turn = f"learn-{f.stem}"
        age = now - f.stat().st_mtime
        if turn in have or age < SETTLE:
            continue
        try:
            d = json.loads(f.read_text(errors="replace"))
        except ValueError:
            d = None
        if not (isinstance(d, dict) and d.get("type") == "result"):
            if age < GIVE_UP:
                continue  # still being written (the file stays empty until the lesson ends): look again later
            d = None
        new.append(_rows(turn, "learn", day_of(f.stat().st_mtime), d))
    if new:
        with LOCK, c:
            c.executemany("INSERT OR IGNORE INTO claude VALUES (?,?,?,?,?,?,?,?,?)", [r for rows in new for r in rows])
            c.executemany("INSERT OR REPLACE INTO claude_run VALUES (?,?,?,?,?,?,?)",
                          [(sid, mo, *[int(x) for x in v[:4]], v[4]) for sid, mm in runs.items() for mo, v in mm.items()])
    c.close()
    return len(new)


def sample_plan():
    """one plan row per usage snapshot (keyed by its own timestamp, so an unchanged snapshot is not written twice);
    a window whose reset time has passed since then is booked as 0 at its reset time"""
    from claude import claude_usage
    u = claude_usage(refresh=False)
    w = u.get("windows") or {}
    at, now = u.get("at"), time.time()
    if not at:
        return False
    cur = {k: (w.get(k) or {}).get("used") for k in ("five_hour", "seven_day")}
    if cur["five_hour"] is None and cur["seven_day"] is None:
        return False
    rows = {int(at): (cur["five_hour"], cur["seven_day"])}
    gone = {k: (w.get(k) or {}).get("resets") for k in cur}
    gone = {k: r for k, r in gone.items() if isinstance(r, (int, float)) and at < r <= now and cur[k] is not None}
    if gone:
        t = int(max(gone.values()))
        rows[t] = tuple(0.0 if k in gone else cur[k] for k in ("five_hour", "seven_day"))
    c = db()
    added = 0
    with LOCK, c:
        for t, v in rows.items():
            added += c.execute("INSERT OR IGNORE INTO plan VALUES (?,?,?)", (t, *v)).rowcount
    c.close()
    return bool(added)


def _loop(name, every, fn):
    while True:
        try:
            STATE[name] = {"at": int(time.time()), "result": fn()}
        except Exception as e:
            STATE[name] = {"at": int(time.time()), "error": str(e)[:200]}
        time.sleep(every)


@on_start
def claude_loop():
    _loop("claude", 300, lambda: import_claude())


@on_start
def plan_loop():
    time.sleep(20)
    _loop("plan", 900, sample_plan)


def summary(days):
    c = db()
    since = day_of(time.time() - days * 86400)
    out = {}

    def day(d):
        return out.setdefault(d, {"day": d, "claude": {"usd": 0.0, "by_model": {}, "turns": 0, "learn_usd": 0.0},
                                  "local": {"by_job": {}}, "gpu_wh": {k: 0.0 for k in ("ollama", "speech", "games", "idle", "other")},
                                  "server_wh": 0.0})
    turns = set()
    for turn, kind, d, model, i, o, cr, cw, usd in c.execute(
            "SELECT turn,kind,day,model,t_in,t_out,cache_read,cache_write,usd FROM claude WHERE day >= ?", (since,)):
        cl = day(d)["claude"]
        if kind == "chat" and (turn, d) not in turns:
            turns.add((turn, d))
            cl["turns"] += 1
        if not model:
            continue
        cl["usd"] += usd
        if kind == "learn":
            cl["learn_usd"] += usd
        m = cl["by_model"].setdefault(model, {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0, "usd": 0.0})
        m["in"] += i; m["out"] += o; m["cache_read"] += cr; m["cache_write"] += cw; m["usd"] += usd
    for d, job, n, i, o, ns in c.execute(
            "SELECT day,job,COUNT(*),SUM(t_in),SUM(t_out),SUM(eval_ns) FROM calls WHERE day >= ? GROUP BY day,job", (since,)):
        day(d)["local"]["by_job"][job] = {"calls": n, "in": i or 0, "out": o or 0, "eval_s": round((ns or 0) / 1e9, 1)}
    for d, cls, wh in c.execute("SELECT day,cls,wh FROM gpu_wh WHERE day >= ?", (since,)):
        day(d)["gpu_wh"][cls] = day(d)["gpu_wh"].get(cls, 0.0) + wh
    for d, wh in c.execute("SELECT day,wh FROM server_wh WHERE day >= ?", (since,)):
        day(d)["server_wh"] = wh
    plan = [{"t": t, "five_h": a, "week": b} for t, a, b in
            c.execute("SELECT t,five_h,week FROM plan WHERE t >= ? ORDER BY t", (time.time() - days * 86400,))]
    c.close()
    return {"settings": {"eur_kwh": num("eur_kwh", 0.38), "usd_eur": num("usd_eur", 0.92),
                         "idle_w": num("idle_w", 45), "max_w": num("max_w", 65)},
            "prices": prices(), "days": [out[k] for k in sorted(out)], "plan": plan,
            "proxy": proxy_state(),
            "power": {"shelly": cost_gpu.STATE.get("shelly_watts") is not None, "watts": cost_gpu.STATE.get("shelly_watts"),
                      "err": cost_gpu.STATE.get("shelly_err")},
            "server_estimated": True}


def proxy_state():
    """the proxy is its own service (dash-cost-proxy): ask it, don't share memory"""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11435/_cost/health", timeout=2) as r:
            d = json.loads(r.read())
        return {"ok": bool(d.get("ok")), "since": d.get("since"), "error": d.get("error")}
    except (OSError, ValueError):
        return {"ok": False, "since": None, "error": "dash-cost-proxy not reachable"}


@get("/cost/summary", quiet=True)
def cost_summary(q):
    try:
        n = int(q.get("days") or 30)
    except (TypeError, ValueError):
        raise ValueError("days must be a number")
    return summary(max(1, min(n, 400)))


@get("/cost/health", quiet=True)
def cost_health(q):
    return {"ok": True, "db": str(DB), "claude": STATE["claude"], "plan": STATE["plan"],
            "gpu": {"last": cost_gpu.STATE.get("last"), "watts": cost_gpu.STATE.get("watts"), "error": cost_gpu.STATE.get("error"),
                    "shelly_watts": cost_gpu.STATE.get("shelly_watts"), "shelly_err": cost_gpu.STATE.get("shelly_err")},
            "proxy": proxy_state()}
