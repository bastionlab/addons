"""Mail: IMAP read + cache, local-model triage and reply drafts, SMTP send on confirmation only.

Accounts are rows in the add-on's `accounts_json` setting; the password of account <id> is the secret `pw_<id>`;
both files are managed by the Accounts screen (routes below), not by the Settings page.
Cache: /var/lib/dash-mail/mail.db (headers, short snippet, category, summary; bodies are fetched on demand).
Triage: user-editable categories; a rule (sender / domain / subject) decides first, else one local-model call with the
category descriptions and the owner's recent manual corrections as examples; an optional second model re-checks unsure ones.
"""
import email, email.policy, email.utils, html, imaplib, json, os, re, smtplib, sqlite3, ssl, threading, time, urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from dash_sdk import CFG, get, ip, post

DIR = Path(os.environ.get("MAIL_DIR") or "/var/lib/dash-mail")
DB = DIR / "mail.db"
MODEL = "qwen3.5:9b"
# the five seeded categories (id, name, colour, description); the old hardcoded tags, now rows the owner can edit
SEED = (("important", "Important", "accent", "Needs a personal reply or action soon, has a deadline, or comes from a real person, bank, authority or employer."),
        ("later", "Later", "muted", "Worth reading but not urgent: updates, receipts, notifications, confirmations."),
        ("newsletter", "Newsletter", "claude", "Mass mailings, newsletters, promotions and marketing."),
        ("spam", "Spam", "bad", "Unwanted, suspicious or phishing mail, scams and junk."),
        ("other", "Other", "faint", "Anything that fits no other category."))
FALLBACK = "other"
COLORS = ("accent", "ok", "warn", "bad", "claude", "muted", "faint", "text")  # token names in main.css
RULE_KINDS = ("from", "domain", "subject")
UNSURE = 0.6
ID_RE = re.compile(r"^[a-z0-9_-]{1,24}$")
DAYS, NEWEST, TRIAGE_BATCH = 60, 200, 12


# ---- accounts ------------------------------------------------------------------------------------------------

# the add-on keeps its own two files (paths overridable for tests): the account rows as the string setting
# `accounts_json` (same key the old Settings field used, so saved data keeps working) and the passwords as secrets pw_<id>
SETTINGS_FILE = Path(os.environ.get("MAIL_SETTINGS_FILE") or "/etc/dash/settings/mail.json")
SECRETS_FILE = Path(os.environ.get("MAIL_SECRETS_FILE") or "/etc/dash/secrets/mail.json")
LOCK = threading.Lock()
HOST_RE = re.compile(r"^(?=.{1,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*$")
MAIL_RE = re.compile(r"^[^@\s,;<>\"']{1,64}@[^@\s,;<>\"']{1,255}$")
PROVIDERS = ("gmail", "workspace", "microsoft", "tuberlin", "gmx", "webde", "other")


def _read_json(p):
    try:
        d = json.loads(p.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_json(p, data, dir_mode):
    """atomic (tmp + rename), file 0600 from the first byte"""
    p.parent.mkdir(mode=dir_mode, parents=True, exist_ok=True)
    if dir_mode == 0o700:
        os.chmod(p.parent, 0o700)
    tmp = p.parent / f".{p.name}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps(data, indent=2))
    os.chmod(tmp, 0o600)
    tmp.replace(p)


def _accounts_raw():
    raw = _read_json(SETTINGS_FILE).get("accounts_json") or "[]"
    try:
        rows = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        raise ValueError("accounts_json is not valid JSON")
    return [r for r in rows if isinstance(r, dict) and ID_RE.match(str(r.get("id", "")))] if isinstance(rows, list) else []


def _save_accounts(rows):
    d = _read_json(SETTINGS_FILE)
    d["accounts_json"] = json.dumps(rows, separators=(",", ":"))
    _write_json(SETTINGS_FILE, d, 0o755)


def _secret(aid):
    return (_read_json(SECRETS_FILE).get("pw_" + aid) or {}).get("value")


def _set_secret(aid, value):
    d = _read_json(SECRETS_FILE)
    if value:
        d["pw_" + aid] = {"value": value, "updated": int(time.time())}
    else:
        d.pop("pw_" + aid, None)
    _write_json(SECRETS_FILE, d, 0o700)


def _sync_stats(aid):
    db = _db()
    r = db.execute("SELECT COUNT(*), COALESCE(SUM(seen=0),0) FROM messages WHERE account=? AND folder='INBOX'", (aid,)).fetchone()
    s = db.execute("SELECT at, error FROM sync WHERE account=?", (aid,)).fetchone()
    return {"messages": r[0], "unread": int(r[1]), "last_sync": s["at"] if s else None, "last_error": (s["error"] or "") if s else ""}


def accounts():
    """public view: never the password (nor its length), only whether one is set"""
    return [{"id": a["id"], "label": a.get("label") or a["id"], "from": a.get("from", ""), "username": a.get("username", ""),
             "provider": a.get("provider", "other"), "imap_host": a.get("imap_host", ""), "imap_port": a.get("imap_port", 993),
             "smtp_host": a.get("smtp_host", ""), "smtp_port": a.get("smtp_port", 587),
             "configured": bool(_secret(a["id"])), **_sync_stats(a["id"])}
            for a in _accounts_raw()]


def _acct(aid):
    for a in _accounts_raw():
        if a["id"] == aid:
            return a
    raise ValueError("unknown account")


def _pw(a):
    pw = _secret(a["id"])
    if not pw:
        raise ValueError(f"account {a['id']} has no password yet")
    return pw


def _port(v, what):
    try:
        n = int(str(v).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{what} port must be a number")
    if not 1 <= n <= 65535:
        raise ValueError(f"{what} port must be 1-65535")
    return n


def _host(v, what):
    h = str(v or "").strip().lower()
    if not HOST_RE.match(h):
        raise ValueError(f"{what} host must be a plain hostname (no scheme, slash or spaces)")
    return h


def validate(b):
    """the posted account fields -> a clean row (without id/password); raises ValueError with a readable reason"""
    label = re.sub(r"\s+", " ", str(b.get("label") or "")).strip()
    if not 1 <= len(label) <= 40 or not label.isprintable():
        raise ValueError("name must be 1-40 characters")
    addr = str(b.get("email") or b.get("from") or "").strip()
    if not MAIL_RE.match(addr) or ".." in addr or not addr.rsplit("@", 1)[1].count("."):
        raise ValueError("email address looks wrong")
    user = str(b.get("username") or "").strip() or addr
    if len(user) > 200 or not user.isprintable():
        raise ValueError("username is not valid")
    prov = str(b.get("provider") or "other")
    if prov in ("gmail", "workspace") and "@" not in user:
        user = addr  # Google logs in with the full address, never the part before the @
    return {"label": label, "from": addr, "username": user, "provider": prov if prov in PROVIDERS else "other",
            "imap_host": _host(b.get("imap_host"), "IMAP"), "imap_port": _port(b.get("imap_port"), "IMAP"),
            "smtp_host": _host(b.get("smtp_host"), "SMTP"), "smtp_port": _port(b.get("smtp_port"), "SMTP")}


def _password(b):
    pw = b.get("password")
    if pw in (None, ""):
        return ""
    pw = str(pw).strip()
    # Google shows app passwords as "abcd efgh ijkl mnop"; the spaces are display only
    if str(b.get("provider", "")).startswith(("gmail", "workspace")):
        pw = pw.replace(" ", "")
    if len(pw) > 500 or "\n" in pw or "\r" in pw:
        raise ValueError("password is not valid")
    return pw


def make_id(label, taken):
    base = re.sub(r"[^a-z0-9]+", "-", str(label).lower()).strip("-")[:20].strip("-") or "mail"
    cand, n = base, 1
    while cand in taken:
        n += 1
        cand = f"{base[:24 - len(str(n)) - 1]}-{n}"
    return cand


def save_account(b):
    row, pw = validate(b), _password(b)
    with LOCK:
        rows = _accounts_raw()
        aid = str(b.get("id") or "")
        if aid:
            if aid not in {r["id"] for r in rows}:
                raise ValueError("unknown account")
            rows = [{**r, **row, "id": aid} if r["id"] == aid else r for r in rows]
        else:
            if not pw:
                raise ValueError("password is required for a new account")
            aid = make_id(row["label"], {r["id"] for r in rows})
            rows.append({"id": aid, **row})
        if pw:
            _set_secret(aid, pw)
        _save_accounts(rows)
    return {"ok": True, "id": aid}


def delete_account(b):
    aid = str(b.get("id") or "")
    with LOCK:
        rows = _accounts_raw()
        if aid not in {r["id"] for r in rows}:
            raise ValueError("unknown account")
        _save_accounts([r for r in rows if r["id"] != aid])
        _set_secret(aid, "")
    if b.get("delete_cache", True) is not False:
        db = _db()
        for t in ("messages", "state", "sync", "examples"):
            db.execute(f"DELETE FROM {t} WHERE account=?", (aid,))
        db.commit()
    return {"ok": True}


def test_connection(b):
    """IMAP login + SMTP EHLO/STARTTLS/login, nothing sent. Fields posted, or a saved id; a blank password uses the saved one."""
    saved = _acct(str(b["id"])) if b.get("id") else {}
    row = validate({**saved, "email": saved.get("from"), **{k: v for k, v in b.items() if v not in (None, "")}}) if saved else validate(b)
    pw = _password(b) or (_secret(saved["id"]) if saved else "")
    if not pw:
        raise ValueError("no password set")
    out = {"imap": "", "smtp": ""}
    ctx = ssl.create_default_context()

    def scrub(e):
        return f"{type(e).__name__}: {e}".replace(pw, "***")[:300]
    try:
        c = imaplib.IMAP4_SSL(row["imap_host"], row["imap_port"], timeout=10, ssl_context=ctx)
        try:
            c.login(row["username"], pw)
        finally:
            try:
                c.logout()
            except Exception:
                pass
    except Exception as e:
        out["imap"] = scrub(e)
    try:
        if row["smtp_port"] == 465:
            s = smtplib.SMTP_SSL(row["smtp_host"], row["smtp_port"], timeout=10, context=ctx)
        else:
            s = smtplib.SMTP(row["smtp_host"], row["smtp_port"], timeout=10)
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
        try:
            s.login(row["username"], pw)
        finally:
            try:
                s.quit()
            except Exception:
                pass
    except Exception as e:
        out["smtp"] = scrub(e)
    err = "; ".join(f"{k.upper()}: {v}" for k, v in out.items() if v)
    return {"ok": not err, "imap_ok": not out["imap"], "smtp_ok": not out["smtp"], "error": err}


# ---- db ------------------------------------------------------------------------------------------------------

_MIGRATED = set()


def _db():
    DIR.mkdir(mode=0o700, exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS messages(account TEXT, uid INTEGER, folder TEXT, "from" TEXT, "to" TEXT, subject TEXT,
      date INTEGER, snippet TEXT, seen INTEGER, tags TEXT, summary TEXT, triaged_at INTEGER, msgid TEXT,
      PRIMARY KEY(account, folder, uid));
    CREATE TABLE IF NOT EXISTS state(account TEXT, folder TEXT, uidvalidity INTEGER, PRIMARY KEY(account, folder));
    CREATE TABLE IF NOT EXISTS sync(account TEXT PRIMARY KEY, at INTEGER, error TEXT);
    CREATE TABLE IF NOT EXISTS sent(id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT, at INTEGER, "to" TEXT,
      subject TEXT, in_reply_to TEXT, body TEXT);
    CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY, name TEXT, color TEXT, description TEXT, builtin INTEGER DEFAULT 0,
      enabled INTEGER DEFAULT 1, pos INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS rules(id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, kind TEXT, value TEXT, pos INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS examples(account TEXT, uid INTEGER, category TEXT, from_addr TEXT, subject TEXT, at INTEGER);
    CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
    """)
    if str(DB) not in _MIGRATED:
        _migrate(c)
        _MIGRATED.add(str(DB))
    return c


def _migrate(c):
    """idempotent: new columns, seeded categories, old tag strings -> category (once)"""
    have = {r[1] for r in c.execute("PRAGMA table_info(messages)")}
    for col, typ in (("category", "TEXT"), ("confidence", "REAL"), ("cat_source", "TEXT")):
        if col not in have:
            c.execute(f"ALTER TABLE messages ADD COLUMN {col} {typ}")
    c.execute("CREATE INDEX IF NOT EXISTS messages_cat ON messages(category)")
    done = {r[0] for r in c.execute("SELECT k FROM meta")}
    if "seeded" not in done:
        for i, (cid, name, color, desc) in enumerate(SEED):
            c.execute("INSERT OR IGNORE INTO categories(id,name,color,description,builtin,enabled,pos) VALUES(?,?,?,?,1,1,?)", (cid, name, color, desc, i))
        c.execute("INSERT INTO meta VALUES('seeded','1')")
    if "tags_backfilled" not in done:
        c.execute("UPDATE messages SET category=tags, cat_source='model' WHERE category IS NULL AND tags IN (SELECT id FROM categories)")
        c.execute("INSERT INTO meta VALUES('tags_backfilled','1')")
    c.commit()


# ---- parsing -------------------------------------------------------------------------------------------------

def _dec(v):
    return str(email.policy.default.header_factory("x", v)) if v else ""


def strip_html(s):
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", s)).strip()


def text_of(msg, cap=8000):
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    try:
        t = part.get_content()
    except Exception:
        t = part.get_payload(decode=True).decode("utf-8", "replace") if part.get_payload() else ""
    if part.get_content_type() == "text/html":
        t = strip_html(t)
    return t.strip()[:cap]


def parse(raw: bytes):
    """one RFC822 message (headers + maybe body) -> the cache columns"""
    m = email.message_from_bytes(raw, policy=email.policy.default)
    try:
        d = email.utils.parsedate_to_datetime(str(m["Date"]))
        ts = int(d.timestamp())
    except Exception:
        ts = int(time.time())
    return {"from": _dec(m["From"]), "to": _dec(m["To"]), "subject": _dec(m["Subject"]) or "(no subject)", "date": ts,
            "msgid": str(m["Message-ID"] or "").strip(), "snippet": re.sub(r"\s+", " ", text_of(m, 400))[:240]}


# ---- imap ----------------------------------------------------------------------------------------------------

def _imap(a):
    c = imaplib.IMAP4_SSL(a["imap_host"], int(a.get("imap_port") or 993), timeout=30)
    c.login(a["username"], _pw(a))
    return c


def sync(aid):
    a = _acct(aid)
    db = _db()
    c = _imap(a)
    try:
        typ, _ = c.select("INBOX", readonly=True)
        if typ != "OK":
            raise ValueError("cannot open INBOX")
        v = c.response("UIDVALIDITY")[1]
        uv = int(v[0]) if v and v[0] else 0
        row = db.execute("SELECT uidvalidity FROM state WHERE account=? AND folder='INBOX'", (aid,)).fetchone()
        if row and row[0] != uv:
            db.execute("DELETE FROM messages WHERE account=? AND folder='INBOX'", (aid,))
        db.execute("INSERT OR REPLACE INTO state VALUES(?,?,?)", (aid, "INBOX", uv))
        top = db.execute("SELECT MAX(uid) FROM messages WHERE account=? AND folder='INBOX'", (aid,)).fetchone()[0] or 0
        since = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime("%d-%b-%Y")
        _, data = c.uid("SEARCH", None, "SINCE", since)
        uids = sorted(int(x) for x in data[0].split())
        new = [u for u in uids if u > top][-NEWEST:]
        for i in range(0, len(new), 25):
            chunk = new[i:i + 25]
            _, res = c.uid("FETCH", ",".join(map(str, chunk)), "(FLAGS BODY.PEEK[HEADER] BODY.PEEK[TEXT]<0.1500>)")
            _store(db, aid, res)
        # flags of what we already hold (read elsewhere)
        _flags(c, db, aid, uids)
        db.commit()
        _note_sync(aid, "")
        tri = triage_pending(aid)
        return {"account": aid, "new": len(new), **tri}
    finally:
        try:
            c.logout()
        except Exception:
            pass


def _note_sync(aid, err):
    db = _db()
    if err:  # keep the time of the last good sync
        db.execute("INSERT INTO sync(account,at,error) VALUES(?,NULL,?) ON CONFLICT(account) DO UPDATE SET error=excluded.error", (aid, err))
    else:
        db.execute("INSERT OR REPLACE INTO sync VALUES(?,?,'')", (aid, int(time.time())))
    db.commit()


def _collect(res):
    """FETCH answer -> {uid: {flags, head, text}}. Servers split one message over several tuples and may put UID/FLAGS
    in any of them (Gmail: after the literals), so entries are grouped by the '<seq> (' that opens each message."""
    ents, cur = [], None
    for item in res:
        meta = (item[0] if isinstance(item, tuple) else item)
        if not isinstance(meta, bytes):
            continue
        s = meta.decode("ascii", "replace")
        if re.match(r"\s*\d+ \(", s) or cur is None:
            cur = {"uid": None, "flags": "", "head": b"", "text": b""}
            ents.append(cur)
        um = re.search(r"UID (\d+)", s)
        if um:
            cur["uid"] = int(um.group(1))
        fm = re.search(r"FLAGS \(([^)]*)\)", s)
        if fm:
            cur["flags"] = fm.group(1)
        if isinstance(item, tuple):
            if re.search(r"BODY\[HEADER", s, re.I):
                cur["head"] = item[1]
            else:
                cur["text"] = item[1]
    return {e["uid"]: e for e in ents if e["uid"] is not None}


def _store(db, aid, res):
    cur = _collect(res)
    for uid, e in cur.items():
        p = parse(e["head"] + b"\r\n" + e["text"] if e["text"] else e["head"])
        if not p["snippet"] and e["text"]:
            p["snippet"] = re.sub(r"\s+", " ", e["text"].decode("utf-8", "replace"))[:240]
        db.execute("INSERT OR IGNORE INTO messages(account,uid,folder,\"from\",\"to\",subject,date,snippet,seen,msgid)"
                   " VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (aid, uid, "INBOX", p["from"], p["to"], p["subject"], p["date"], p["snippet"],
                    1 if "\\Seen" in e["flags"] else 0, p["msgid"]))


def _flags(c, db, aid, uids):
    have = {r[0] for r in db.execute("SELECT uid FROM messages WHERE account=? AND folder='INBOX' AND seen=0", (aid,))}
    have &= set(uids)
    if not have:
        return
    _, res = c.uid("FETCH", ",".join(map(str, sorted(have))), "(FLAGS)")
    for item in res:
        s = (item if isinstance(item, bytes) else item[0]).decode("ascii", "replace")
        um = re.search(r"UID (\d+)", s)
        if um and "\\Seen" in s:
            db.execute("UPDATE messages SET seen=1 WHERE account=? AND folder='INBOX' AND uid=?", (aid, int(um.group(1))))


def body(aid, uid):
    a = _acct(aid)
    c = _imap(a)
    try:
        c.select("INBOX", readonly=True)
        _, res = c.uid("FETCH", str(int(uid)), "(BODY.PEEK[])")
        raw = next((i[1] for i in res if isinstance(i, tuple)), None)
        if raw is None:
            raise ValueError("message not found")
        m = email.message_from_bytes(raw, policy=email.policy.default)
        return {"text": text_of(m), "message_id": str(m["Message-ID"] or ""), "references": str(m["References"] or ""),
                "reply_to": _dec(m["Reply-To"] or m["From"])}
    finally:
        try:
            c.logout()
        except Exception:
            pass


# ---- local model ---------------------------------------------------------------------------------------------

def _ollama_url():
    return (CFG.get("ollama_proxy") or f"http://{ip('ai')}:11434").rstrip("/")


def _llm(system, user, timeout=120, model=None):
    req = urllib.request.Request(_ollama_url() + "/api/chat", method="POST", headers={"Content-Type": "application/json", "X-Job": "mail"},
                                 data=json.dumps({"model": model or MODEL, "stream": False, "think": False, "format": "json",
                                                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(json.loads(r.read())["message"]["content"])


# ---- categories + rules --------------------------------------------------------------------------------------

def _addr(frm):
    return email.utils.parseaddr(str(frm or ""))[1].strip().lower()


def _domain(frm):
    a = _addr(frm)
    return a.rsplit("@", 1)[1] if "@" in a else ""


def _cats(db, enabled_only=False):
    return [dict(r) for r in db.execute("SELECT * FROM categories" + (" WHERE enabled=1" if enabled_only else "") + " ORDER BY pos, id")]


def rule_hit(rule, frm, subject):
    v = rule["value"]
    if rule["kind"] == "from":
        return v in _addr(frm)
    if rule["kind"] == "domain":
        d = _domain(frm)
        return d == v or d.endswith("." + v)
    return v in str(subject or "").lower()


def match_rule(db, frm, subject):
    """first rule by pos (then id) whose category is enabled -> category id, else None; needs no model"""
    for r in db.execute("SELECT r.* FROM rules r JOIN categories c ON c.id=r.category WHERE c.enabled=1 ORDER BY r.pos, r.id"):
        if rule_hit(r, frm, subject):
            return r["category"]
    return None


def _examples(db, frm, enabled_ids, n=8):
    """recent manual corrections, those from the same sender domain first"""
    dom = _domain(frm)
    rows = [r for r in db.execute("SELECT * FROM examples ORDER BY at DESC, rowid DESC LIMIT 200") if r["category"] in enabled_ids]
    same = [r for r in rows if dom and _domain(r["from_addr"]) == dom]
    return (same + [r for r in rows if r not in same])[:n]


def build_prompt(db, r):
    """-> {"system", "user"}; the same prompt goes to the main model and to the judge"""
    cats = _cats(db, True)
    ids = {c["id"] for c in cats}
    system = ("Sort one email into exactly one of the owner's categories. Reply JSON "
              '{"category": <one id from the list>, "confidence": number 0..1, "summary": one line, max 15 words, in the mail\'s own language}. '
              "Use only the mail's text; never invent facts. Plain text, no emoji. If you are unsure, lower the confidence.")
    lines = ["Categories:"] + [f"- {c['id']} ({c['name']}): {c['description']}" for c in cats]
    ex = _examples(db, r["from"], ids)
    if ex:
        lines += ["", "Earlier corrections by the owner (sender | subject -> category):"]
        lines += [f"- {e['from_addr']} | {str(e['subject'])[:80]} -> {e['category']}" for e in ex]
    lines += ["", f"From: {r['from']}", f"Subject: {r['subject']}", "", str(r["snippet"] or "")]
    return {"system": system, "user": "\n".join(lines)}


def clean_result(j, ids):
    """model JSON -> (category id, confidence 0..1, one-line summary); an unknown id falls back to other with confidence 0"""
    j = j if isinstance(j, dict) else {}
    cat = str(j.get("category", "")).strip().lower()
    try:
        conf = min(1.0, max(0.0, float(j.get("confidence", 0))))
    except (TypeError, ValueError):
        conf = 0.0
    if cat not in ids:
        cat, conf = FALLBACK, 0.0
    return cat, conf, re.sub(r"\s+", " ", str(j.get("summary", ""))).strip()[:160]


def _setting(key, default=""):
    v = _read_json(SETTINGS_FILE).get(key)
    return default if v in (None, "") else v


def judge(prompt):
    """second opinion from the add-on setting `judge_model`; replace this function to use an external service"""
    return _llm(prompt["system"], prompt["user"], 120, model=str(_setting("judge_model")))


def classify(db, r):
    """-> (category, confidence, summary, source)"""
    hit = match_rule(db, r["from"], r["subject"])
    if hit:
        return hit, 1.0, "", "rule"
    if not str(r["snippet"] or "").strip() and str(r["subject"] or "").strip() in ("", "(no subject)"):
        return FALLBACK, 0.0, "", "model"
    ids = {c["id"] for c in _cats(db, True)}
    prompt = build_prompt(db, r)
    cat, conf, summ = clean_result(_llm(prompt["system"], prompt["user"], 90), ids)
    src = "model"
    try:
        below = float(_setting("judge_below", UNSURE))
    except (TypeError, ValueError):
        below = UNSURE
    if _setting("judge_model") and conf < below:
        try:
            c2, f2, s2 = clean_result(judge(prompt), ids)
            cat, conf, summ, src = c2, f2, s2 or summ, "judge"
        except Exception:
            pass  # the judge is optional, keep the first answer
    return cat, conf, summ, src


TRIAGE_LOCK = threading.Lock()


def pending(aid=""):
    db = _db()
    return db.execute("SELECT COUNT(*) FROM messages WHERE triaged_at IS NULL" + (" AND account=?" if aid else ""), (aid,) if aid else ()).fetchone()[0]


def triage_pending(aid="", limit=TRIAGE_BATCH):
    """sort up to `limit` untriaged messages (newest first); the UI calls again while `pending` > 0"""
    with TRIAGE_LOCK:
        db = _db()
        rows = db.execute("SELECT account,uid,\"from\",subject,snippet FROM messages WHERE triaged_at IS NULL"
                          + (" AND account=?" if aid else "") + " ORDER BY date DESC LIMIT ?", ((aid,) if aid else ()) + (limit,)).fetchall()
        done, note = 0, ""
        for r in rows:
            try:
                cat, conf, summ, src = classify(db, r)
            except Exception as e:
                note = f"model unavailable, left unsorted ({type(e).__name__})"
                break
            db.execute("UPDATE messages SET category=?, confidence=?, cat_source=?, tags=?, summary=?, triaged_at=? WHERE account=? AND folder='INBOX' AND uid=?",
                       (cat, conf, src, cat, summ, int(time.time()), r["account"], r["uid"]))
            db.commit()
            done += 1
        out = {"triaged": done, "pending": pending(aid)}
        if note:
            out["note"] = note
        return out


def _slug(name, taken):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:24].strip("-") or "cat"
    cand, n = base, 1
    while cand in taken:
        n += 1
        cand = f"{base[:24 - len(str(n)) - 1]}-{n}"
    return cand


def _clean_cat(b, others):
    """posted fields -> clean (name, color, description); `others` = the other categories (names must differ)"""
    name = re.sub(r"\s+", " ", str(b.get("name") or "")).strip()
    if not 1 <= len(name) <= 30 or not name.isprintable():
        raise ValueError("name must be 1-30 characters")
    if name.lower() in {c["name"].lower() for c in others}:
        raise ValueError("a category with this name exists")
    color = str(b.get("color") or "muted")
    if color not in COLORS:
        raise ValueError("unknown colour")
    desc = re.sub(r"\s+", " ", str(b.get("description") or "")).strip()
    if len(desc) > 200:
        raise ValueError("description is limited to 200 characters")
    return name, color, desc


def save_category(b):
    db = _db()
    cid = str(b.get("id") or "")
    allc = _cats(db)
    if cid:
        cur = next((c for c in allc if c["id"] == cid), None)
        if not cur:
            raise ValueError("unknown category")
        name, color, desc = _clean_cat({**cur, **b}, [c for c in allc if c["id"] != cid])
        enabled = cur["enabled"] if "enabled" not in b else (1 if b["enabled"] else 0)
        if cid == FALLBACK:
            enabled = 1
        pos = int(b["pos"]) if "pos" in b else cur["pos"]
        db.execute("UPDATE categories SET name=?,color=?,description=?,enabled=?,pos=? WHERE id=?", (name, color, desc, enabled, pos, cid))
    else:
        name, color, desc = _clean_cat(b, allc)
        cid = _slug(name, {c["id"] for c in allc})
        if not ID_RE.match(cid):
            raise ValueError("cannot make an id from this name")
        pos = int(b["pos"]) if "pos" in b else max([c["pos"] for c in allc] + [-1]) + 1
        db.execute("INSERT INTO categories(id,name,color,description,builtin,enabled,pos) VALUES(?,?,?,?,0,?,?)",
                   (cid, name, color, desc, 0 if b.get("enabled") is False else 1, pos))
    db.commit()
    return {"ok": True, "id": cid}


def delete_category(b):
    db = _db()
    cid = str(b.get("id") or "")
    cur = db.execute("SELECT builtin FROM categories WHERE id=?", (cid,)).fetchone()
    if not cur:
        raise ValueError("unknown category")
    if cur[0] or cid == FALLBACK:
        raise ValueError("built-in categories can only be turned off" if cid != FALLBACK else "Other is the fallback and cannot be removed")
    n = db.execute("UPDATE messages SET category=?, tags=? WHERE category=?", (FALLBACK, FALLBACK, cid)).rowcount
    for t in ("rules", "examples"):
        db.execute(f"DELETE FROM {t} WHERE category=?", (cid,))
    db.execute("DELETE FROM categories WHERE id=?", (cid,))
    db.commit()
    return {"ok": True, "moved": n}


def _rule_value(kind, value):
    if kind not in RULE_KINDS:
        raise ValueError("rule kind must be from, domain or subject")
    v = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    if kind == "domain":
        v = v.lstrip("@")
        if not HOST_RE.match(v):
            raise ValueError("domain looks wrong")
    if not 2 <= len(v) <= 80:
        raise ValueError("rule value must be 2-80 characters")
    return v


def _apply_rule(db, rule):
    n = 0
    for r in db.execute("SELECT account,uid,\"from\",subject,seen FROM messages WHERE folder='INBOX' AND COALESCE(cat_source,'')!='manual'").fetchall():
        if rule_hit(rule, r["from"], r["subject"]):
            db.execute("UPDATE messages SET category=?, tags=?, confidence=1, cat_source='rule', triaged_at=COALESCE(triaged_at,?) "
                       "WHERE account=? AND folder='INBOX' AND uid=?", (rule["category"], rule["category"], int(time.time()), r["account"], r["uid"]))
            n += 1
    return n


def _add_rule(db, cid, kind, value):
    if not db.execute("SELECT 1 FROM categories WHERE id=?", (cid,)).fetchone():
        raise ValueError("unknown category")
    v = _rule_value(kind, value)
    ex = db.execute("SELECT id FROM rules WHERE kind=? AND value=? AND category=?", (kind, v, cid)).fetchone()
    if ex:
        return {"id": ex[0], "kind": kind, "value": v, "category": cid}
    pos = (db.execute("SELECT MAX(pos) FROM rules").fetchone()[0] or 0) + 1
    rid = db.execute("INSERT INTO rules(category,kind,value,pos) VALUES(?,?,?,?)", (cid, kind, v, pos)).lastrowid
    return {"id": rid, "kind": kind, "value": v, "category": cid}


def add_rule(b):
    db = _db()
    rule = _add_rule(db, str(b.get("category") or ""), str(b.get("kind") or ""), b.get("value"))
    n = _apply_rule(db, rule) if b.get("apply") else 0
    db.commit()
    return {"ok": True, "rule": rule, "applied": n}


def delete_rule(b):
    db = _db()
    n = db.execute("DELETE FROM rules WHERE id=?", (int(b.get("id") or 0),)).rowcount
    db.commit()
    if not n:
        raise ValueError("unknown rule")
    return {"ok": True}


def set_message_category(b):
    """the owner's hand: category + an example for the next prompts; optional also_rule {kind, value}"""
    db = _db()
    aid, uid, cid = str(b.get("account") or ""), int(b.get("uid") or 0), str(b.get("category") or "")
    if not db.execute("SELECT 1 FROM categories WHERE id=?", (cid,)).fetchone():
        raise ValueError("unknown category")
    r = db.execute("SELECT \"from\",subject FROM messages WHERE account=? AND folder='INBOX' AND uid=?", (aid, uid)).fetchone()
    if not r:
        raise ValueError("message not found")
    rule = None
    ar = b.get("also_rule")
    if isinstance(ar, dict):
        rule = _add_rule(db, cid, str(ar.get("kind") or ""), ar.get("value"))
    now = int(time.time())
    db.execute("UPDATE messages SET category=?, tags=?, confidence=1, cat_source='manual', triaged_at=COALESCE(triaged_at,?) "
               "WHERE account=? AND folder='INBOX' AND uid=?", (cid, cid, now, aid, uid))
    db.execute("DELETE FROM examples WHERE account=? AND uid=?", (aid, uid))
    db.execute("INSERT INTO examples(account,uid,category,from_addr,subject,at) VALUES(?,?,?,?,?,?)", (aid, uid, cid, _addr(r["from"]), r["subject"], now))
    db.commit()
    return {"ok": True, "category": cid, "rule": rule}


def resort(b):
    """forget the automatic category (all, or only confidence < 0.6) so the next triage run sorts it again; manual rows stay"""
    db = _db()
    where = "COALESCE(cat_source,'')!='manual'" + (" AND confidence < ?" if b.get("only_unsure") else "")
    args = [UNSURE] if b.get("only_unsure") else []
    if b.get("account"):
        where += " AND account=?"; args.append(str(b["account"]))
    n = db.execute(f"UPDATE messages SET category=NULL, tags=NULL, confidence=NULL, cat_source=NULL, triaged_at=NULL WHERE folder='INBOX' AND {where}", args).rowcount
    db.commit()
    return {"ok": True, "count": n, "pending": pending(str(b.get("account") or ""))}


def suggest_categories(b=None):
    """up to 80 recent mails -> 3-6 new category proposals, not saved"""
    db = _db()
    rows = db.execute("SELECT \"from\",subject FROM messages WHERE folder='INBOX' ORDER BY date DESC LIMIT 80").fetchall()
    if not rows:
        raise ValueError("no mail cached yet, sync first")
    cats = _cats(db)
    lines = [f"- {re.sub(r'<.*', '', str(r['from'])).strip()[:40]} ({_domain(r['from'])}): {str(r['subject'])[:80]}" for r in rows]
    j = _llm("You help an email owner organise their inbox. From the list of recent mails propose 3 to 6 NEW categories that would "
             "sort most of it. Do not repeat these existing ones: " + ", ".join(c["name"] for c in cats) + ". Reply JSON "
             '{"categories":[{"name": 1-3 words, "description": one plain sentence telling a model what belongs here, max 150 characters}]}. '
             "Use only what the list shows. Plain text, no emoji.", "\n".join(lines), 120)
    taken = {c["name"].lower() for c in cats} | {c["id"] for c in cats}
    out = []
    for p in (j.get("categories") or []) if isinstance(j, dict) else []:
        if not isinstance(p, dict):
            continue
        name = re.sub(r"\s+", " ", str(p.get("name") or "")).strip()
        if not 1 <= len(name) <= 30 or name.lower() in taken or _slug(name, set()) in taken:
            continue
        taken.add(name.lower())
        out.append({"name": name, "description": re.sub(r"\s+", " ", str(p.get("description") or "")).strip()[:200]})
    return {"suggestions": out[:6]}


def list_categories(aid=""):
    db = _db()
    w, a = (" AND account=?", (aid,)) if aid else ("", ())
    cnt = {r[0]: (r[1], r[2]) for r in db.execute("SELECT category, COUNT(*), COALESCE(SUM(seen=0),0) FROM messages WHERE folder='INBOX'" + w + " GROUP BY category", a)}
    rules = {}
    for r in db.execute("SELECT * FROM rules ORDER BY pos, id"):
        rules.setdefault(r["category"], []).append({"id": r["id"], "kind": r["kind"], "value": r["value"]})
    cats = [{**c, "builtin": bool(c["builtin"]), "enabled": bool(c["enabled"]), "count": cnt.get(c["id"], (0, 0))[0],
             "unread": int(cnt.get(c["id"], (0, 0))[1]), "rules": rules.get(c["id"], [])} for c in _cats(db)]
    return {"categories": cats, "colors": list(COLORS), "pending": pending(aid),
            "total": sum(v[0] for v in cnt.values()), "total_unread": int(sum(v[1] for v in cnt.values()))}


def drafts(aid, uid):
    db = _db()
    r = db.execute("SELECT \"from\",subject FROM messages WHERE account=? AND folder='INBOX' AND uid=?", (aid, int(uid))).fetchone()
    if not r:
        raise ValueError("message not found")
    txt = body(aid, uid)["text"]
    j = _llm('Write three short reply drafts for the email owner, in the same language as the mail: a short acceptance, a polite decline, '
             'a request for more information. Never invent facts (dates, prices, names): use placeholders like [date]. '
             'Reply JSON {"options":[{"label": "...", "text": "..."}]} with exactly 3 options. No greeting line with an invented name.',
             f"From: {r['from']}\nSubject: {r['subject']}\n\n{txt[:6000]}", 150)
    opts = [{"label": str(o.get("label", ""))[:40], "text": str(o.get("text", ""))[:3000]}
            for o in (j.get("options") or []) if isinstance(o, dict)][:3]
    return {"options": opts}


# ---- send ----------------------------------------------------------------------------------------------------

def send(aid, to, subject, text, in_reply_to="", references="", dry_run=False):
    a = _acct(aid)
    if not re.fullmatch(r"[^@\s,;<>]+@[^@\s,;<>]+", str(to).strip().split("<")[-1].rstrip(">") if "<" in str(to) else str(to).strip()):
        raise ValueError("one valid recipient address, please")
    if not str(text).strip():
        raise ValueError("empty message")
    m = EmailMessage()
    m["From"] = a.get("from") or a["username"]
    m["To"], m["Subject"] = str(to).strip(), re.sub(r"[\r\n]+", " ", str(subject))[:300]
    m["Date"] = email.utils.formatdate(localtime=True)
    m["Message-ID"] = email.utils.make_msgid()
    if in_reply_to:
        m["In-Reply-To"] = re.sub(r"[\r\n]+", " ", in_reply_to)
        m["References"] = re.sub(r"[\r\n]+", " ", (references + " " + in_reply_to).strip())
    m.set_content(text)
    if dry_run:
        return {"dry_run": True, "preview": str(m)[:2000]}
    port, ctx = int(a.get("smtp_port") or 587), ssl.create_default_context()
    pw = _pw(a)
    if port == 465:
        s = smtplib.SMTP_SSL(a["smtp_host"], port, timeout=30, context=ctx)
    else:
        s = smtplib.SMTP(a["smtp_host"], port, timeout=30)
        s.starttls(context=ctx)
    try:
        s.login(a["username"], pw)
        s.send_message(m)
    finally:
        s.quit()
    db = _db()
    db.execute("INSERT INTO sent(account,at,\"to\",subject,in_reply_to,body) VALUES(?,?,?,?,?,?)",
               (aid, int(time.time()), m["To"], m["Subject"], in_reply_to, text))
    db.commit()
    return {"sent": True}


# ---- routes --------------------------------------------------------------------------------------------------

def _q(q, k, d=""):
    v = q.get(k, d)
    return (v[0] if isinstance(v, list) else v) or d


@get("/mail/accounts")
def r_accounts(q):
    return {"accounts": accounts()}


@post("/mail/sync")
def r_sync(body_):
    ids = [body_["account"]] if body_.get("account") else [a["id"] for a in accounts() if a["configured"]]
    out = []
    for i in ids:
        try:
            out.append(sync(i))
        except Exception as e:  # a bad account must not stop the others; the message carries no password
            out.append({"account": i, "error": f"{type(e).__name__}: {e}"[:200]})
            try:
                _note_sync(i, out[-1]["error"])
            except Exception:
                pass
    return {"results": out}


@post("/mail/triage")
def r_triage(b):
    return triage_pending(str(b.get("account") or ""))


def _confirmed(b, what):
    if b.get("confirm") is not True:
        raise ValueError(f"{what} needs the owner's confirmation")


@get("/mail/categories")
def r_categories(q):
    return list_categories(_q(q, "account"))


@post("/mail/categories/save")
def r_cat_save(b):
    _confirmed(b, "saving a category")
    return save_category(b)


@post("/mail/categories/delete")
def r_cat_delete(b):
    _confirmed(b, "removing a category")
    return delete_category(b)


@post("/mail/categories/rule")
def r_cat_rule(b):
    _confirmed(b, "adding a rule")
    return add_rule(b)


@post("/mail/categories/rule-delete")
def r_cat_rule_delete(b):
    _confirmed(b, "removing a rule")
    return delete_rule(b)


@post("/mail/categories/suggest")
def r_cat_suggest(b):
    return suggest_categories(b)


@post("/mail/categories/resort")
def r_cat_resort(b):
    _confirmed(b, "re-sorting")
    return resort(b)


@post("/mail/message/category")
def r_msg_category(b):
    _confirmed(b, "changing a category")
    return set_message_category(b)


@post("/mail/account/save")
def r_account_save(b):
    return save_account(b)


@post("/mail/account/delete")
def r_account_delete(b):
    return delete_account(b)


@post("/mail/account/test")
def r_account_test(b):
    return test_connection(b)


@get("/mail/messages")
def r_messages(q):
    where, args = [], []
    if _q(q, "account"):
        where.append("account=?"); args.append(_q(q, "account"))
    if _q(q, "category"):
        where.append("category=?"); args.append(_q(q, "category"))
    if _q(q, "unread") == "1":
        where.append("seen=0")
    if _q(q, "q"):
        where.append("(subject LIKE ? OR \"from\" LIKE ? OR summary LIKE ?)"); args += [f"%{_q(q, 'q')[:80]}%"] * 3
    sql = ("SELECT account,uid,\"from\",subject,date,snippet,seen,tags,summary,category,confidence,cat_source AS source FROM messages"
           + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY seen ASC, date DESC LIMIT 200")
    return {"messages": [dict(r) for r in _db().execute(sql, args)]}


@get("/mail/message")
def r_message(q):
    aid, uid = _q(q, "account"), int(_q(q, "uid", "0"))
    r = _db().execute("SELECT account,uid,\"from\",\"to\",subject,date,seen,tags,summary,category,confidence,cat_source AS source FROM messages WHERE account=? AND folder='INBOX' AND uid=?", (aid, uid)).fetchone()
    if not r:
        raise ValueError("message not found")
    return {**dict(r), **body(aid, uid)}


@post("/mail/drafts")
def r_drafts(b):
    return drafts(str(b.get("account")), int(b.get("uid")))


@post("/mail/send")
def r_send(b):
    if b.get("confirm") is not True:
        raise ValueError("sending needs the owner's confirmation")
    return send(str(b.get("account")), b.get("to", ""), b.get("subject", ""), b.get("text", ""),
                str(b.get("in_reply_to") or ""), str(b.get("references") or ""), bool(b.get("dry_run")))
