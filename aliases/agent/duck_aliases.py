"""Aliases tab: your DuckDuckGo Email Protection @duck.com aliases, talked to the way DDG's own apps do

DDG has no public API and no way to list the aliases you made, so the list lives here
(/var/lib/dash-aliases/aliases.json, in the backup). Login = your Duck username + the one-time code DDG mails
to your forwarding inbox; the access token it gives back is kept in /etc/dash/secrets/aliases.json.
Endpoints (quack.duckduckgo.com/api, as in DDG's browsers): auth/loginlink, auth/login, email/dashboard,
POST email/addresses = new alias, GET/PUT email/addresses?address=…&active= = status / on-off.
Nothing can be deleted at DDG: "delete" = switch off (mail to it is dropped) and drop it from the list.
"""
import json, os, re, threading, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

from dash_sdk import get, post

API = "https://quack.duckduckgo.com/api"
DIR = Path("/var/lib/dash-aliases")
LIST = DIR / "aliases.json"
SECRET = Path("/etc/dash/secrets/aliases.json")
USER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
ALIAS_RE = re.compile(r"\b([a-z0-9][a-z0-9._-]{2,63})@duck\.com\b", re.I)
LOCK = threading.Lock()
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


# --- storage --------------------------------------------------------------------------------------------------
def _read(p, default):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return default


def _write(p, data, mode):
    p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.chmod(tmp, mode)
    tmp.replace(p)


def _secret():
    """{user, token, pending_user}; same {value, updated} shape as Settings' secrets so its inventory reads it"""
    return {k: (v or {}).get("value") for k, v in _read(SECRET, {}).items()}


def _save_secret(**kv):
    s = _read(SECRET, {})
    for k, v in kv.items():
        if v:
            s[k] = {"value": v, "updated": int(time.time())}
        else:
            s.pop(k, None)
    _write(SECRET, s, 0o600)


def _items():
    return _read(LIST, {}).get("aliases", [])


def _save(items):
    _write(LIST, {"aliases": items}, 0o600)


def _find(items, address):
    a = _addr(address)
    return next((i for i in items if i["address"] == a), None)


def _addr(v):
    m = ALIAS_RE.fullmatch(str(v or "").strip().lower())
    if not m:
        raise ValueError("not a @duck.com address")
    return m.group(0).lower()


def _text(v, n):
    return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


# --- DDG ------------------------------------------------------------------------------------------------------
def _ddg(method, path, query=None, token=None):
    url = f"{API}/{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
    req = urllib.request.Request(url, method=method, data=b"" if method in ("POST", "PUT") else None,
                                 headers={"User-Agent": UA, **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}
    except (urllib.error.URLError, TimeoutError) as e:
        raise ValueError(f"DuckDuckGo unreachable: {e}")


def _token():
    t = _secret().get("token")
    if not t:
        raise ValueError("not signed in to DuckDuckGo")
    return t


def _authed(method, path, query=None):
    code, j = _ddg(method, path, query, _token())
    if code in (401, 403):
        raise ValueError("DuckDuckGo login expired: sign in again")
    return code, j


# --- routes ---------------------------------------------------------------------------------------------------
@get("/aliases/list", quiet=True)
def list_route(q):
    s = _secret()
    return {"user": s.get("user"), "signed_in": bool(s.get("token")), "pending": s.get("pending_user"),
            "aliases": sorted(_items(), key=lambda i: -i.get("created", 0))}


@post("/aliases/login")
def login(body):
    """step 1: DDG mails a one-time passphrase to the inbox the Duck address forwards to"""
    user = str(body.get("user") or "").strip().lower().removesuffix("@duck.com")
    if not USER_RE.match(user):
        raise ValueError("your Duck username (the part before @duck.com)")
    code, _ = _ddg("GET", "auth/loginlink", {"user": user})
    if code != 200:
        raise ValueError("DuckDuckGo did not know that username")
    _save_secret(pending_user=user)
    return {"ok": True, "pending": user}


@post("/aliases/verify")
def verify(body):
    """step 2: the passphrase (words, as in the mail) → login token → the long-lived access token"""
    user = _secret().get("pending_user")
    if not user:
        raise ValueError("ask for a code first")
    words = str(body.get("otp") or "").split()
    if not words or len(" ".join(words)) > 200:
        raise ValueError("paste the passphrase from the mail")
    # DDG's own clients send the words joined by "+"; plain spaces as a fallback
    for otp in ("+".join(words), " ".join(words)):
        code, j = _ddg("GET", "auth/login", {"otp": otp, "user": user})
        if code == 200 and j.get("token"):
            break
    if code != 200 or not j.get("token"):
        raise ValueError("that code did not work (they expire quickly)")
    code, d = _ddg("GET", "email/dashboard", token=j["token"])
    access = (d.get("user") or {}).get("access_token") if code == 200 else None
    if not access:
        raise ValueError("DuckDuckGo signed you in but gave no access token")
    _save_secret(user=user, token=access, pending_user=None)
    return list_route({})


@post("/aliases/logout")
def logout(body):
    _save_secret(token=None, pending_user=None)
    return list_route({})


@post("/aliases/new")
def new(body):
    code, j = _authed("POST", "email/addresses")
    if code not in (200, 201) or not j.get("address"):
        raise ValueError(f"DuckDuckGo would not make an alias ({code})")
    item = {"address": f"{j['address'].lower()}@duck.com", "label": _text(body.get("label"), 80),
            "note": _text(body.get("note"), 300), "active": True, "created": int(time.time()), "checked": int(time.time())}
    with LOCK:
        items = _items()
        items.append(item)
        _save(items)
    return item


@post("/aliases/import")
def import_(body):
    """any pasted text: every @duck.com in it joins the list (a label after a comma or tab on the same line)"""
    s = _secret()
    own = f"{s['user']}@duck.com" if s.get("user") else None
    added = 0
    with LOCK:
        items = _items()
        have = {i["address"] for i in items}
        for line in str(body.get("text") or "")[:200_000].splitlines():
            for m in ALIAS_RE.finditer(line):
                a = m.group(0).lower()
                if a in have or a == own:
                    continue
                rest = _text(re.sub(r"^[\s,;:\t|-]+", "", line[m.end():]), 80)
                items.append({"address": a, "label": rest, "note": "", "active": None, "created": int(time.time()), "checked": 0})
                have.add(a)
                added += 1
        _save(items)
    return {"added": added, **list_route({})}


@post("/aliases/edit")
def edit(body):
    with LOCK:
        items = _items()
        i = _find(items, body.get("address"))
        if not i:
            raise ValueError("not in the list")
        if "label" in body:
            i["label"] = _text(body["label"], 80)
        if "note" in body:
            i["note"] = _text(body["note"], 300)
        _save(items)
    return i


def _set_active(address, active):
    code, j = _authed("PUT", "email/addresses", {"address": address.removesuffix("@duck.com"), "active": "true" if active else "false"})
    if code != 200:
        raise ValueError(f"DuckDuckGo would not change {address} ({code})")
    return bool(j.get("active", active))


@post("/aliases/active")
def active(body):
    a = _addr(body.get("address"))
    on = _set_active(a, bool(body.get("active")))
    with LOCK:
        items = _items()
        i = _find(items, a)
        if i:
            i["active"], i["checked"] = on, int(time.time())
            _save(items)
    return i or {"address": a, "active": on}


@post("/aliases/delete")
def delete(body):
    """switch it off at DDG (when signed in), then drop it from the list"""
    a = _addr(body.get("address"))
    if body.get("deactivate", True) and _secret().get("token"):
        _set_active(a, False)
    with LOCK:
        _save([i for i in _items() if i["address"] != a])
    return {"ok": True}


@post("/aliases/refresh")
def refresh(body):
    """ask DDG whether each alias is still on: someone may have switched one off from a mail's banner"""
    _token()
    with LOCK:
        items = _items()
    errors = 0
    for i in items:
        code, j = _authed("GET", "email/addresses", {"address": i["address"].removesuffix("@duck.com")})
        if code == 200 and "active" in j:
            i["active"], i["checked"] = bool(j["active"]), int(time.time())
        else:
            errors += 1
    with LOCK:
        cur = {i["address"]: i for i in _items()}
        for i in items:
            if i["address"] in cur:
                cur[i["address"]].update(active=i["active"], checked=i["checked"])
        _save(list(cur.values()))
    return {"errors": errors, **list_route({})}
