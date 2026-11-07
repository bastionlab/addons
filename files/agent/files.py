"""Files: a file browser over a few host folders (roots) with streaming/Range, chunked upload and public share tokens.

Roots live in /etc/dash/files.json; every path is resolved with realpath and must stay inside its root's realpath.
Deleting and renaming are owner-run actions (files_delete / files_rename); the Funnel side reads /files/pub.
"""
import base64, json, mimetypes, os, posixpath, re, secrets, stat, subprocess, tempfile, threading, time
from pathlib import Path
from urllib.parse import quote

from dash_sdk import HOST_IP, action, ct, get, on_start, pct, post, scoped_token, sh, stream

CONF = Path("/etc/dash/files.json")
STATE = Path("/var/lib/dash-files")
SHARES = STATE / "shares.json"
DEFAULT = "/srv/bastion-files"
CHUNK = 1 << 20
MAX_CHUNK = 16 << 20
PUB_TOKEN = Path("/etc/dash/files-pub.token")  # the only bearer the public share proxy holds: GET /files/pub, nothing else
SHARE_ENV = "/etc/dash-share/agent.env"  # in the dashboard CT, readable by the dash-share user
CSP = "sandbox; default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'"
RISKY = ("text/html", "application/xhtml+xml", "image/svg+xml", "text/xml", "application/xml")  # script-capable: download only
PART_RE = re.compile(r"[0-9a-f]{16}")


# --- roots ---------------------------------------------------------------------------------------------------------

def _seed():
    """default root plus read-only bookmarks for the bind mounts of the games and media CTs"""
    Path(DEFAULT).mkdir(parents=True, exist_ok=True)
    roots = [{"id": "files", "label": "Files", "path": DEFAULT, "writable": True}]
    for vmid, label in (("109", "Games"), ("106", "Media")):  # CT 102 mounts only subfolders of what 106 mounts
        for line in sh("pct", "config", vmid).splitlines():
            m = re.match(r"mp\d+: ([^,]+),.*mp=(/[^,\s]+)", line)
            if not m:
                continue
            host = m[1] if m[1].startswith("/") else sh("pvesm", "path", m[1]).strip()  # storage volume -> host path
            if host and Path(host).is_dir() and not any(r["path"] == host for r in roots):
                name = Path(m[2]).name
                lab = label if name in ("games", "medien") else f"{label} {name}"
                roots.append({"id": _slug(lab, roots), "label": lab, "path": host, "writable": False})
    return roots


def _slug(label, roots):
    base = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "root"
    i, rid = 2, base
    while any(r["id"] == rid for r in roots):
        rid, i = f"{base}-{i}", i + 1
    return rid


def _roots():
    try:
        return json.loads(CONF.read_text())["roots"]
    except (OSError, ValueError, KeyError):
        roots = _seed()
        _save_roots(roots)
        return roots


def _save_roots(roots):
    CONF.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONF.with_suffix(".tmp")
    tmp.write_text(json.dumps({"roots": roots}, indent=1))
    tmp.replace(CONF)


_CTS = {"at": 0.0, "v": []}


def _ct_roots():
    """every container as a browsable root (its whole filesystem, via pct exec); never stored, listed fresh every 15 s"""
    if time.time() - _CTS["at"] > 15:
        out = []
        for line in sh("pct", "list").splitlines()[1:]:
            f = line.split()
            if len(f) >= 3 and f[0].isdigit():
                out.append({"id": f"ct-{f[0]}", "label": f"{f[-1]} ({f[0]})", "path": "/", "writable": True, "ct": int(f[0]), "running": f[1] == "running"})
        _CTS.update(at=time.time(), v=out)
    return _CTS["v"]


def _root(rid):
    for r in _roots() + _ct_roots():
        if r["id"] == rid:
            return r
    raise ValueError("unknown root")


_HOME = {}


def _ct_home(vmid):
    """the first real user's home in the CT (/home/<name>), else /root"""
    if vmid not in _HOME:
        out = _ctx(vmid, 'for d in /home/*/; do [ -d "$d" ] && { echo "${d%/}"; exit; }; done; echo /root').decode().strip()
        _HOME[vmid] = out or "/root"
    return _HOME[vmid]


def _ctpath(p, vmid=None):
    """absolute path inside a container for a root-relative p; .. cannot climb above /; "~" = the CT's home"""
    p = str(p or "")
    if p == "~" and vmid:
        return _ct_home(vmid)
    if "\x00" in p:
        raise ValueError("bad path")
    return posixpath.normpath("/" + p)


def _ctx(vmid, script, *args, inp=None, timeout=60):
    """sh -c script inside the CT with args as $1.. (never interpolated); returns stdout bytes"""
    pr = subprocess.run(["pct", "exec", str(vmid), "--", "sh", "-c", script, "sh", *args], input=inp, capture_output=True, timeout=timeout)
    if pr.returncode:
        msg = pr.stderr.decode(errors="replace").strip().splitlines()
        raise ValueError((msg[-1] if msg else f"failed ({pr.returncode})")[:200])
    return pr.stdout


def _resolve(rid, p, write=False):
    """(root, absolute real path); refuses absolute p, .. and symlinks that leave the root"""
    r = _root(rid)
    if r.get("ct"):
        raise ValueError("not available inside a container")
    p = str(p or "")
    if p.startswith("/") or "\x00" in p:
        raise ValueError("bad path")
    base = os.path.realpath(r["path"])
    full = os.path.realpath(os.path.join(base, p))
    if full != base and not full.startswith(base.rstrip("/") + "/"):
        raise ValueError("path outside the root")
    if write and not r.get("writable"):
        raise ValueError("this root is read-only")
    return r, full


def _resolve_entry(rid, p, write=False):
    """(root, path of the entry itself): the parent folder is resolved, the last name is not, so a symlink is acted on
    (deleted / renamed) rather than whatever it points at; the root itself is refused"""
    r = _root(rid)
    if r.get("ct"):
        raise ValueError("not available inside a container")
    p = str(p or "").rstrip("/")
    if not p or p.startswith("/") or "\x00" in p:
        raise ValueError("bad path")
    if write and not r.get("writable"):
        raise ValueError("this root is read-only")
    base = os.path.realpath(r["path"])
    head, name = os.path.split(p)
    if name in ("", ".", ".."):
        raise ValueError("bad path")
    parent = os.path.realpath(os.path.join(base, head))
    if parent != base and not parent.startswith(base.rstrip("/") + "/"):
        raise ValueError("path outside the root")
    return r, os.path.join(parent, name)


def _inside(base, real):
    return real == base or real.startswith(base.rstrip("/") + "/")


def _rel(r, full):
    base = os.path.realpath(r["path"])
    return "" if full == base else os.path.relpath(full, base)


def _name(v):
    v = str(v or "").strip()
    if not v or "/" in v or "\\" in v or re.search(r"[\x00-\x1f\x7f]", v) or v in (".", "..") or len(v.encode()) > 250:
        raise ValueError("bad name")
    return v


def _mime(name):
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


@get("/files/roots", quiet=True)
def files_roots(q):
    return {"roots": [{k: r.get(k) for k in ("id", "label", "path", "writable", "ct", "running")} for r in _roots() + _ct_roots()]}


@post("/files/roots/add")
def roots_add(body):
    label, path = str(body.get("label") or "").strip()[:60], str(body.get("path") or "").strip()
    if not label or not path.startswith("/") or not os.path.isdir(path):
        raise ValueError("needs a label and an existing absolute folder")
    roots = _roots()
    base = _slug(label, [])  # never reuse the id of a removed bookmark (shares point at ids): add 4 hex
    rid = f"{base}-{secrets.token_hex(2)}"
    while any(r["id"] == rid for r in roots):
        rid = f"{base}-{secrets.token_hex(2)}"
    roots.append({"id": rid, "label": label, "path": os.path.realpath(path), "writable": body.get("writable") is True})
    _save_roots(roots)
    return {"ok": True}


@post("/files/roots/remove")
def roots_remove(body):
    rid = str(body.get("id") or "")
    if rid == "files":
        raise ValueError("the Files root cannot be removed")
    roots = [r for r in _roots() if r["id"] != rid]
    _save_roots(roots)
    s = _load_shares()
    if any(v.get("root") == rid for v in s.values()):  # its links must not outlive it
        _save_shares({t: v for t, v in s.items() if v.get("root") != rid})
    return {"ok": True}


# --- browse --------------------------------------------------------------------------------------------------------

def _ct_list(r, p):
    d = _ctpath(p, r["ct"])
    raw = _ctx(r["ct"], 'cd "$1" 2>/dev/null || exit 2; find . -mindepth 1 -maxdepth 1 -printf "%Y\\t%s\\t%T@\\t%f\\0"', d)
    entries = []
    for rec in raw.split(b"\0"):
        f = rec.decode(errors="replace").split("\t", 3)
        if len(f) < 4 or (f[3].startswith(".") and f[3].endswith(".part")):
            continue
        isdir = f[0] == "d"
        try:
            size, mt = int(f[1]), int(float(f[2]))
        except ValueError:
            continue
        entries.append({"name": f[3], "dir": isdir, "size": 0 if isdir else size, "mtime": mt, "mime": "" if isdir else _mime(f[3])})
    entries.sort(key=lambda x: (not x["dir"], x["name"].lower()))
    rel = d.strip("/")
    parts = [x for x in rel.split("/") if x]
    crumbs = [{"name": r["label"], "p": ""}] + [{"name": x, "p": "/".join(parts[:i + 1])} for i, x in enumerate(parts)]
    return {"root": r["id"], "path": rel, "writable": True, "parents": crumbs, "entries": entries, "ct": True}


@get("/files/list", quiet=True)
def files_list(q):
    rr = _root(q.get("root"))
    if rr.get("ct"):
        return _ct_list(rr, q.get("p"))
    r, full = _resolve(q.get("root"), q.get("p"))
    if not os.path.isdir(full):
        raise ValueError("not a folder")
    entries = []
    with os.scandir(full) as it:
        for e in it:
            if e.name.startswith(".") and e.name.endswith(".part"):
                continue
            try:
                st = e.stat()
                d = e.is_dir()
            except OSError:
                continue
            entries.append({"name": e.name, "dir": d, "size": 0 if d else st.st_size, "mtime": int(st.st_mtime), "mime": "" if d else _mime(e.name)})
    entries.sort(key=lambda x: (not x["dir"], x["name"].lower()))
    rel = _rel(r, full)
    parts = [x for x in rel.split("/") if x]
    crumbs = [{"name": r["label"], "p": ""}] + [{"name": x, "p": "/".join(parts[:i + 1])} for i, x in enumerate(parts)]
    return {"root": r["id"], "path": rel, "writable": bool(r.get("writable")), "parents": crumbs, "entries": entries}


def _fuzzy(tokens, name, rel):
    """score of a name against every token (higher = better); None when one token does not match.
    substring beats subsequence beats a hit only in the folder path"""
    n, total = name.lower(), 0
    for t in tokens:
        i = n.find(t)
        if i >= 0:
            total += 100 + (30 if i == 0 else 15 if n[i - 1] in " ._-/" else 0) - min(len(n) - len(t), 40) // 4
            continue
        j = -1
        for ch in t:
            j = n.find(ch, j + 1)
            if j < 0:
                break
        if j >= 0 and len(t) > 1:
            total += 40 - min(len(n), 40) // 4
        elif t in rel.lower():
            total += 20
        else:
            return None
    return total


@get("/files/search", quiet=True)
def files_search(q):
    """fuzzy search of file and folder names below a folder, any root (containers through one find)"""
    tokens = [t for t in str(q.get("q") or "").lower().split() if t][:6]
    if not tokens:
        return {"results": [], "cut": False}
    rr = _root(q.get("root"))
    start = time.time()
    cands = []  # (rel path, isdir, size, mtime)
    cut = False
    if rr.get("ct"):
        d = _ctpath(q.get("p"), rr["ct"])
        pr = subprocess.run(["pct", "exec", str(rr["ct"]), "--", "sh", "-c",
                             'find "$1" -mindepth 1 \\( -path /proc -o -path /sys -o -path /dev \\) -prune -o -printf "%Y\\t%s\\t%T@\\t%p\\0" 2>/dev/null | head -c 60000000', "sh", d],
                            capture_output=True, timeout=40)
        base = d.rstrip("/")
        cut = len(pr.stdout) >= 60000000
        for rec in pr.stdout.split(b"\0"):
            f = rec.decode(errors="replace").split("\t", 3)
            if len(f) == 4 and f[3].startswith(base + "/"):
                try:
                    cands.append((f[3][len(base) + 1:], f[0] == "d", int(f[1]), int(float(f[2]))))
                except ValueError:
                    pass
    else:
        r, full = _resolve(q.get("root"), q.get("p"))
        if not os.path.isdir(full):
            raise ValueError("not a folder")
        b = os.path.realpath(r["path"])
        for dp, dns, fns in os.walk(full):
            if time.time() - start > 15 or len(cands) > 400000:
                cut = True
                break
            for nm, isd in [(x, True) for x in dns] + [(x, False) for x in fns]:
                if nm.startswith(".") and nm.endswith(".part"):
                    continue
                try:
                    st = os.lstat(os.path.join(dp, nm))
                except OSError:
                    continue
                cands.append((os.path.relpath(os.path.join(dp, nm), full), isd, 0 if isd else st.st_size, int(st.st_mtime)))
    scored = []
    for rel, isd, size, mt in cands:
        sc = _fuzzy(tokens, rel.rsplit("/", 1)[-1], rel)
        if sc is not None:
            scored.append((-sc, len(rel), rel, isd, size, mt))
    scored.sort()
    base_rel = _ctpath(q.get("p"), rr["ct"]).strip("/") if rr.get("ct") else _rel(r, full)
    out = []
    for _, _, rel, isd, size, mt in scored[:100]:
        name = rel.rsplit("/", 1)[-1]
        out.append({"name": name, "dir": isd, "size": size, "mtime": mt, "mime": "" if isd else _mime(name),
                    "p": f"{base_rel}/{rel}" if base_rel else rel, "in": rel.rsplit("/", 1)[0] if "/" in rel else ""})
    return {"results": out, "cut": cut, "total": len(scored)}


@get("/files/stat", quiet=True)
def files_stat(q):
    rr = _root(q.get("root"))
    if rr.get("ct"):
        d = _ctpath(q.get("p"), rr["ct"])
        out = _ctx(rr["ct"], 'stat -L -c "%F|%s|%Y" -- "$1"', d).decode().strip().split("|")
        if len(out) != 3:
            raise ValueError("no such file")
        isdir = out[0] == "directory"
        return {"name": posixpath.basename(d) or "/", "dir": isdir, "size": int(out[1]), "mtime": int(out[2]), "mime": _mime(d)}
    r, full = _resolve(q.get("root"), q.get("p"))
    if not os.path.exists(full):
        raise ValueError("no such file")
    st = os.stat(full)
    return {"name": os.path.basename(full), "dir": os.path.isdir(full), "size": st.st_size, "mtime": int(st.st_mtime), "mime": _mime(full)}


def _fail(h, code, msg, extra=None):
    body = json.dumps({"error": msg}).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(body)))
    for k, v in (extra or {}).items():
        h.send_header(k, v)
    h.end_headers()
    h.wfile.write(body)


def _head(h, code, name, size, start, end, dl):
    mime = _mime(name)
    risky = mime in RISKY
    h.send_response(code)
    h.send_header("Content-Type", "application/octet-stream" if risky else mime)
    h.send_header("X-Content-Type-Options", "nosniff")
    if mime != "application/pdf":  # Chrome's PDF viewer does not run inside a sandboxed frame
        h.send_header("Content-Security-Policy", CSP)
    h.send_header("Accept-Ranges", "bytes")
    h.send_header("Content-Length", str(end - start + 1))
    if code == 206:
        h.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    h.send_header("Content-Disposition", f"{'attachment' if dl or risky else 'inline'}; filename*=UTF-8''{quote(name, safe='')}")
    h.end_headers()


def _serve_ct(h, r, p, dl):
    """a file inside a container, streamed through pct exec (tail | head for a Range)"""
    d = _ctpath(p, r["ct"])
    try:
        info = _ctx(r["ct"], 'stat -L -c "%F|%s" -- "$1"', d).decode().strip().split("|")
        if info[0] != "regular file" and info[0] != "regular empty file":
            return _fail(h, 404, "no such file")
        size = int(info[1])
    except (ValueError, IndexError) as e:
        return _fail(h, 404, str(e) or "no such file")
    start, end, code = 0, size - 1, 200
    rng = h.headers.get("Range")
    if rng and "," not in rng:
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
        if not m or not (m[1] or m[2]):
            return _fail(h, 416, "bad range", {"Content-Range": f"bytes */{size}"})
        if m[1]:
            start = int(m[1])
            end = min(int(m[2]), size - 1) if m[2] else size - 1
        else:
            start, end = max(size - int(m[2]), 0), size - 1
        if start >= size or start > end:
            return _fail(h, 416, "range not satisfiable", {"Content-Range": f"bytes */{size}"})
        code = 206
    if size == 0:
        end = -1
    _head(h, code, posixpath.basename(d), size, start, end, dl)
    if end < start:
        return
    pr = subprocess.Popen(["pct", "exec", str(r["ct"]), "--", "sh", "-c", 'tail -c +"$2" -- "$1" | head -c "$3"', "sh", d, str(start + 1), str(end - start + 1)],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        while chunk := pr.stdout.read(CHUNK):
            h.wfile.write(chunk)
    except (BrokenPipeError, ConnectionResetError, TimeoutError):
        pass
    finally:
        pr.kill()
        pr.wait()


def _serve(h, full, dl, base):
    """the file with Range support: 200, 206 (one range) or 416. It is opened first and the fd's real path checked
    against the root, so a symlink swapped in after the path check cannot lead out"""
    try:
        fd = os.open(full, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError:
        return _fail(h, 404, "no such file")
    try:
        if not _inside(base, os.path.realpath(f"/proc/self/fd/{fd}")) or not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            return _fail(h, 404, "no such file")
        size = os.fstat(fd).st_size
        f = os.fdopen(fd, "rb")
    except OSError:
        os.close(fd)
        return _fail(h, 404, "no such file")
    with f:
        start, end, code = 0, size - 1, 200
        rng = h.headers.get("Range")
        if rng and "," not in rng:  # several ranges: ignore and send the whole file
            m = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
            if not m or not (m[1] or m[2]):
                return _fail(h, 416, "bad range", {"Content-Range": f"bytes */{size}"})
            if m[1]:
                start = int(m[1])
                end = min(int(m[2]), size - 1) if m[2] else size - 1
            else:
                start, end = max(size - int(m[2]), 0), size - 1
            if start >= size or start > end:
                return _fail(h, 416, "range not satisfiable", {"Content-Range": f"bytes */{size}"})
            code = 206
        _head(h, code, os.path.basename(full), size, start, end, dl)
        try:
            f.seek(start)
            left = end - start + 1
            while left > 0 and (chunk := f.read(min(CHUNK, left))):
                h.wfile.write(chunk)
                left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass


@stream("/files/raw")
def files_raw(h, q):
    try:
        rr = _root(q.get("root"))
        if rr.get("ct"):
            return _serve_ct(h, rr, q.get("p"), q.get("dl") == "1")
        r, full = _resolve(q.get("root"), q.get("p"))
    except ValueError as e:
        return _fail(h, 400, str(e))
    _serve(h, full, q.get("dl") == "1", os.path.realpath(r["path"]))


# --- upload / folders ----------------------------------------------------------------------------------------------

def _ct_upload(r, body):
    """same chunk protocol as host roots; the part file takes the folder's owner, the final name never overwrites"""
    d = _ctpath(body.get("p"), r["ct"])
    name = _name(body.get("name"))
    off = int(body.get("offset", 0))
    data = base64.b64decode(body.get("data") or "")
    if len(data) > MAX_CHUNK:
        raise ValueError("chunk too large")
    if off == 0:
        uid = secrets.token_hex(8)
        _ctx(r["ct"], '[ -d "$1" ] || { echo "not a folder" >&2; exit 3; }; set -C; cat > "$1/.$2.part" || exit 4; chown --reference="$1" "$1/.$2.part" 2>/dev/null; true', d, uid, inp=data, timeout=300)
    else:
        uid = str(body.get("id") or "")
        if not PART_RE.fullmatch(uid):
            raise ValueError("upload out of step, start again")
        _ctx(r["ct"], 'f="$1/.$2.part"; [ "$(stat -c %s "$f" 2>/dev/null)" = "$3" ] || { echo "upload out of step, start again" >&2; exit 4; }; cat >> "$f"', d, uid, str(off), inp=data, timeout=300)
    final = body.get("final") is True
    out = name
    if final:
        script = (
            'd=$1; n=$2; p="$1/.$3.part"; out=$n; i=2\n'
            'while [ -e "$d/$out" ] || [ -L "$d/$out" ]; do\n'
            '  case $n in *.*) stem=${n%.*}; ext=.${n##*.};; *) stem=$n; ext=;; esac\n'
            '  out="$stem ($i)$ext"; i=$((i+1))\n'
            'done\n'
            'ln "$p" "$d/$out" && rm -f "$p" && printf %s "$out"')
        out = _ctx(r["ct"], script, d, name, uid).decode()
    return {"ok": True, "name": out, "done": final, "id": uid}


@post("/files/upload")
def files_upload(body):
    """chunks of one file: the first (offset 0) creates `.<id>.part` and returns the id, later ones must send it"""
    rr = _root(body.get("root"))
    if rr.get("ct"):
        return _ct_upload(rr, body)
    r, d = _resolve(body.get("root"), body.get("p"), write=True)
    if not os.path.isdir(d):
        raise ValueError("not a folder")
    base = os.path.realpath(r["path"])
    name = _name(body.get("name"))
    off = int(body.get("offset", 0))
    data = base64.b64decode(body.get("data") or "")
    if len(data) > MAX_CHUNK:
        raise ValueError("chunk too large")
    if off == 0:
        uid = secrets.token_hex(8)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    else:
        uid = str(body.get("id") or "")
        if not PART_RE.fullmatch(uid):
            raise ValueError("upload out of step, start again")
        flags = os.O_WRONLY | os.O_APPEND
    part = os.path.join(d, f".{uid}.part")
    try:
        fd = os.open(part, flags | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
    except OSError:
        raise ValueError("upload out of step, start again")
    with os.fdopen(fd, "ab") as f:
        if not _inside(base, os.path.realpath(f"/proc/self/fd/{f.fileno()}")):
            os.unlink(part)
            raise ValueError("path outside the root")
        if os.fstat(f.fileno()).st_size != off:
            raise ValueError("upload out of step, start again")
        f.write(data)
    final = body.get("final") is True
    out = name
    if final:
        stem, ext = os.path.splitext(name)
        n = 2
        while True:
            try:
                os.link(part, os.path.join(d, out))  # fails if the name exists: never overwrites
                break
            except FileExistsError:
                out, n = f"{stem} ({n}){ext}", n + 1
        os.unlink(part)
    return {"ok": True, "name": out, "done": final, "id": uid}


def _sweep():
    """abandoned `.<id>.part` files (an upload that never finished) go after a day, within 4 levels of a writable root"""
    old = time.time() - 86400
    for r in _roots():
        if not r.get("writable"):
            continue
        base = os.path.realpath(r["path"])
        for dp, dns, fns in os.walk(base):
            if dp[len(base):].count("/") >= 4:
                dns[:] = []
            for fn in fns:
                if fn.startswith(".") and fn.endswith(".part") and PART_RE.fullmatch(fn[1:-5]):
                    try:
                        fp = os.path.join(dp, fn)
                        st = os.lstat(fp)
                        if stat.S_ISREG(st.st_mode) and st.st_mtime < old:
                            os.unlink(fp)
                    except OSError:
                        pass


@post("/files/mkdir")
def files_mkdir(body):
    rr = _root(body.get("root"))
    if rr.get("ct"):
        _ctx(rr["ct"], 'mkdir -- "$1/$2" && chown --reference="$1" "$1/$2" 2>/dev/null; true', _ctpath(body.get("p"), rr["ct"]), _name(body.get("name")))
        return {"ok": True}
    _, d = _resolve(body.get("root"), body.get("p"), write=True)
    os.mkdir(os.path.join(d, _name(body.get("name"))))
    return {"ok": True}


# --- shares --------------------------------------------------------------------------------------------------------

def _load_shares():
    try:
        return json.loads(SHARES.read_text())
    except (OSError, ValueError):
        return {}


def _save_shares(d):
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = SHARES.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(d, f, indent=1)
    tmp.replace(SHARES)


@post("/files/share")
def files_share(body):
    r, full = _resolve(body.get("root"), body.get("p"))
    if not os.path.isfile(full):
        raise ValueError("only files can be shared")
    if not r.get("writable"):  # bookmarks (Media, Games) hold third-party works: public links only for your own Files
        raise ValueError("public links only from writable folders")
    hours = min(max(float(body.get("ttl_hours") or 72), 0.1), 2160)
    now = int(time.time())
    s = _load_shares()
    s = {t: v for t, v in s.items() if v["expires"] > now}
    tok = secrets.token_urlsafe(24)
    s[tok] = {"root": r["id"], "p": _rel(r, full), "expires": now + int(hours * 3600), "created": now}
    _save_shares(s)
    return {"token": tok, "expires": s[tok]["expires"]}


@get("/files/shares", quiet=True)
def files_shares(q):
    now = int(time.time())
    return {"shares": sorted(({"token": t, **v, "name": os.path.basename(v["p"]), "expired": v["expires"] <= now} for t, v in _load_shares().items()),
                             key=lambda x: -x["created"])}


@post("/files/share/revoke")
def files_revoke(body):
    s = _load_shares()
    s.pop(str(body.get("token") or ""), None)
    _save_shares(s)
    return {"ok": True}


@stream("/files/pub")
def files_pub(h, q):
    v = _load_shares().get(q.get("t") or "")
    if not v or v["expires"] <= time.time():
        return _fail(h, 404, "link expired or unknown")
    try:
        r, full = _resolve(v["root"], v["p"])
    except ValueError:
        return _fail(h, 404, "gone")
    if not r.get("writable"):
        return _fail(h, 404, "gone")
    _serve(h, full, q.get("dl") == "1", os.path.realpath(r["path"]))


# --- owner-run actions ---------------------------------------------------------------------------------------------

@action("files_delete")
def a_files_delete(args):
    """one path or a list of paths (folders too); each entry is checked and acted on as itself"""
    ps = args.get("p")
    ps = ps if isinstance(ps, list) else [ps]
    if not ps or len(ps) > 200:
        raise ValueError("pick 1 to 200 entries")
    rr = _root(args.get("root"))
    if rr.get("ct"):
        fulls = [_ctpath(str(p).rstrip("/")) for p in ps]
        if any(f.count("/") < 2 for f in fulls):
            raise ValueError("top-level folders of a container cannot be deleted here")
        return (f"delete {len(fulls)} item(s) in {rr['label']}: " + ", ".join(fulls[:5]) + (" ..." if len(fulls) > 5 else ""),
                ["pct", "exec", str(rr["ct"]), "--", "rm", "-rf", "--", *fulls], 600)
    labels, fulls = [], []
    for p in ps:
        r, full = _resolve_entry(args.get("root"), p, write=True)
        if not os.path.lexists(full):
            raise ValueError("no such file")
        labels.append(_rel(r, full))
        fulls.append(full)
    desc = f"delete {len(fulls)} item(s) in {r['label']}: " + ", ".join(labels[:5]) + (" ..." if len(labels) > 5 else "")
    return desc, ["rm", "-rf", "--", *fulls], 600


@action("files_rename")
def a_files_rename(args):
    rr = _root(args.get("root"))
    if rr.get("ct"):
        src = _ctpath(str(args.get("p") or "").rstrip("/"))
        if src.count("/") < 2:
            raise ValueError("top-level folders of a container cannot be renamed here")
        name = _name(args.get("name"))
        return f"rename {posixpath.basename(src)} to {name} in {rr['label']}", ["pct", "exec", str(rr["ct"]), "--", "mv", "-n", "-T", "--", src, posixpath.join(posixpath.dirname(src), name)], 60
    r, full = _resolve_entry(args.get("root"), args.get("p"), write=True)
    name = _name(args.get("name"))
    dst = os.path.join(os.path.dirname(full), name)
    if not os.path.lexists(full):
        raise ValueError("no such file")
    if os.path.lexists(dst):
        raise ValueError("that name already exists")
    return f"rename {os.path.basename(full)} to {name}", ["mv", "-n", "-T", "--", full, dst], 60


# --- the public proxy's narrow credential --------------------------------------------------------------------------

def _pub_token():
    """/etc/dash/files-pub.token (0600) = the bearer share.mjs sends; the agent accepts it for GET /files/pub only"""
    if not PUB_TOKEN.exists():
        PUB_TOKEN.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(PUB_TOKEN, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_urlsafe(32) + "\n")
    os.chmod(PUB_TOKEN, 0o600)
    return PUB_TOKEN.read_text().strip()


def _push_env():
    """put the agent URL + that token where dash-share (CT, non-root) can read them; only when the content differs"""
    want = f"DASH_AGENT_URL=http://{HOST_IP}:{os.environ.get('AGENT_PORT', '7070')}\nDASH_FILES_TOKEN={_pub_token()}\n"
    if not ct("dash"):
        return
    pct("dash", "sh", "-c", "getent group dash-share >/dev/null || groupadd --system dash-share; mkdir -p /etc/dash-share; chgrp dash-share /etc/dash-share; chmod 750 /etc/dash-share")
    if pct("dash", "cat", SHARE_ENV) != want:
        with tempfile.TemporaryDirectory() as td:
            tmp = os.path.join(td, "agent.env")
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(want)
            sh("pct", "push", str(ct("dash")), tmp, SHARE_ENV, "--perms", "640", "--user", "0", "--group", "0")
    pct("dash", "sh", "-c", f"chgrp dash-share {SHARE_ENV}; chmod 640 {SHARE_ENV}")


scoped_token("/files/pub", PUB_TOKEN)
try:
    _pub_token()
except OSError:
    pass


@on_start
def _housekeeping():
    try:
        _push_env()
    except Exception as e:
        print(f"files: could not push {SHARE_ENV}: {e}", flush=True)

    def loop():
        while True:
            try:
                _sweep()
            except Exception:
                pass
            time.sleep(3600)
    threading.Thread(target=loop, daemon=True).start()
