"""no network: parser, html strip, triage cleanup, send dry run. Run: python3 -I addons/mail/tests/test_mail.py"""
import json, os, stat, sys, tempfile, types
from pathlib import Path
tmp = Path(tempfile.mkdtemp())  # settings, secrets and cache live here, never in the real /etc/dash
os.environ.update(MAIL_SETTINGS_FILE=str(tmp / "set/mail.json"), MAIL_SECRETS_FILE=str(tmp / "sec/mail.json"), MAIL_DIR=str(tmp / "db"))
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "agent"))
sdk = types.ModuleType("dash_sdk")  # the real one pulls the whole agent; the engine only needs these names
sdk.CFG = {}; sdk.ip = lambda n: ""
sdk.get = sdk.post = lambda *a, **k: (lambda f: f)
sys.modules["dash_sdk"] = sdk
sys.path.insert(0, str(root / "addons/mail/agent"))
import mail, imaplib, smtplib
assert str(mail.SETTINGS_FILE).startswith(str(tmp)) and str(mail.SECRETS_FILE).startswith(str(tmp))
raw = b"From: =?utf-8?q?J=C3=BCrgen?= <j@example.org>\r\nSubject: Termin\r\nDate: Mon, 26 Oct 2026 10:00:00 +0100\r\nMessage-ID: <a@x>\r\nContent-Type: text/html\r\n\r\n<p>Hallo <b>Welt</b></p><style>x{}</style>"
p = mail.parse(raw)
assert "Jürgen" in p["from"] and p["subject"] == "Termin" and p["snippet"] == "Hallo Welt", p
assert mail.clean_result({"category": "WAT", "confidence": .9, "summary": " a  b "}, {"later", "other"}) == ("other", 0.0, "a b")
assert mail.clean_result({"category": "Later", "confidence": 7}, {"later"}) == ("later", 1.0, "")
good = dict(label="Uni", email="me@example.org", password="s3cret-PW", provider="tuberlin",
            imap_host="imap.example.org", imap_port=993, smtp_host="smtp.example.org", smtp_port=587)
assert mail.save_account(good)["id"] == "uni"
r = mail.send("uni", "x@example.org", "Re: a", "hi", "<a@x>", dry_run=True)
assert r["dry_run"] and "In-Reply-To: <a@x>" in r["preview"]
try:
    mail.send("uni", "bad", "s", "hi", dry_run=True); raise SystemExit("bad address accepted")
except ValueError:
    pass

def bad(**kw):
    try:
        mail.validate({**good, **kw}); raise SystemExit(f"accepted {kw}")
    except ValueError:
        pass
for h in ("imap://x.org", "a b.org", "x.org/path", "", "-x.org", "x..org"):
    bad(imap_host=h)
bad(smtp_host="mail.example.org:587")
for pt in (0, 65536, "abc", "", -1):
    bad(imap_port=pt)
for e in ("nope", "a@b", "a b@c.org", "a@b..org", ""):
    bad(email=e)
bad(label=""); bad(label="x" * 41)
assert mail.validate({**good, "username": ""})["username"] == "me@example.org"

# ids: slug of the label, unique, always matches the id pattern
assert mail.make_id("My Uni!", set()) == "my-uni" and mail.make_id("!!!", set()) == "mail"
assert mail.save_account({**good, "label": "Uni"})["id"] == "uni-2"
assert mail.save_account({**good, "label": "Uni"})["id"] == "uni-3"
long_ids = {mail.make_id("x" * 60, {"x" * 20}), mail.make_id("x" * 60, {"x" * 20, "x" * 20 + "-2"})}
assert all(mail.ID_RE.match(i) for i in long_ids), long_ids
try:
    mail.save_account({**good, "password": ""}); raise SystemExit("new account without password")
except ValueError:
    pass

# update keeps the password when none is posted; the list never shows it
mail.save_account({**good, "id": "uni", "label": "Uni 1", "password": ""})
lst = mail.accounts()
assert lst[0]["label"] == "Uni 1" and lst[0]["configured"] and len(lst) == 3
assert "s3cret-PW" not in json.dumps(lst) and not any("pw" in k or "password" in k for a in lst for k in a)
for f_, mode in ((mail.SECRETS_FILE, 0o600), (mail.SETTINGS_FILE, 0o600), (mail.SECRETS_FILE.parent, 0o700)):
    assert stat.S_IMODE(f_.stat().st_mode) == mode, (f_, oct(f_.stat().st_mode))
assert not list(mail.SECRETS_FILE.parent.glob(".*tmp"))

# sync bookkeeping + delete with and without cache
db = mail._db()
db.execute("INSERT INTO messages(account,uid,folder,seen) VALUES('uni',1,'INBOX',0),('uni',2,'INBOX',1),('uni-2',1,'INBOX',0)")
db.commit()
mail._note_sync("uni", "boom")
st = mail.accounts()[0]
assert (st["messages"], st["unread"], st["last_error"]) == (2, 1, "boom")
mail._note_sync("uni", "")
assert mail.accounts()[0]["last_sync"] and mail.accounts()[0]["last_error"] == ""
mail.delete_account({"id": "uni", "delete_cache": False})
assert db.execute("SELECT COUNT(*) FROM messages WHERE account='uni'").fetchone()[0] == 2
assert "pw_uni" not in json.loads(mail.SECRETS_FILE.read_text()) and "pw_uni-2" in json.loads(mail.SECRETS_FILE.read_text())
mail.delete_account({"id": "uni-2"})
assert db.execute("SELECT COUNT(*) FROM messages WHERE account='uni-2'").fetchone()[0] == 0
mail.delete_account({"id": "uni-3"})
assert mail.accounts() == []

# connection test with mocked imaplib/smtplib: nothing leaves this process
calls = []
class FakeIMAP:
    def __init__(self, host, port, timeout=None, ssl_context=None): calls.append(("imap", host, port, timeout)); assert ssl_context
    def login(self, u, p):
        if p == "wrong": raise imaplib.IMAP4.error("AUTHENTICATIONFAILED wrong")
    def logout(self): pass
class FakeSMTP:
    def __init__(self, host, port, timeout=None, context=None): calls.append(("smtp", host, port, timeout))
    def ehlo(self): pass
    def starttls(self, context=None): assert context
    def login(self, u, p): pass
    def quit(self): pass
    def send_message(self, m): raise SystemExit("test must not send")
imaplib.IMAP4_SSL, smtplib.SMTP, smtplib.SMTP_SSL = FakeIMAP, FakeSMTP, FakeSMTP
r = mail.test_connection(good)
assert r["ok"] and calls == [("imap", "imap.example.org", 993, 10), ("smtp", "smtp.example.org", 587, 10)], calls
r = mail.test_connection({**good, "password": "wrong"})
assert not r["ok"] and r["smtp_ok"] and "wrong" not in r["error"].replace("AUTHENTICATIONFAILED", "") and "***" in r["error"], r
mail.save_account(good)
assert mail.test_connection({"id": "uni"})["ok"]  # saved id: stored password
try:
    mail.test_connection({**good, "password": ""}); raise SystemExit("test without any password")
except ValueError:
    pass

# Gmail-style FETCH answer: header and text come as separate tuples, UID/FLAGS only in a later piece
hdr = b"From: =?utf-8?q?J=C3=BCrgen?= <j@example.org>\r\nTo: me@example.org\r\nSubject: Hello there\r\nDate: Tue, 27 Oct 2026 10:00:00 +0000\r\nMessage-ID: <a@b>\r\n\r\n"
res = [(b"1 (UID 77 FLAGS (\\Seen) BODY[HEADER] {%d}" % len(hdr), hdr),
       (b" BODY[TEXT]<0> {12}", b"Hi, a body.\r\n"), b")",
       (b"2 (BODY[HEADER] {%d}" % len(hdr), hdr), (b" BODY[TEXT]<0> {5}", b"Body2"), b" UID 78 FLAGS ())"]
got = mail._collect(res)
assert set(got) == {77, 78}, got
assert got[77]["head"] == hdr and got[77]["text"].startswith(b"Hi") and "Seen" in got[77]["flags"], got
assert got[78]["head"] == hdr and got[78]["text"] == b"Body2" and "Seen" not in got[78]["flags"], got
pp = mail.parse(got[77]["head"] + b"\r\n" + got[77]["text"])
assert pp["subject"] == "Hello there" and "j@example.org" in pp["from"], pp

# ---- categories, rules, learning (fresh db file so the checks above stay untouched) ----
import sqlite3
mail.DIR = tmp / "db2"; mail.DB = mail.DIR / "mail.db"
mail.DIR.mkdir()
old = sqlite3.connect(mail.DB)  # a db as the old version left it: tags only, no category columns
old.executescript("""CREATE TABLE messages(account TEXT, uid INTEGER, folder TEXT, "from" TEXT, "to" TEXT, subject TEXT, date INTEGER,
  snippet TEXT, seen INTEGER, tags TEXT, summary TEXT, triaged_at INTEGER, msgid TEXT, PRIMARY KEY(account, folder, uid));
  INSERT INTO messages(account,uid,folder,"from",subject,date,snippet,seen,tags,triaged_at) VALUES
  ('a',1,'INBOX','Bob <bob@x.org>','hi',1,'s',0,'important',5),('a',2,'INBOX','n@news.org','deal',2,'s',1,'newsletter',5),
  ('a',3,'INBOX','z@z.org','odd',3,'s',1,'weird',5);""")
old.commit(); old.close()
db = mail._db()
cat = lambda uid: db.execute("SELECT category,cat_source FROM messages WHERE uid=?", (uid,)).fetchone()
assert tuple(cat(1)) == ("important", "model") and cat(2)[0] == "newsletter" and cat(3)[0] is None
assert [r[0] for r in db.execute("SELECT id FROM categories ORDER BY pos")] == ["important", "later", "newsletter", "spam", "other"]
mail._MIGRATED.clear(); mail._db()  # idempotent
assert db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 5
assert mail.list_categories()["categories"][0]["count"] == 1

def ins(uid, frm, subj, snip="body text"):
    db.execute("INSERT INTO messages(account,uid,folder,\"from\",subject,date,snippet,seen) VALUES('a',?,'INBOX',?,?,?,?,0)", (uid, frm, subj, 100 + uid, snip))
    db.commit()

prompts, answers = [], []
def fake_llm(system, user, timeout=120, model=None):
    prompts.append((system, user, model))
    return answers.pop(0)
mail._llm = fake_llm

# rules beat the model; first rule by pos wins; the model is not asked
mail.save_category({"name": "Shop", "color": "ok", "description": "orders"})
mail.add_rule({"category": "spam", "kind": "domain", "value": "Evil.com"})
mail.add_rule({"category": "shop", "kind": "from", "value": "evil"})
ins(10, "Eve <x@mail.evil.com>", "WIN"); ins(11, "shop@shop.de", "Your order 55")
mail.add_rule({"category": "shop", "kind": "subject", "value": "your order"})
assert mail.triage_pending("a")["triaged"] == 2 and prompts == []  # uid 10 and 11 by rule, no model call
assert tuple(cat(10)) == ("spam", "rule") and cat(11)[0] == "shop", (tuple(cat(10)), tuple(cat(11)))
for bad_ in ({"category": "shop", "kind": "from", "value": "x"}, {"category": "shop", "kind": "nope", "value": "xx"}, {"category": "zzz", "kind": "from", "value": "xx"}):
    try:
        mail.add_rule(bad_); raise SystemExit(f"accepted {bad_}")
    except ValueError:
        pass

# unknown id from the model -> other, confidence 0; summary kept
prompts.clear(); ins(12, "p@p.org", "Hello", "some text")
answers.append({"category": "madeup", "confidence": 0.99, "summary": "A line"})
mail.triage_pending("a")
r12 = db.execute("SELECT category,confidence,summary,cat_source FROM messages WHERE uid=12").fetchone()
assert tuple(r12) == ("other", 0.0, "A line", "model"), tuple(r12)
assert len(prompts) == 1 and "- important (Important)" in prompts[0][1] and "Subject: Hello" in prompts[0][1]
# no subject and no text: no model call
ins(13, "q@q.org", "(no subject)", ""); mail.triage_pending("a")
assert len(prompts) == 1 and tuple(db.execute("SELECT category,summary FROM messages WHERE uid=13").fetchone()) == ("other", "")

# judge: only below the threshold, answer kept with source judge; off when judge_model empty
mail.SETTINGS_FILE.write_text(json.dumps({"judge_model": "big:1b", "judge_below": 0.6}))
judged = []
real_judge = mail.judge
mail.judge = lambda pr: (judged.append(pr), {"category": "later", "confidence": 0.8, "summary": "J"})[1]
ins(14, "a@b.org", "sure one"); ins(15, "c@d.org", "unsure one")
answers[:] = [{"category": "later", "confidence": 0.3, "summary": "M"}, {"category": "later", "confidence": 0.9, "summary": "M"}]
mail.triage_pending("a")  # newest first: uid 15 (unsure) then 14
got = {u: tuple(db.execute("SELECT category,confidence,cat_source FROM messages WHERE uid=?", (u,)).fetchone()) for u in (14, 15)}
assert len(judged) == 1 and got[15][2] == "judge" and got[14][2] == "model", (got, len(judged))
mail.judge = real_judge
mail.SETTINGS_FILE.write_text(json.dumps({"judge_model": ""}))
mail.judge = lambda pr: judged.append(1) or SystemExit("judge off")
ins(16, "e@f.org", "unsure two"); answers[:] = [{"category": "later", "confidence": 0.1}]
mail.triage_pending("a"); assert len(judged) == 1
mail.judge = real_judge

# manual change: example written, next prompt shows it (same-domain first), optional rule
mail.set_message_category({"account": "a", "uid": 12, "category": "later", "also_rule": {"kind": "domain", "value": "p.org"}})
assert tuple(cat(12)) == ("later", "manual")
ex = db.execute("SELECT category,from_addr,subject FROM examples").fetchall()
assert len(ex) == 1 and tuple(ex[0]) == ("later", "p@p.org", "Hello")
assert any(r["kind"] == "domain" and r["value"] == "p.org" for c in mail.list_categories()["categories"] for r in c["rules"])
prompts.clear(); ins(17, "w@w.org", "fresh"); answers[:] = [{"category": "other", "confidence": .9}]
mail.triage_pending("a")
assert "p@p.org | Hello -> later" in prompts[0][1], prompts[0][1]
try:
    mail.set_message_category({"account": "a", "uid": 12, "category": "nope"}); raise SystemExit("unknown category accepted")
except ValueError:
    pass

# resort keeps manual rows; only_unsure touches low confidence only
n = mail.resort({"only_unsure": True})["count"]
assert tuple(cat(12)) == ("later", "manual") and cat(17)[0] is not None
db.execute("UPDATE messages SET confidence=0.95 WHERE uid=17"); db.commit()
n2 = mail.resort({"only_unsure": True})["count"]
assert cat(17)[0] is not None and cat(12)[0] == "later"
n3 = mail.resort({})["count"]
assert cat(17)[0] is None and cat(12)[0] == "later" and n3 >= 1
assert mail.pending("a") >= 1

# suggest: duplicates (name or slug, any case) dropped, nothing saved
answers[:] = [{"categories": [{"name": "SHOP", "description": "x"}, {"name": "Travel", "description": "Trips and bookings"}, {"name": "travel"}, {"name": "Spam"}, {"name": ""}]}]
sug = mail.suggest_categories()["suggestions"]
assert [x["name"] for x in sug] == ["Travel"], sug
assert db.execute("SELECT COUNT(*) FROM categories WHERE name='Travel'").fetchone()[0] == 0

# delete: mail moves to other, rules go; builtins cannot be deleted; other cannot be disabled
mail.save_category({"id": "shop", "name": "Shop 2", "color": "warn", "description": "d"})
db.execute("UPDATE messages SET category='shop' WHERE uid=11"); db.commit()  # resort above cleared it
r = mail.delete_category({"id": "shop"})
assert r["moved"] >= 1 and cat(11)[0] == "other" and db.execute("SELECT COUNT(*) FROM rules WHERE category='shop'").fetchone()[0] == 0
for cid in ("other", "spam"):
    try:
        mail.delete_category({"id": cid}); raise SystemExit(f"deleted {cid}")
    except ValueError:
        pass
mail.save_category({"id": "other", "name": "Other", "color": "faint", "description": "d", "enabled": False})
assert db.execute("SELECT enabled FROM categories WHERE id='other'").fetchone()[0] == 1
mail.save_category({"id": "spam", "name": "Spam", "color": "bad", "description": "d", "enabled": False})
assert db.execute("SELECT enabled FROM categories WHERE id='spam'").fetchone()[0] == 0
for bad_ in ({"name": "x" * 31}, {"name": "ok", "color": "pink"}, {"name": "Later"}, {"name": "ok", "description": "d" * 201}):
    try:
        mail.save_category(bad_); raise SystemExit(f"accepted {bad_}")
    except ValueError:
        pass
assert mail.save_category({"name": "Äpfel & Co"})["id"] == "pfel-co"
# Google logs in with the full address, even if the form was given just the local part
g = mail.validate({"label": "G", "email": "a@sidestream.tech", "username": "a", "provider": "workspace",
                   "imap_host": "imap.gmail.com", "imap_port": 993, "smtp_host": "smtp.gmail.com", "smtp_port": 587})
assert g["username"] == "a@sidestream.tech", g
o = mail.validate({"label": "O", "email": "a@example.org", "username": "a", "provider": "other",
                   "imap_host": "imap.example.org", "imap_port": 993, "smtp_host": "smtp.example.org", "smtp_port": 587})
assert o["username"] == "a", o
print("ok")
