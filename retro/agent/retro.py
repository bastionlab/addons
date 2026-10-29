"""Retro games: one library of game files on the games CT's disk (<mp /games>/roms/<system>/), played in the browser
with EmulatorJS (phone + PC, nothing to install) or, for 3DS, streamed from Azahar in the games CT over Moonlight.

Saves live next to the library (<mp>/retro-saves/<system>/<file>.srm|.state) so every device continues the same game.
"Get games" is a catalogue of free, legally shared homebrew (Homebrew Hub for GB/GBC/GBA, Retrobrews for
NES/SNES/Sega/Atari); commercial games come from your own dumps via upload or the Samba share.
"""
import base64, json, os, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dash_sdk import action, cached, ct, get, invalidate, post, sh, stream, stale_after_jobs

CT = ct("games")
STATE = Path("/var/lib/dash-retro")
UA = {"User-Agent": "bastion-retro"}
MAX_FILE = 4 << 30
# key: (name, EmulatorJS core or "stream", file extensions, generation order for sorting)
SYSTEMS = {
    "nes": ("NES", "nes", "nes fds unf unif", 3),
    "snes": ("SNES", "snes", "sfc smc fig swc", 4),
    "n64": ("Nintendo 64", "n64", "n64 z64 v64", 5),
    "gb": ("Game Boy", "gb", "gb", 4),
    "gbc": ("Game Boy Color", "gbc", "gbc", 5),
    "gba": ("Game Boy Advance", "gba", "gba", 6),
    "nds": ("Nintendo DS", "nds", "nds", 7),
    "3ds": ("Nintendo 3DS", "stream", "3ds cci cia cxi", 8),
    "vb": ("Virtual Boy", "vb", "vb vboy", 5),
    "sms": ("Master System", "segaMS", "sms", 3),
    "gg": ("Game Gear", "segaGG", "gg", 4),
    "md": ("Mega Drive", "segaMD", "md gen smd bin", 4),
    "segacd": ("Sega CD", "segaCD", "chd cue iso", 4),
    "32x": ("Sega 32X", "sega32x", "32x", 4),
    "saturn": ("Saturn", "segaSaturn", "chd cue iso", 5),
    "psx": ("PlayStation", "psx", "chd pbp cue iso img", 5),
    "psp": ("PSP", "psp", "iso cso", 7),
    "pce": ("PC Engine", "pce", "pce", 4),
    "ngp": ("Neo Geo Pocket", "ngp", "ngp ngc", 5),
    "ws": ("WonderSwan", "ws", "ws wsc", 5),
    "lynx": ("Atari Lynx", "lynx", "lnx", 4),
    "a2600": ("Atari 2600", "atari2600", "a26 bin", 2),
    "a7800": ("Atari 7800", "atari7800", "a78", 3),
    "arcade": ("Arcade", "arcade", "zip", 4),
}
ARCHIVES = {"zip", "7z"}
SYS_RE = re.compile("|".join(SYSTEMS))
NAME_RE = re.compile(r"[^/\\\x00-\x1f]{1,180}")
COVER_EXT = ("png", "jpg", "jpeg", "webp")
stale_after_jobs("library")


def _root():
    """the host path behind the games CT's /games mount point (pvesm resolves tank:subvol-109-disk-0)"""
    return _games_mp()


@cached(300)
def _games_mp():
    for line in sh("pct", "config", str(CT)).splitlines():
        m = re.match(r"mp\d+: ([^,]+),.*mp=/games\b", line)
        if m:
            p = sh("pvesm", "path", m[1]).strip()
            if p and Path(p).is_dir():
                return p
    raise ValueError(f"CT {CT} has no /games mount point")


def _sys(v):
    v = str(v or "")
    if not SYS_RE.fullmatch(v):
        raise ValueError("unknown system")
    return v


def _name(v):
    v = str(v or "").strip()
    if not NAME_RE.fullmatch(v) or v.startswith(".") or v in ("..", "bios"):
        raise ValueError("bad file name")
    return v


def _exts(s):
    return set(SYSTEMS[s][2].split()) | (set() if SYSTEMS[s][1] == "stream" else ARCHIVES)


def _rom(s, name):
    p = Path(_root(), "roms", _sys(s), _name(name))
    if not p.is_file():
        raise ValueError("no such game")
    return p


def _saves(s):
    d = Path(_root(), "retro-saves", s)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _own(p):
    try:
        os.chown(p, 1000, 1000)  # the games CT is privileged: uid 1000 = its retro / Samba user
    except OSError:
        pass


def _title(stem):
    """'Pokemon Alpha Sapphire (Europe) (En,Ja) (Rev 2)' → title + the tags in brackets"""
    tags = re.findall(r"[(\[]([^)\]]*)[)\]]", stem)
    t = re.sub(r"\s*[(\[][^)\]]*[)\]]", "", stem).replace("_", " ").strip() or stem
    return t, tags


def _ct_status():
    out = sh("pct", "status", str(CT), timeout=10)
    return out.split(":", 1)[1].strip() if ":" in out else "missing"


@get("/retro", quiet=True)
def retro_route(q):
    return library()


@cached(5)
def library():
    root = Path(_root())
    games = []
    for s in SYSTEMS:
        d = root / "roms" / s
        if not d.is_dir():
            continue
        exts = _exts(s)
        files = list(d.iterdir())
        covers = {f.stem: f.name for f in files if f.suffix[1:].lower() in COVER_EXT}
        saves = root / "retro-saves" / s
        for f in files:
            if not f.is_file() or f.name.startswith(".") or f.suffix[1:].lower() not in exts:
                continue
            if s == "md" and f.suffix.lower() == ".bin" and f.with_suffix(".cue").exists():
                continue
            st = f.stat()
            title, tags = _title(f.stem)
            games.append({"sys": s, "file": f.name, "title": title, "tags": tags, "size": st.st_size, "added": int(st.st_mtime),
                          "cover": covers.get(f.stem), "saved": (saves / f"{f.name}.srm").exists() or (saves / f"{f.name}.state").exists()})
    games.sort(key=lambda g: g["title"].lower())
    du = os.statvfs(root)
    bios = [s for s in SYSTEMS if any(f.is_file() for f in (root / "roms" / s / "bios").glob("*"))]
    return {"ct": CT, "ctStatus": _ct_status(), "games": games, "free": du.f_bavail * du.f_frsize, "bios": bios,
            "systems": [{"key": k, "name": v[0], "core": v[1], "exts": v[2].split(), "gen": v[3]} for k, v in SYSTEMS.items()]}


@stream("/retro/file")
def retro_file(h, q):
    """the bytes of a game (kind=rom), its cover (kind=cover) or a BIOS (kind=bios); a 404 for missing saves"""
    try:
        s, kind = _sys(q.get("sys")), q.get("kind", "rom")
        if kind == "rom":
            p = _rom(s, q.get("name"))
        elif kind == "cover":
            p = Path(_root(), "roms", s, _name(q.get("name")))
            if p.suffix[1:].lower() not in COVER_EXT:
                raise ValueError("not an image")
        elif kind in ("srm", "state"):
            p = _saves(s) / f"{_name(q.get('name'))}.{kind}"
        elif kind == "bios":
            p = next((f for f in Path(_root(), "roms", s, "bios").glob("*") if f.is_file()), Path("/nonexistent"))
        else:
            raise ValueError("bad kind")
        if not p.is_file():
            h.send_response(404)
            h.send_header("Content-Length", "0")
            h.end_headers()
            return
    except (ValueError, KeyError) as e:
        body = json.dumps({"error": str(e)}).encode()
        h.send_response(400)
        h.send_header("Content-Type", "application/json")
        h.send_header("Content-Length", str(len(body)))
        h.end_headers()
        h.wfile.write(body)
        return
    h.send_response(200)
    h.send_header("Content-Type", "application/octet-stream")
    h.send_header("Content-Length", str(p.stat().st_size))
    h.send_header("X-File-Name", p.name.encode("ascii", "replace").decode())
    h.end_headers()
    try:
        with p.open("rb") as f:
            while chunk := f.read(1 << 20):
                h.wfile.write(chunk)
    except (BrokenPipeError, ConnectionResetError):
        pass


@post("/retro/upload")
def retro_upload(body):
    """one chunk of a game file, written to .part-<name> and renamed once the last byte is in"""
    s, name = _sys(body.get("sys")), _name(body.get("name"))
    off, total = int(body.get("offset", 0)), int(body.get("total", 0))
    target = body.get("kind", "rom")
    ext = name.rsplit(".", 1)[-1].lower()
    if target == "rom" and ext not in _exts(s) | set(COVER_EXT):
        raise ValueError(f"{SYSTEMS[s][0]} takes .{', .'.join(sorted(_exts(s)))}")
    if not 0 < total <= MAX_FILE or not 0 <= off < total:
        raise ValueError("bad size")
    data = base64.b64decode(body.get("data") or "")
    d = Path(_root(), "roms", s, "bios") if target == "bios" else Path(_root(), "roms", s)
    d.mkdir(parents=True, exist_ok=True)
    _own(d.parent)
    _own(d)
    part = d / f".part-{name}"
    if off == 0:
        part.unlink(missing_ok=True)
    elif not part.exists() or part.stat().st_size != off:
        raise ValueError("upload out of step, start again")
    with part.open("ab") as f:
        f.write(data)
    done = off + len(data) >= total
    if done:
        if target == "bios":
            for old in d.glob("*"):
                if old.is_file() and old != part:
                    old.unlink()
        part.rename(d / name)
        _own(d / name)
        invalidate("library")
    return {"ok": True, "done": done, "got": off + len(data)}


@post("/retro/save")
def retro_save(body):
    """a save from the browser player: srm = the game's own save (battery), state = a save state"""
    s, name, kind = _sys(body.get("sys")), _name(body.get("name")), body.get("kind")
    if kind not in ("srm", "state"):
        raise ValueError("bad kind")
    _rom(s, name)
    data = base64.b64decode(body.get("data") or "")
    if not data or len(data) > 64 << 20:
        raise ValueError("bad save")
    p = _saves(s) / f"{name}.{kind}"
    tmp = p.with_name(f".{p.name}.tmp")
    tmp.write_bytes(data)
    if p.exists():
        os.replace(p, p.with_name(f"{p.name}.bak"))  # one step back, in case a device writes an empty/new save over it
    tmp.rename(p)
    _own(p)
    invalidate("library")
    return {"ok": True, "at": int(time.time())}


@action("retro_delete")
def a_retro_delete(args):
    """removes a game (and its cover); its saves stay in retro-saves so a re-upload continues where it was"""
    p = _rom(args.get("sys"), args.get("name"))
    covers = [str(c) for e in COVER_EXT if (c := p.with_suffix(f".{e}")).exists()]
    return f"delete {SYSTEMS[p.parent.name][0]} game {p.name} (saves are kept)", ["rm", "-f", "--", str(p), *covers], 30


# --- free homebrew catalogue ---------------------------------------------------------------------------------------

HH = "https://hh3.gbdev.io"
HH_SYS = {"GB": "gb", "GBC": "gbc", "GBA": "gba"}
RB = {"nes": "nes-games", "snes": "snes-games", "gbc": "gbc-games", "gba": "gba-games", "md": "md-games",
      "sms": "sms-games", "a2600": "atari2600-games"}


def _fetch(url, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def _hh():
    out, page, pages = [], 1, 1
    while page <= pages and page <= 20:
        d = json.loads(_fetch(f"{HH}/api/search?typetag=game&results=200&page={page}"))
        pages = d.get("page_total", 1)
        for e in d.get("entries", []):
            s = HH_SYS.get(e.get("platform"))
            files = [f for f in e.get("files", []) if f.get("playable")]
            f = next((f for f in files if f.get("default")), files[0] if files else None)
            if not s or not f:
                continue
            base = f"{HH}/static/{e.get('basepath', 'database-gb')}/entries/{e['slug']}"
            shots = e.get("screenshots") or []
            out.append({"id": f"hh:{e['slug']}", "src": "Homebrew Hub", "sys": s, "title": e.get("title") or e["slug"],
                        "dev": ", ".join(d.get("name", "") for d in e.get("developer") or [] if isinstance(d, dict))[:80],
                        "desc": (e.get("description") or "")[:400], "tags": (e.get("tags") or [])[:5], "date": e.get("date", ""),
                        "cover": f"{base}/{shots[0]}" if shots else "", "url": f"{base}/{f['filename']}",
                        "file": Path(f["filename"]).name, "link": f"{HH}/{e['slug']}"})
        page += 1
    return out


def _rb(s, repo):
    tree = json.loads(_fetch(f"https://api.github.com/repos/retrobrews/{repo}/git/trees/master"))["tree"]
    names = {t["path"] for t in tree if t["type"] == "blob"}
    raw = f"https://raw.githubusercontent.com/retrobrews/{repo}/master"
    out = []
    for n in sorted(names):
        stem, _, ext = n.rpartition(".")
        if ext.lower() not in SYSTEMS[s][2].split() + ["zip"] or not stem:
            continue
        title = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem).replace("-", " ").replace("_", " ").strip()
        cover = next((f"{raw}/{stem}.{c}" for c in COVER_EXT if f"{stem}.{c}" in names), "")
        out.append({"id": f"rb:{s}:{n}", "src": "Retrobrews", "sys": s, "title": title[:1].upper() + title[1:], "dev": "",
                    "desc": "", "tags": [], "date": "", "cover": cover, "url": f"{raw}/{n}", "file": n,
                    "info": f"{raw}/{stem}.txt" if f"{stem}.txt" in names else "", "link": f"https://github.com/retrobrews/{repo}"})
    return out


def _catalog():
    """the catalogue, refreshed once a day (kept on disk: GitHub allows 60 anonymous calls an hour)"""
    f = STATE / "catalog.json"
    try:
        if time.time() - f.stat().st_mtime < 86400:
            return json.loads(f.read_text())
    except (OSError, ValueError):
        pass
    with ThreadPoolExecutor(8) as ex:
        jobs = [ex.submit(_hh)] + [ex.submit(_rb, s, r) for s, r in RB.items()]
        parts = []
        for j in jobs:
            try:
                parts.append(j.result())
            except Exception:
                parts.append(None)
    if any(p is None for p in parts) and f.exists():
        return json.loads(f.read_text())  # one source down: keep yesterday's list rather than a partial one
    items = [i for p in parts if p for i in p]
    STATE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(items))
    return items


def _dest(i):
    """the file name a catalogue game gets in the library: its title, so the library reads well"""
    t = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", i["title"]).strip(" .")[:120] or Path(i["file"]).stem
    return f"{t}{Path(i['file']).suffix.lower()}"


@get("/retro/catalog", quiet=True)
def retro_catalog(q):
    have = {(g["sys"], g["file"]) for g in library()["games"]}
    return {"items": [{**i, "have": (i["sys"], _dest(i)) in have, "dest": _dest(i)} for i in _catalog()]}


@get("/retro/info")
def retro_info(q):
    """a Retrobrews game's readme (the catalogue only has the file name)"""
    i = next((i for i in _catalog() if i["id"] == q.get("id")), None)
    if not i or not i.get("info"):
        return {"text": ""}
    return {"text": _fetch(i["info"], 15).decode("utf-8", "replace")[:3000]}


@post("/retro/get")
def retro_get(body):
    """downloads one catalogue game (and its cover) into the library"""
    i = next((i for i in _catalog() if i["id"] == body.get("id")), None)
    if not i:
        raise ValueError("not in the catalogue")
    d = Path(_root(), "roms", i["sys"])
    d.mkdir(parents=True, exist_ok=True)
    _own(d.parent)
    _own(d)
    name = _name(_dest(i))
    data = _fetch(i["url"], 120)
    if len(data) > 256 << 20:
        raise ValueError("too big")
    (d / name).write_bytes(data)
    _own(d / name)
    if i.get("cover"):
        try:
            ext = i["cover"].rsplit(".", 1)[-1].lower()
            c = d / f"{Path(name).stem}.{ext if ext in COVER_EXT else 'png'}"
            c.write_bytes(_fetch(i["cover"], 30))
            _own(c)
        except Exception:
            pass
    invalidate("library")
    return {"ok": True, "sys": i["sys"], "file": name}
