"""Trending repos add-on on the host: the only part that needs the GitHub token. Scrapes github.com/trending,
fetches READMEs and stars/unstars. Summaries, scores and the list live
in the app (web/server/utils/trending.ts)."""
import base64, html, json, re, urllib.error, urllib.parse, urllib.request

from dash_sdk import GH_TOKEN_FILE, get, post

UA = {"User-Agent": "bastion-trending", "Accept-Language": "en"}
REPO = re.compile(r"[\w.-]{1,100}/[\w.-]{1,100}")
ROW = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)


def _token():
    try:
        return GH_TOKEN_FILE.read_text().strip()
    except OSError:
        return ""


def _api(path, method="GET", timeout=15):
    h = {**UA, "Accept": "application/vnd.github+json"}
    if _token():
        h["Authorization"] = "Bearer " + _token()
    req = urllib.request.Request("https://api.github.com" + path, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
    return json.loads(body) if body else {}


def _num(s):
    s = re.sub(r"[^\d]", "", s or "")
    return int(s) if s else 0


def _scrape(since, lang=""):
    url = "https://github.com/trending" + ("/" + urllib.parse.quote(lang) if lang else "") + "?since=" + since
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        page = r.read().decode("utf-8", "replace")
    out = []
    for row in ROW.findall(page):
        m = re.search(r'<h2[^>]*>.*?href="/([^"/]+/[^"/]+)"', row, re.S)
        if not m or not REPO.fullmatch(m.group(1)):
            continue
        d = re.search(r'<p class="col-9[^"]*"[^>]*>(.*?)</p>', row, re.S)
        lg = re.search(r'itemprop="programmingLanguage">([^<]+)<', row)
        st = re.search(r'href="/[^"]+/stargazers"[^>]*>(.*?)</a>', row, re.S)
        today = re.search(r"([\d,]+)\s+stars?\s+(?:today|this week|this month)", row)
        out.append({
            "repo": m.group(1), "desc": html.unescape(re.sub(r"<[^>]+>|\s+", " ", d.group(1))).strip() if d else "",
            "lang": lg.group(1).strip() if lg else "", "stars": _num(re.sub(r"<[^>]+>", "", st.group(1))) if st else 0,
            "gain": _num(today.group(1)) if today else 0, "source": "trending-" + since,
        })
    return out


@get("/trending-repos/candidates")
def candidates(q):
    """what is trending on GitHub today, merged by repo"""
    found, errors = {}, []
    jobs = [lambda: _scrape("daily")]
    for job in jobs:
        try:
            for r in job():
                cur = found.get(r["repo"])
                if cur:
                    cur["sources"].append(r["source"])
                    cur["gain"] = max(cur["gain"], r["gain"])
                    cur["stars"] = max(cur["stars"], r["stars"])
                    cur["desc"] = cur["desc"] or r["desc"]
                else:
                    found[r["repo"]] = {**r, "sources": [r["source"]]}
        except (urllib.error.URLError, OSError, ValueError) as e:
            errors.append(str(e)[:120])
    return {"repos": list(found.values()), "errors": errors}


@get("/trending-repos/readme")
def readme(q):
    repo = q.get("repo", "")
    if not REPO.fullmatch(repo):
        raise ValueError("bad repo")
    meta = {}
    try:
        meta = _api("/repos/" + repo)
        d = _api("/repos/" + repo + "/readme")
        text = base64.b64decode(d.get("content", "")).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise ValueError(f"GitHub {e.code}")
        text = ""
    return {"readme": text[:12000], "topics": meta.get("topics", []), "license": (meta.get("license") or {}).get("spdx_id", ""),
            "pushed": meta.get("pushed_at", ""), "stars": meta.get("stargazers_count", 0), "lang": meta.get("language") or ""}


@post("/trending-repos/star")
def star(body):
    repo = str(body.get("repo", ""))
    if not REPO.fullmatch(repo):
        raise ValueError("bad repo")
    if not _token():
        raise ValueError("no GitHub token set (Settings → Connections)")
    try:
        _api("/user/starred/" + repo, "PUT" if body.get("on", True) else "DELETE")
    except urllib.error.HTTPError as e:
        raise ValueError("GitHub refused: the token needs permission to star" if e.code in (401, 403) else f"GitHub {e.code}")
    return {"ok": True}
