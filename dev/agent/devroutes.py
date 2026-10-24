"""Dev on the host: the routes for dev boxes, previews, Claude Code / ship sessions, web terminals and GitHub,
the terminal stream, and the dev actions (git, projects, new dev box). The work itself is in dev.py / github.py."""
import base64, json, re, time
from pathlib import Path

from dash_sdk import DEVBOX_IDS, DEVBOX_IPS, GH_TOKEN_FILE, PV, action, cts, get, on_start, post, sse_start, stream
from dev import _dims, _winsize, checked_project, claude_code, dev_cts, preview, projects, pv, shell_kill, shell_new, shells, ship_log, term_close, term_get, term_open, term_reaper
from github import _gh_user, github_repos

GH_NEW = str(Path(__file__).resolve().parent / "gh-new")
on_start(term_reaper)


def _pct(vmid, *cmd):
    return ["pct", "exec", str(vmid), "--", *cmd]


# --- routes -------------------------------------------------------------------------------------------------
@get("/projects", quiet=True)
def projects_route(q):
    return projects()


@get("/github/repos", quiet=True)
def github_route(q):
    return github_repos()


@get("/cc/log", quiet=True)
def cc_log(q):
    return claude_code("log", int(q["vmid"]), q["path"], ansi=q.get("ansi") == "1")


@get("/ship/log", quiet=True)
def ship_log_route(q):
    return ship_log(int(q["vmid"]), q["path"], q.get("ansi") == "1")


@get("/preview/log", quiet=True)
def preview_log(q):
    return preview("log", int(q["vmid"]), q["path"], q.get("ansi") == "1")


@get("/shells", quiet=True)
def shells_route(q):
    return shells()


@post(r"/preview/(start|stop)", regex=True)
def preview_do(body, m):
    return preview(m[1], int(body["vmid"]), str(body["path"]))


@post(r"/cc/(start|stop)", regex=True)
def cc_do(body, m):
    return claude_code(m[1], int(body["vmid"]), str(body["path"]), str(body.get("profile", "noven")))


@post("/term/open")
def term_open_route(body):
    return term_open(int(body["vmid"]), str(body.get("path", "")), str(body["target"]),
                     body.get("cols", 80), body.get("rows", 24), body.get("session"))


@post("/shells/new")
def shell_new_route(body):
    return shell_new(int(body["vmid"]))


@post("/shells/kill")
def shell_kill_route(body):
    return shell_kill(int(body["vmid"]), str(body["session"]))


@post("/term/input")
def term_input(body):
    data = body.get("data", "")
    if not isinstance(data, str) or len(data) > 65536:
        raise ValueError("bad input")
    term_get(body["id"]).write(data.encode())
    return {"ok": True}


@post("/term/resize")
def term_resize(body):
    t = term_get(body["id"])
    _winsize(t.fd, *_dims(body["cols"], body["rows"]))
    return {"ok": True}


@post("/term/close")
def term_close_route(body):
    return term_close(body["id"])


@stream("/term/stream")
def term_stream(h, q):
    """server-sent events: `data:` = base64 of the pty output from byte offset `from`, `event: end` when it exits"""
    t, pos = term_get(q["id"]), int(q.get("from", 0))
    sse_start(h)
    t.readers += 1
    try:
        while True:
            with t.cond:
                if pos - t.base >= len(t.buf) and t.alive:
                    t.cond.wait(15)
                start = max(pos - t.base, 0)
                chunk = bytes(t.buf[start:])
                pos = t.base + len(t.buf)
                alive = t.alive
                t.seen = time.time()
            if chunk:
                h.wfile.write(f"id: {pos}\ndata: {base64.b64encode(chunk).decode()}\n\n".encode())
            elif alive:
                h.wfile.write(b": ping\n\n")
            if not alive:
                h.wfile.write(b"event: end\ndata: \n\n")
                h.wfile.flush()
                return
            h.wfile.flush()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        t.readers -= 1
        t.seen = time.time()


# --- actions (run via the approve-then-Run flow; argv fixed, every argument checked here) ------------------
def _dev_project(args):
    """a running dev box plus one of the projects `pv ls` reports in it"""
    try:
        vmid = int(args["vmid"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("vmid must be a dev container id")
    path = str(args.get("path", ""))
    checked_project(vmid, path)
    name = next((c["name"] for c in cts() if c["vmid"] == vmid), vmid)
    return vmid, path, name


@action("git_push")
def a_git_push(args):
    vmid, path, name = _dev_project(args)
    msg = str(args.get("message", "")).strip()
    if msg and (len(msg) > 200 or "\n" in msg):
        raise ValueError("commit message must be one line, max 200 characters")
    short = path.rsplit("/", 1)[-1]
    if msg:
        return f"commit everything in {short} as “{msg}” and push it to GitHub ({name})", \
            _pct(vmid, PV, "push", path, msg), 600
    return f"push the committed work in {short} to GitHub ({name})", _pct(vmid, PV, "push", path), 600


@action("git_fetch")
def a_git_fetch(args):
    vmid, path, name = _dev_project(args)
    return f"fetch {path.rsplit('/', 1)[-1]} from GitHub ({name})", _pct(vmid, PV, "fetch", path), 300


@action("project_new")
def a_project_new(args):
    try:
        vmid = int(args["vmid"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("vmid must be a dev container id")
    if not any(c["vmid"] == vmid and c["status"] == "running" for c in dev_cts()):
        raise ValueError(f"CT {vmid} is not a running dev box")
    name = str(args.get("name", ""))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}", name):
        raise ValueError("project name: letters, digits, dot, dash, underscore")
    repo = str(args.get("repo", "")).strip()
    box = next((c["name"] for c in cts() if c["vmid"] == vmid), vmid)
    if repo:
        if not re.fullmatch(r"(?:git@[\w.-]+:[\w.-]+/[\w.-]+|https://[\w.-]+/[\w.-]+/[\w.-]+)(?:\.git)?", repo):
            raise ValueError("repo must be git@host:owner/name or https://host/owner/name")
        return f"clone {repo} into ~/Projects/GitHub/{name} on {box}", _pct(vmid, PV, "new", name, repo), 1800
    if args.get("github"):
        if not GH_TOKEN_FILE.exists():
            raise ValueError("creating repos on GitHub needs a token (repo scope) in /root/devbox/keys/github_token")
        vis = _visibility(args)
        return (f"create ~/Projects/GitHub/{name} on {box}, create the {vis} GitHub repo {_gh_user()}/{name} and push it",
                ["python3", GH_NEW, "new", str(vmid), name, vis], 1800)
    return f"create a new git project ~/Projects/GitHub/{name} on {box}", _pct(vmid, PV, "new", name), 600


def _visibility(args):
    vis = str(args.get("visibility", "private"))
    if vis not in ("private", "public"):
        raise ValueError("visibility must be private or public")
    return vis


@action("github_publish")
def a_github_publish(args):
    """an existing project that has no remote yet: create the repo on GitHub and push it there"""
    vmid, path, _box = _dev_project(args)
    if not GH_TOKEN_FILE.exists():
        raise ValueError("creating repos on GitHub needs a token (repo scope) in /root/devbox/keys/github_token")
    name = str(args.get("name") or path.rstrip("/").split("/")[-1])
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}", name):
        raise ValueError("repo name: letters, digits, dot, dash, underscore")
    vis = _visibility(args)
    box = next((c["name"] for c in cts() if c["vmid"] == vmid), vmid)
    return (f"create the {vis} GitHub repo {_gh_user()}/{name} and push {path} on {box} to it",
            ["python3", GH_NEW, "publish", str(vmid), path, name, vis], 1800)


@action("project_remove")
def a_project_remove(args):
    """Destructive, so the description the owner reads on the Run button must be exact: it names the box,
    the project and whether anything would be lost. `pv rm` itself refuses unpushed work unless forced,
    and moves the project to ~/.pv-trash rather than deleting it."""
    vmid, path, box = _dev_project(args)
    short = path.rstrip("/").rsplit("/", 1)[-1]
    force = bool(args.get("force"))
    bits = []
    try:
        pr = next((x for x in json.loads(pv(vmid, "ls", "--json")) if x["path"] == path), None)
        g = (pr or {}).get("git") or {}
        if g.get("dirty"):
            bits.append(f"{g['dirty']} uncommitted change(s)")
        if not g.get("repo"):
            bits.append("no GitHub remote")
        elif g.get("ahead"):
            bits.append(f"{g['ahead']} unpushed commit(s)")
    except Exception:
        pass
    # A model asked to "delete X" sets force=true by reflex, so the Run button — the only thing the owner
    # actually reads — has to say what forcing costs, in front, instead of a parenthesis at the end.
    if force and bits:
        desc = (f"FORCE: remove {short} from {box} (CT {vmid}) although it has {' and '.join(bits)} — "
                f"that work exists nowhere else and would live on only as the ~/.pv-trash copy")
    elif force:
        desc = f"remove the project {short} from {box} (CT {vmid}) (clean and pushed) — it is moved to ~/.pv-trash, not deleted"
    else:
        state = f" ({', '.join(bits)}, so this will be refused — push it first)" if bits else " (clean and pushed)"
        desc = f"remove the project {short} from {box} (CT {vmid}){state} — it is moved to ~/.pv-trash, not deleted"
    return desc, _pct(vmid, PV, "rm", path, *(["--force"] if force else [])), 600




@action("newdev")
def a_newdev(args):
    vmid, name, ip = args.get("vmid"), str(args.get("name", "")), str(args.get("ip", ""))
    try:
        vmid = int(vmid)
    except (TypeError, ValueError):
        raise ValueError("vmid must be a number")
    lo, hi = DEVBOX_IDS
    if not lo <= vmid <= hi:
        raise ValueError(f"dev boxes use ids {lo}-{hi}")
    if any(c["vmid"] == vmid for c in cts()):
        raise ValueError(f"CT {vmid} already exists")
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,20}", name):
        raise ValueError("name must be lowercase letters, digits and dashes")
    net, first = DEVBOX_IPS[0].rsplit(".", 1)
    last = DEVBOX_IPS[1].rsplit(".", 1)[1]
    m = re.fullmatch(re.escape(net) + r"\.(\d{1,3})", ip)
    if not m or not int(first) <= int(m[1]) <= int(last):
        raise ValueError(f"ip must be {net}.{first}-{last}")
    if any(c["ip"] == ip for c in cts()):
        raise ValueError(f"{ip} is already used")
    return f"create dev box CT {vmid} {name} at {ip} (newdev, several minutes)", ["/usr/local/bin/newdev", str(vmid), name, ip], 3 * 3600
