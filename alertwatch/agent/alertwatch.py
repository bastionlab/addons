"""Alert watch on the host: read-only helpers for the app (CT 104). GET /alertwatch/state returns what agent/alerts.py
keeps in /var/lib/dash/alerts.json (checked + log); GET /alertwatch/turns?ids=a-1,b-2 reads how the investigations'
Claude turns ended (/var/lib/dash-claude/<id>.jsonl, stream-json from claude -p)."""
import json
import re
from pathlib import Path

from dash_sdk import get

ALERTS = Path("/var/lib/dash/alerts.json")
TURNS = Path("/var/lib/dash-claude")
ID = re.compile(r"^[a-z0-9]+-\d+$")


@get("/alertwatch/state", quiet=True)
def state(q):
    try:
        d = json.loads(ALERTS.read_text())
    except (OSError, ValueError):
        return {"checked": None, "log": []}
    log = d.get("log")
    return {"checked": d.get("checked"), "log": log if isinstance(log, list) else []}


def _turn(tid):
    f = TURNS / f"{tid}.jsonl"
    text = None
    try:
        with f.open(errors="replace") as fh:
            for line in fh:  # big files: one line at a time
                if '"result"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("type") == "result":
                    text = str(o.get("result") or "")
    except OSError:
        return {"done": False, "cause": None, "allok": False}
    if text is None:
        return {"done": False, "cause": None, "allok": False}
    lines = [x.strip() for x in text.splitlines()]
    allok = text.lstrip().startswith("ALL-OK")
    if allok:
        cause = next((x for x in lines if x.startswith("ALL-OK")), "")[len("ALL-OK"):].strip()
    else:
        cause = next((x[len("CAUSE:"):].strip() for x in lines if x.startswith("CAUSE:")), None)
        if cause is None:
            cause = next((x for x in lines if x), "")
    return {"done": True, "cause": cause[:200], "allok": allok}


@get("/alertwatch/turns", quiet=True)
def turns(q):
    raw = q.get("ids") or ""
    raw = raw[0] if isinstance(raw, list) else raw
    ids = [i for i in (x.strip() for x in raw.split(",")) if ID.match(i)][:40]
    return {i: _turn(i) for i in ids}
