#!/usr/bin/env python3
"""check.py — the gate an add-on passes before it is merged into pvedash/addons (and so reaches every install).

  check.py --id <id> --pr <PR checkout> --base <main checkout> [--files <changed list>] [--author <login>]
           [--admin] [--lint] [--report <out.md>]                          exit 0 = merge, 1 = not

Run by .github/workflows/publish.yml on every `publish/<id>` pull request, and by the core's addon-publish on pve
before it pushes (without --lint). It only reads the PR's files, never runs them.

  scope     the PR touches <id>/ only (no other add-on, no index.json, no .github)
  manifest  addon.yaml is complete, id = folder, version x.y.z and higher than main's
  owner     an existing add-on is published by its author (or an org admin); a new one carries its publisher
  safety    addon_scan.py: reverse shells, miners, decode-and-run, ssh keys, dashboard secrets, binaries, ClamAV
  leaks     no tokens, keys or webhook URLs in the code
  style     the core's rules: no hex colours in styles, no hardcoded IPs / tailnet names / CT ids, no native
            confirm()/alert(), files under 1 MB
  lint      (--lint) ruff for Python, ESLint + eslint-plugin-vue for web/ (config from main, never the PR's)
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import addon_scan  # noqa: E402

ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,30}$")
VER_RE = re.compile(r"^\d+\.\d+\.\d+$")
CODE_EXT = {".py", ".sh", ".ts", ".js", ".mjs", ".vue"}
COMMENT = re.compile(r"^\s*(#|//|/?\*|<!--)")

LEAKS = [
    ("github-token", r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{40,}"),
    ("tailscale-key", r"\btskey-(?:auth|api|client)-[A-Za-z0-9-]{10,}"),
    ("aws-key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("discord-webhook", r"discord(?:app)?\.com/api/webhooks/\d+/[\w-]{20,}"),
    ("api-key", r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}"),
    ("slack-token", r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),
]
LEAKS = [(r, re.compile(x)) for r, x in LEAKS]
PRIV_IP = re.compile(r"(?<![\d.])(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01])|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7]))\.\d{1,3}\.\d{1,3}(?![\d.])")
TAILNET = re.compile(r"\b[a-z0-9-]+\.ts\.net\b")
CT_ID = re.compile(r"\bpct\s+(?:exec|push|pull|enter|start|stop|reboot|config)\s+\d{3,}|\bct\s*\(\s*\d{3,}|\bvmid\s*[=:]\s*\d{3,}")
PEM = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----\s*\n[A-Za-z0-9+/=]{40,}")
# black/white (masks, text on solid colours) and a fallback inside var(--token, #hex) are fine
HEX_OK = re.compile(r"var\(--[\w-]+,\s*#[0-9a-fA-F]{3,8}\)|#(?:000|fff|000000|ffffff)\b", re.I)
HEX = re.compile(r"(?<![\w&])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
DIALOG = re.compile(r"(?<![\w.$])(?:window\.)?(?:confirm|alert|prompt)\s*\(")
MAX_FILE = 1_000_000
MAX_TOTAL = 10_000_000
REQUIRED = ("id", "name", "version", "author", "desc")


class Report:
    def __init__(self):
        self.items = []

    def add(self, check, level, msg, file=None, line=None):
        self.items.append({"check": check, "level": level, "msg": msg, "file": file, "line": line})

    @property
    def ok(self):
        return not any(i["level"] == "block" for i in self.items)

    def markdown(self, aid, version, ran):
        blocks = [i for i in self.items if i["level"] == "block"]
        warns = [i for i in self.items if i["level"] == "warn"]
        head = (f"### ✅ {aid} {version} passed — merging" if self.ok
                else f"### ❌ {aid} {version}: {len(blocks)} problem{'s' if len(blocks) != 1 else ''} — not merged")
        out = ["<!-- pvedash-check -->", head, "", "| check | result |", "|---|---|"]
        for c in ran:
            mine = [i for i in self.items if i["check"] == c]
            b = sum(i["level"] == "block" for i in mine)
            w = sum(i["level"] == "warn" for i in mine)
            out.append(f"| {c} | {'❌ ' + str(b) if b else '✅'}{f' · ⚠️ {w}' if w else ''} |")
        for title, rows in (("Problems (fix these, then Publish again)", blocks), ("Warnings", warns)):
            if rows:
                out += ["", f"**{title}**", ""]
                for i in rows[:60]:
                    where = f"`{i['file']}{':' + str(i['line']) if i['line'] else ''}` " if i["file"] else ""
                    out.append(f"- **{i['check']}** {where}{i['msg']}")
                if len(rows) > 60:
                    out.append(f"- … and {len(rows) - 60} more")
        return "\n".join(out) + "\n"


def manifest(d: Path):
    import yaml
    try:
        return yaml.safe_load((d / "addon.yaml").read_text()) or {}
    except Exception as e:
        return {"__error__": str(e)}


def ver(v):
    return tuple(int(x) for x in str(v).split(".")) if VER_RE.match(str(v or "")) else None


def texts(root: Path):
    for p in addon_scan.files(root):
        if p.is_file() and not p.is_symlink() and p.suffix in addon_scan.TEXT_EXT:
            try:
                yield p, p.read_text(errors="replace")
            except OSError:
                continue


def check_scope(rep, aid, files):
    for f in files:
        f = f.strip()
        if f and not f.startswith(f"{aid}/"):
            rep.add("scope", "block", f"outside {aid}/: a publish may only change its own folder", f)


def check_manifest(rep, aid, new, old):
    if "__error__" in new:
        rep.add("manifest", "block", f"addon.yaml is not valid YAML: {new['__error__'][:200]}", f"{aid}/addon.yaml")
        return
    for k in REQUIRED:
        if not str(new.get(k) or "").strip():
            rep.add("manifest", "block", f"addon.yaml needs `{k}`", f"{aid}/addon.yaml")
    if new.get("id") != aid:
        rep.add("manifest", "block", f"addon.yaml id is {new.get('id')!r}, the folder is {aid!r}", f"{aid}/addon.yaml")
    if not ver(new.get("version")):
        rep.add("manifest", "block", "version must be x.y.z", f"{aid}/addon.yaml")
    elif old and ver(old.get("version")) and ver(new["version"]) <= ver(old["version"]):
        rep.add("manifest", "block", f"version {new['version']} is not higher than main's {old['version']}", f"{aid}/addon.yaml")
    if len(str(new.get("desc") or "")) > 300:
        rep.add("manifest", "warn", "desc is over 300 characters; one or two lines read best on the card", f"{aid}/addon.yaml")
    for r in new.get("routes") or []:
        if not str(r).startswith("/"):
            rep.add("manifest", "block", f"route {r!r} must start with /", f"{aid}/addon.yaml")
    for d in new.get("depends_on") or []:
        if not ID_RE.match(str(d)):
            rep.add("manifest", "block", f"depends_on {d!r} is not an add-on id", f"{aid}/addon.yaml")


def check_owner(rep, aid, new, old, author, admin):
    if not author:
        return
    if old and str(old.get("author")) != author and not admin:
        rep.add("owner", "block", f"{aid} belongs to {old.get('author')}; only they or an org admin can publish it")
    if not old and str(new.get("author")) != author:
        rep.add("owner", "block", f"a new add-on's author must be its publisher ({author}), not {new.get('author')!r}",
                f"{aid}/addon.yaml")


def check_safety(rep, d: Path, aid, old_dir, ci=False):
    s = addon_scan.scan(d, old_dir if old_dir and old_dir.is_dir() else None, aid, [])
    for f in s["findings"]:
        if f["level"] in ("block", "warn"):
            rep.add("safety", f["level"], f"{f['rule']}: {f['why']}", f"{aid}/{f['file']}" if f.get("file") else None, f.get("line"))
    if ci and s.get("clamav") != "clean":  # hits are findings already; on GitHub it must also have run
        rep.add("safety", "block", f"ClamAV: {s.get('clamav')}")
    return s


def check_text(rep, d: Path, aid):
    total = 0
    for p, t in texts(d):
        rel = f"{aid}/{p.relative_to(d)}"
        size = p.stat().st_size
        total += size
        if size > MAX_FILE:
            rep.add("style", "block", f"{size // 1000} kB: keep files under 1 MB (data belongs in the add-on's CT)", rel)
        in_style = p.suffix == ".css"
        if PEM.search(t):
            rep.add("leaks", "block", "a private key in the code; it belongs in `settings:` (secret: true)", rel)
        for n, line in enumerate(t.splitlines(), 1):
            for rule, rx in LEAKS:
                if rx.search(line):
                    rep.add("leaks", "block", f"{rule}: a real secret in the code; it belongs in `settings:` (secret: true)", rel, n)
            if p.suffix == ".vue":
                if re.match(r"\s*<style\b", line):
                    in_style = True
                elif re.match(r"\s*</style>", line):
                    in_style = False
            if p.suffix not in CODE_EXT and p.suffix != ".css":
                continue
            if COMMENT.match(line):
                continue
            if PRIV_IP.search(line):
                rep.add("style", "block", "hardcoded private IP: use ip()/ctIp() from config.json", rel, n)
            if TAILNET.search(line):
                rep.add("style", "block", "hardcoded tailnet name: use tsUrl()/TAILNET", rel, n)
            if CT_ID.search(line):
                rep.add("style", "block", "hardcoded CT id: use ct()/ctId() with a `cts` key", rel, n)
            if HEX.search(HEX_OK.sub("", line)) and p.suffix in (".vue", ".css"):
                if in_style or "style=" in line:
                    rep.add("style", "block", "hex colour: use the core's tokens (var(--accent), var(--ok), …)", rel, n)
                elif p.suffix == ".vue":
                    rep.add("style", "warn", "hex colour in script/template (fine for chart palettes only)", rel, n)
            if p.suffix == ".vue" and DIALOG.search(line):
                rep.add("style", "block", "native confirm()/alert()/prompt(): use an inline confirm (`.sure` + useArm)", rel, n)
    for p in d.rglob("*"):
        if p.is_file() and p.suffix not in addon_scan.TEXT_EXT and not any(x in addon_scan.SKIP_DIRS for x in p.parts):
            total += p.stat().st_size
    if total > MAX_TOTAL:
        rep.add("style", "block", f"{total // 1_000_000} MB in total: keep an add-on under 10 MB")


def check_python(rep, d: Path, aid):
    for p in d.rglob("*.py"):
        if any(x in addon_scan.SKIP_DIRS for x in p.parts):
            continue
        try:
            compile(p.read_text(errors="replace"), str(p), "exec")
        except SyntaxError as e:
            rep.add("lint", "block", f"Python syntax error: {e.msg}", f"{aid}/{p.relative_to(d)}", e.lineno)


def run_lint(rep, d: Path, aid):
    py = [str(p) for p in d.rglob("*.py") if not any(x in addon_scan.SKIP_DIRS for x in p.parts)]
    if py:
        r = subprocess.run(["ruff", "check", "--isolated", "--output-format", "json", "--select", "E9,F,B006,B008,B012",
                            "--ignore", "F403,F405", *py], capture_output=True, text=True, timeout=300)
        try:
            if r.returncode not in (0, 1):
                raise ValueError(f"exit {r.returncode}")
            for f in json.loads(r.stdout):
                rel = f"{aid}/{Path(f['filename']).resolve().relative_to(d.resolve())}"
                rep.add("lint", "block", f"{f['code']} {f['message']}", rel, (f.get("location") or {}).get("row"))
        except (ValueError, KeyError) as e:
            rep.add("lint", "block", f"ruff did not run ({e}): {r.stderr.strip()[:200]}")
    web = d / "web"
    if web.is_dir():
        # with -c, ESLint's base path is the cwd: run from the add-on, with main's tools and config
        r = subprocess.run([str(HERE / "node_modules/.bin/eslint"), "-c", str(HERE / "eslint.config.mjs"), "--format", "json",
                            "--no-warn-ignored", "web"], capture_output=True, text=True, timeout=600, cwd=d)
        try:
            if r.returncode not in (0, 1):  # 2 = ESLint itself failed: no answer is not a pass
                raise ValueError(f"exit {r.returncode}")
            for f in json.loads(r.stdout):
                rel = f"{aid}/{Path(f['filePath']).resolve().relative_to(d.resolve())}"
                for m in f["messages"]:
                    rep.add("lint", "block" if m["severity"] == 2 else "warn", f"{m.get('ruleId') or 'parse'}: {m['message']}", rel, m.get("line"))
        except (ValueError, KeyError) as e:
            rep.add("lint", "block", f"ESLint did not run ({e}): {r.stderr.strip()[:300]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--pr", required=True, type=Path)
    ap.add_argument("--base", type=Path)
    ap.add_argument("--files", type=Path)
    ap.add_argument("--author", default="")
    ap.add_argument("--admin", action="store_true")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--report", type=Path)
    a = ap.parse_args()
    aid = a.id
    rep = Report()
    ran = []
    if not ID_RE.match(aid):
        rep.add("scope", "block", f"bad add-on id {aid!r}")
    d = a.pr / aid
    if not (d / "addon.yaml").exists():
        rep.add("manifest", "block", f"{aid}/addon.yaml is missing")
        new = {}
    else:
        new = manifest(d)
    old_dir = a.base / aid if a.base else None
    old = manifest(old_dir) if old_dir and (old_dir / "addon.yaml").exists() else None
    if a.files:
        ran.append("scope")
        check_scope(rep, aid, a.files.read_text().splitlines())
    ran += ["manifest", "owner", "safety", "leaks", "style", "lint"]
    if new:
        check_manifest(rep, aid, new, old)
        check_owner(rep, aid, new, old, a.author, a.admin)
        check_safety(rep, d, aid, old_dir, ci=a.lint)
        check_text(rep, d, aid)
        check_python(rep, d, aid)
        if a.lint:
            run_lint(rep, d, aid)
    md = rep.markdown(aid, new.get("version", "?"), ran)
    if a.report:
        a.report.write_text(md)
    print(md)
    sys.exit(0 if rep.ok else 1)


if __name__ == "__main__":
    main()
