#!/usr/bin/env python3
"""check_design.py — the gate a design passes before it joins the catalogue (`_designs/<slug>.json`).

  check_design.py --slug <slug> --pr <PR checkout> [--base <main checkout>] [--files <changed list>]
                  [--author <login>] [--admin] [--report <out.md>]                 exit 0 = merge, 1 = not

Run by .github/workflows/publish.yml on every `design/<slug>` pull request and by the Designs add-on's
design-publish before it pushes. A design is data the app paints into other people's browsers, so it may hold
nothing but a name and the known colour tokens as #rrggbb, a corner radius and light/dark.

  scope   the PR changes `_designs/<slug>.json` only
  design  valid JSON, slug = file name, only known keys, strict values, under 4 kB
  owner   an existing design is updated by its author (or an org admin); a new one carries its publisher
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import Report  # noqa: E402

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,59}$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
COLORS = {"bg", "panel", "panel-2", "line", "line-2", "text", "muted", "faint", "accent", "ok", "warn", "bad", "track",
          "claude", "term-bg", "term-fg"}
KEYS = {"slug", "name", "author", "tokens", "updated"}
NAME_BAD = re.compile(r"[<>\x00-\x1f\x7f]")


def load(f: Path):
    try:
        return json.loads(f.read_text())
    except Exception as e:
        return {"__error__": str(e)}


def check_design(rep, slug, d, rel):
    if "__error__" in d:
        rep.add("design", "block", f"not valid JSON: {d['__error__'][:200]}", rel)
        return
    if not isinstance(d, dict):
        rep.add("design", "block", "must be a JSON object", rel)
        return
    for k in set(d) - KEYS:
        rep.add("design", "block", f"unknown key `{k}`", rel)
    if d.get("slug") != slug:
        rep.add("design", "block", f"slug is {d.get('slug')!r}, the file is {slug!r}", rel)
    name = d.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 40 or NAME_BAD.search(name):
        rep.add("design", "block", "name: 1–40 characters, no < > or control characters", rel)
    if not isinstance(d.get("author"), str) or not d["author"]:
        rep.add("design", "block", "needs `author`", rel)
    if "updated" in d and not isinstance(d["updated"], int):
        rep.add("design", "block", "`updated` must be a unix time", rel)
    t = d.get("tokens")
    if not isinstance(t, dict):
        rep.add("design", "block", "needs `tokens`", rel)
        return
    for k, v in t.items():
        if k in COLORS:
            if not isinstance(v, str) or not HEX.match(v):
                rep.add("design", "block", f"`{k}` must be a #rrggbb colour", rel)
        elif k == "radius":
            if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 24:
                rep.add("design", "block", "`radius` must be a whole number 0–24", rel)
        elif k == "scheme":
            if v not in ("dark", "light"):
                rep.add("design", "block", "`scheme` must be dark or light", rel)
        else:
            rep.add("design", "block", f"unknown token `{k}`", rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--pr", required=True, type=Path)
    ap.add_argument("--base", type=Path)
    ap.add_argument("--files", type=Path)
    ap.add_argument("--author", default="")
    ap.add_argument("--admin", action="store_true")
    ap.add_argument("--report", type=Path)
    a = ap.parse_args()
    rep, slug = Report(), a.slug
    rel = f"_designs/{slug}.json"
    ran = ["scope", "design", "owner"]
    d = {}
    if not SLUG_RE.match(slug):
        rep.add("scope", "block", f"bad design slug {slug!r}")
    else:
        if a.files:
            for f in a.files.read_text().splitlines():
                if f.strip() and f.strip() != rel:
                    rep.add("scope", "block", f"outside {rel}: a design publish may only change its own file", f.strip())
        f = a.pr / rel
        if not f.is_file() or f.is_symlink():
            rep.add("design", "block", f"{rel} is missing")
        elif f.stat().st_size > 4000:
            rep.add("design", "block", "over 4 kB: a design is a handful of colours", rel)
        else:
            d = load(f)
            check_design(rep, slug, d, rel)
        old_f = a.base / rel if a.base else None
        old = load(old_f) if old_f and old_f.is_file() else None
        if a.author and isinstance(d, dict):
            if old and old.get("author") != a.author and not a.admin:
                rep.add("owner", "block", f"{slug} belongs to {old.get('author')}; only they or an org admin can update it")
            if not old and d.get("author") != a.author:
                rep.add("owner", "block", f"a new design's author must be its publisher ({a.author}), not {d.get('author')!r}", rel)
    md = rep.markdown(f"design {slug}", "", ran)
    if a.report:
        a.report.write_text(md)
    print(md)
    sys.exit(0 if rep.ok else 1)


if __name__ == "__main__":
    main()
