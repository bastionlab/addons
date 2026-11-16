"""Daily briefing on the host: the two things the app (CT 104) cannot do itself. GET /briefing/alerts lists the host's
current problems (agent/alerts.py problems(); the thresholds live there); POST /briefing/push sends the
briefing as a Web Push to the devices that have the Briefing topic on. Never Discord, never hooks.send."""
import re

import push  # core agent module (the agent's own dir is on sys.path, like google_auth in the calendar add-on)
from dash_sdk import get, post

# registered from the add-on so the core stays untouched; Settings → Notifications lists push.TOPICS. A device that was
# subscribed before the add-on existed has to switch the Briefing topic on there once.
push.TOPICS.setdefault("briefing", ("Briefing", "/briefing"))



def _plain(msg):
    """alerts.py writes Discord markdown (**bold**, `code`): plain text for the briefing"""
    return re.sub(r"\s+", " ", re.sub(r"[*`]", "", str(msg or ""))).strip()[:200]


@get("/briefing/alerts", quiet=True)
def alerts_now(q):
    """What is wrong right now: agent/alerts.py problems() run live and read-only (it only shells out to pvesh, zpool and df;
    main() is what pings and writes alerts.json, and it is not called). `open` in alerts.json is ping bookkeeping, not
    the current state. ?since=<epoch s> = the briefing's "new" cutoff: a failed backup task counts only if it ended
    after it. Errors are not caught: the caller must see a failure, never an empty list that reads as all clear."""
    import alerts as host_alerts  # core agent module; imported here so an import problem is an error of this call
    since = q.get("since")
    since = since[0] if isinstance(since, list) else since
    state = {"_task_seen": float(since)} if since else {}  # problems() mutates this scratch dict only
    return {"alerts": [m for m in (_plain(x) for x in host_alerts.problems(state).values()) if m]}


@post("/briefing/push")
def send(body):
    title = _plain((body or {}).get("title")) or "Daily briefing"
    text = _plain((body or {}).get("body"))
    if not text:
        raise ValueError("body is required")
    return {"ok": bool(push.notify("briefing", title[:120], text[:400], "/briefing"))}
