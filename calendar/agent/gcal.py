"""Calendar: Google Calendar API v3 for every account connected through agent/google_auth.py.

Google is the source of truth, nothing is stored except which calendars the owner hid (/var/lib/dash/calendar-prefs.json).
The agent SDK has only GET and POST routes, so edit and delete are POST /gcal/event/update and /gcal/event/delete.
Events are read expanded (singleEvents) so a repeating event arrives as one row per occurrence, carrying recurringEventId
and originalStartTime; "this event" writes that occurrence, "all events" writes the series. Reminders are Google's own.
"""
import json, os, threading, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dash_sdk import get, post, setting
import google_auth  # core agent dir module (on sys.path of the agent)

API = "https://www.googleapis.com/calendar/v3"
PREFS = Path(os.environ.get("GCAL_PREFS") or "/var/lib/dash/calendar-prefs.json")
TTL = 60
LOCK = threading.Lock()
_CACHE = {}  # key -> (expires, value)
_GEN = 0  # bumped by every write / toggle; a fetch that started before it must not store its (stale) result


class GErr(Exception):
    pass


def _call(account, method, path, query=None, body=None):
    url = API + path + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")
    data = json.dumps(body).encode() if body is not None else None
    for attempt in (0, 1):
        try:
            tok = google_auth.access_token(account)
        except Exception as e:
            raise GErr(str(e))
        req = urllib.request.Request(url, data=data, method=method, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:400]
            raise GErr(f"Google {e.code}: {text}")
        except Exception as e:
            if attempt:
                raise GErr(str(e))


def _safe(fn):
    def w(*a):
        try:
            return fn(*a)
        except GErr as e:
            return {"ok": False, "error": str(e)}
        except (ValueError, KeyError) as e:
            return {"ok": False, "error": str(e)}
    return w


def _hidden():
    try:
        return set(json.loads(PREFS.read_text()).get("hidden", []))
    except Exception:
        return set()


def _key(account, cid):
    return f"{account}|{cid}"


def _colors():
    with LOCK:
        hit = _CACHE.get("colors")
    if hit and hit[0] > time.time():
        return hit[1]
    accs = [a["email"] for a in google_auth.accounts() if a.get("ok")]
    out = {}
    if accs:
        out = {k: v["background"] for k, v in _call(accs[0], "GET", "/colors").get("event", {}).items()}
    with LOCK:
        _CACHE["colors"] = (time.time() + 86400, out)
    return out


def _calendars():
    hidden, out, errs = _hidden(), [], []
    for a in google_auth.accounts():
        if not a.get("ok"):
            errs.append({"account": a["email"], "error": a.get("detail", "reconnect")})
            continue
        try:
            items = _call(a["email"], "GET", "/users/me/calendarList", {"minAccessRole": "reader"}).get("items", [])
        except GErr as e:
            errs.append({"account": a["email"], "error": str(e)})
            continue
        for c in items:
            out.append({"id": c["id"], "summary": c.get("summaryOverride") or c.get("summary", c["id"]), "backgroundColor": c.get("backgroundColor", "#4285f4"),
                        "accessRole": c.get("accessRole"), "primary": bool(c.get("primary")), "timeZone": c.get("timeZone"),
                        "accountEmail": a["email"], "selected": _key(a["email"], c["id"]) not in hidden})
    return {"ok": True, "calendars": out, "errors": errs, "colors": _colors(), "week_start": setting("calendar", "week_start", "monday")}


def _norm(e, cal, colors):
    """a Google event as the page wants it (same shape for list results and for the answer to a create / update)"""
    cid = e.get("colorId")
    return {"id": e["id"], "calendarId": cal["id"], "accountEmail": cal["accountEmail"], "summary": e.get("summary", ""),
            "location": e.get("location", ""), "description": e.get("description", ""), "start": e.get("start"), "end": e.get("end"),
            "colorId": cid, "color": colors.get(cid) if cid else cal["backgroundColor"], "calendarName": cal["summary"],
            "recurringEventId": e.get("recurringEventId"), "originalStartTime": e.get("originalStartTime"),
            "writable": cal.get("accessRole") in ("owner", "writer"), "htmlLink": e.get("htmlLink")}


def _written(ev, acc, b):
    """the answer for a create / update: the normalised event, {id} when the calendar lookup fails, refetch for a series master"""
    if ev.get("recurrence"):
        return {"ok": True, "refetch": True}  # a series master: the occurrences are expanded by Google's list, not here
    try:
        cid = str(b.get("calendarId") or "")
        cal = next(c for c in _calendars()["calendars"] if c["accountEmail"] == acc and c["id"] == cid)
        return {"ok": True, "event": _norm(ev, cal, _colors())}
    except Exception:
        return {"ok": True, "event": {"id": ev.get("id")}}


def _one(cal, start, end, colors):
    q = {"timeMin": start, "timeMax": end, "singleEvents": "true", "orderBy": "startTime", "maxResults": 2500}
    items = _call(cal["accountEmail"], "GET", f"/calendars/{urllib.parse.quote(cal['id'], safe='')}/events", q).get("items", [])
    return [_norm(e, cal, colors) for e in items if e.get("status") != "cancelled"]


def _events(start, end):
    ck = f"ev|{start}|{end}"
    with LOCK:
        gen = _GEN
        hit = _CACHE.get(ck)
    if hit and hit[0] > time.time():
        return hit[1]
    cals = _calendars()
    colors, events, errs = cals["colors"], [], list(cals["errors"])
    for cal in cals["calendars"]:
        if not cal["selected"]:
            continue
        try:
            events += _one(cal, start, end, colors)
        except GErr as e:
            errs.append({"account": cal["accountEmail"], "calendar": cal["summary"], "error": str(e)})
    res = {"ok": True, "events": events, "errors": errs}
    with LOCK:
        if gen == _GEN:  # a write happened meanwhile: this result may predate it, do not keep it
            _CACHE[ck] = (time.time() + TTL, res)
    return res


def _drop_cache():
    global _GEN
    with LOCK:
        _GEN += 1
        for k in [k for k in _CACHE if k.startswith("ev|")]:
            del _CACHE[k]


def _target(b):
    acc, cal = str(b.get("account") or ""), str(b.get("calendarId") or "")
    if not acc or not cal:
        raise ValueError("account and calendarId are required")
    return acc, f"/calendars/{urllib.parse.quote(cal, safe='')}/events"


def _clean(body):
    body = dict(body or {})
    body.pop("reminders", None)
    return body


def _when(x):
    """a start/end value ({date} or {dateTime}) as a naive datetime (UTC when it carries an offset); None if unreadable"""
    try:
        if x.get("date"):
            return datetime.fromisoformat(x["date"][:10])
        d = datetime.fromisoformat(str(x["dateTime"]).replace("Z", "+00:00"))
        return d.astimezone(timezone.utc).replace(tzinfo=None) if d.tzinfo else d
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def _check_range(body):
    """Google answers timeRangeEmpty for end <= start (an all-day end date is exclusive, so it must be after the start too)"""
    s, e = _when(body.get("start") or {}), _when(body.get("end") or {})
    if s and e and e <= s:
        raise ValueError("End must be after start")


def _shift_series(master, body):
    """'all events': keep the series' first date, take the time of day and the length from the edited occurrence"""
    s, e = body.get("start"), body.get("end")
    if not s or not e:
        return
    ms = master["start"]
    if "date" in s:
        d0 = datetime.fromisoformat(s["date"]); d1 = datetime.fromisoformat(e["date"])
        first = datetime.fromisoformat(ms.get("date") or ms["dateTime"][:10])
        s["date"], e["date"] = first.date().isoformat(), (first + (d1 - d0)).date().isoformat()
    else:
        a = datetime.fromisoformat(s["dateTime"][:19]); b = datetime.fromisoformat(e["dateTime"][:19])
        first = (ms.get("dateTime") or ms["date"])[:10]
        na = datetime.fromisoformat(first + "T" + a.strftime("%H:%M:%S"))
        s["dateTime"], e["dateTime"] = na.strftime("%Y-%m-%dT%H:%M:%S"), (na + (b - a)).strftime("%Y-%m-%dT%H:%M:%S")


@get("/gcal/calendars")
def r_calendars(q):
    return _safe(_calendars)()


@get("/gcal/events")
def r_events(q):
    def v(k):
        x = q.get(k, "")
        return (x[0] if isinstance(x, list) else x) or ""
    start, end = v("start"), v("end")
    if not start or not end:
        return {"ok": False, "error": "start and end are required (RFC3339)"}
    return _safe(_events)(start, end)


@post("/gcal/select")
def r_select(b):
    def go(b):
        hid = _hidden()
        k = _key(str(b.get("account")), str(b.get("calendarId")))
        hid.discard(k) if b.get("selected") else hid.add(k)
        PREFS.parent.mkdir(parents=True, exist_ok=True)
        PREFS.write_text(json.dumps({"hidden": sorted(hid)}))
        _drop_cache()
        return {"ok": True}
    return _safe(go)(b)


@post("/gcal/event")
def r_create(b):
    def go(b):
        acc, path = _target(b)
        body = _clean(b.get("body"))
        _check_range(body)
        body["reminders"] = {"useDefault": True}
        ev = _call(acc, "POST", path, None, body)
        _drop_cache()
        return _written(ev, acc, b)
    return _safe(go)(b)


@post("/gcal/event/update")
def r_update(b):
    def go(b):
        acc, path = _target(b)
        eid, body = str(b.get("eventId") or ""), _clean(b.get("body"))
        if not eid:
            raise ValueError("eventId is required")
        _check_range(body)
        if b.get("scope") == "all":
            sid = str(b.get("recurringEventId") or eid)
            master = _call(acc, "GET", f"{path}/{urllib.parse.quote(sid, safe='')}")
            _shift_series(master, body)
            eid = sid
        else:
            body.pop("recurrence", None)  # one occurrence cannot carry a rule
        ev = _call(acc, "PATCH", f"{path}/{urllib.parse.quote(eid, safe='')}", None, body)
        _drop_cache()
        if b.get("scope") == "all":
            return {"ok": True, "refetch": True}
        return _written(ev, acc, b)
    return _safe(go)(b)


@post("/gcal/event/delete")
def r_delete(b):
    def go(b):
        acc, path = _target(b)
        eid = str(b.get("eventId") or "")
        if not eid:
            raise ValueError("eventId is required")
        if b.get("scope") == "all":
            eid = str(b.get("recurringEventId") or eid)
        _call(acc, "DELETE", f"{path}/{urllib.parse.quote(eid, safe='')}")
        _drop_cache()
        return {"ok": True, "eventId": eid, "scope": b.get("scope")}
    return _safe(go)(b)
