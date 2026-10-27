"""Cost add-on: the sqlite store, settings and price table shared by the other cost_*.py modules"""
import json, os, sqlite3, threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def setting(addon, key, default=None):
    """owner settings via the agent's SDK; imported late so the standalone proxy (cost_proxy.py) never loads the agent"""
    from dash_sdk import setting as _s
    return _s(addon, key, default)


DB = Path(os.environ.get("DASH_COST_DB") or "/var/lib/dash-cost/cost.db")
TZ = ZoneInfo("Europe/Berlin")
LOCK = threading.Lock()  # one writer at a time; sqlite is cheap here

# USD per million tokens. TODO: these defaults are NOT verified against the current price list: check them
# (or override them with the `prices_json` setting, e.g. {"sonnet": {"in": 3, "out": 15}}).
# local_* = what the same tokens would cost on the hosted model, to compare with the local GPU.
PRICES = {
    "opus": {"in": 5.0, "out": 25.0, "cache_read": 0.5, "cache_write": 6.25},
    "sonnet": {"in": 3.0, "out": 15.0, "cache_read": 0.3, "cache_write": 3.75},
    "haiku": {"in": 1.0, "out": 5.0, "cache_read": 0.1, "cache_write": 1.25},
    "local_haiku": {"in": 1.0, "out": 5.0, "cache_read": 0.1, "cache_write": 1.25},
    "local_sonnet": {"in": 3.0, "out": 15.0, "cache_read": 0.3, "cache_write": 3.75},
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS claude (turn TEXT, kind TEXT, day TEXT, model TEXT, t_in INT, t_out INT,
  cache_read INT, cache_write INT, usd REAL, PRIMARY KEY (turn, model));
CREATE INDEX IF NOT EXISTS claude_day ON claude(day);
CREATE TABLE IF NOT EXISTS claude_run (session TEXT, model TEXT, t_in INT, t_out INT, cache_read INT, cache_write INT,
  usd REAL, PRIMARY KEY (session, model));  -- last running total of a resumed session (turn rows hold the increase)
CREATE TABLE IF NOT EXISTS plan (t INT PRIMARY KEY, five_h REAL, week REAL);
CREATE TABLE IF NOT EXISTS gpu_wh (day TEXT, cls TEXT, wh REAL, PRIMARY KEY (day, cls));
CREATE TABLE IF NOT EXISTS server_wh (day TEXT PRIMARY KEY, wh REAL);
CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, t REAL, day TEXT, job TEXT, source TEXT, model TEXT,
  path TEXT, status INT, t_in INT, t_out INT, eval_ns INT, load_ns INT);
CREATE INDEX IF NOT EXISTS calls_day ON calls(day);
"""
_ready = set()


def db():
    """a fresh connection (sqlite objects stay in their thread); creates the dir + schema on first use"""
    DB.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("PRAGMA journal_mode=WAL")
    if str(DB) not in _ready:
        c.executescript(SCHEMA)
        _ready.add(str(DB))
    return c


def day_of(t):
    """Berlin calendar day of an epoch (seconds)"""
    return datetime.fromtimestamp(t, TZ).strftime("%Y-%m-%d")


def num(key, default):
    try:
        return float(setting("cost", key, default))
    except (TypeError, ValueError):
        return float(default)


def prices():
    out = {k: dict(v) for k, v in PRICES.items()}
    raw = setting("cost", "prices_json", "")
    try:
        over = json.loads(raw) if isinstance(raw, str) and raw.strip() else (raw if isinstance(raw, dict) else {})
        for k, v in over.items():
            if isinstance(v, dict):
                out.setdefault(str(k), {}).update({a: float(b) for a, b in v.items() if a in ("in", "out", "cache_read", "cache_write")})
    except (ValueError, TypeError, AttributeError):
        pass  # a bad override must not break the page: keep the defaults
    return out
