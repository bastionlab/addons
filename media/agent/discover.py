"""Discover tab: film and series suggestions from Seerr (TMDB) and the Jellyfin watch history, minus anything the
library has or ever had. Reads the Seerr/Jellyfin keys out of CT 106's Seerr settings; they stay on the host."""
import json, re
from pathlib import Path
from urllib.parse import urlencode

import threading, time

from dash_sdk import FAN, action, cached, ct, get, http_json, ip, on_start, post, sh
import media

POSTER = "https://image.tmdb.org/t/p/w342"
SEEDS = 6      # recently watched titles that recommendations are asked for
PER_SECTION = 24
KEEP = 40      # cached per section per depth, so hiding "seen" titles still leaves a full row
MAX_DEPTH = 5  # "Load more" fetches deeper TMDB pages, up to this many rounds
SEEN_FILE = Path("/var/lib/dash-media/seen.json")
WATCH_FILE = Path("/var/lib/dash-media/seen-watch.json")  # "series:123" -> {title, seasons, episodes} at the time of the last check
WATCH_EVERY = 6 * 3600
_watch_lock = threading.Lock()
REQUEST = str(Path(__file__).resolve().parent / "media-request")


@cached(1800)
def seerr_settings():
    return json.loads(sh("pct", "exec", str(ct("dl")), "--", "cat", "/opt/media/seerr/settings.json", timeout=15))


def seerr(path, **query):
    key = seerr_settings()["main"]["apiKey"]
    url = f"http://{ip('dl')}:5055/api/v1{path}" + ("?" + urlencode(query) if query else "")
    return http_json(url, {"X-Api-Key": key}, timeout=25) or {}


def jellyfin(path, **query):
    j = seerr_settings()["jellyfin"]
    url = f"http://{j['ip']}:{j['port']}{j.get('urlBase') or ''}{path}" + ("?" + urlencode(query) if query else "")
    return http_json(url, {"Authorization": f'MediaBrowser Token="{j["apiKey"]}"'}, timeout=25) or {}


def _safe(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception:
        return {}


# --- what the household already has or had -----------------------------------------------------------
@cached(1800)
def known():
    """tmdb ids of films / series to hide: in or once in Radarr/Sonarr, on their exclusion lists, watched"""
    movies, series = set(), set()
    movies |= {m["tmdbId"] for m in _safe(media.arr, "radarr", "movie") or [] if m.get("tmdbId")}
    movies |= {e["tmdbId"] for e in _safe(media.arr, "radarr", "exclusions") or [] if e.get("tmdbId")}
    tvdb = {}
    for s in _safe(media.arr, "sonarr", "series") or []:
        if s.get("tmdbId"):
            series.add(s["tmdbId"])
        elif s.get("tvdbId"):
            tvdb[s["tvdbId"]] = 1
    # Sonarr's exclusions only carry tvdb ids: resolve them to tmdb through Sonarr's own lookup
    for e in _safe(media.arr, "sonarr", "importlistexclusion") or []:
        tvdb[e.get("tvdbId")] = 1
    for t in list(tvdb):
        hit = (_safe(media.arr, "sonarr", "series/lookup", term=f"tvdb:{t}") or [None])[0]
        if hit and hit.get("tmdbId"):
            series.add(hit["tmdbId"])
    return movies, series


@cached(900)
def watched():
    """-> (played tmdb ids {"movie": set, "series": set}, last distinct titles [(kind, tmdbId, title)])"""
    seen = {"movie": set(), "series": set()}
    recent = []
    for u in _safe(jellyfin, "/Users") or []:
        r = _safe(jellyfin, f"/Users/{u['Id']}/Items", Recursive="true", IncludeItemTypes="Movie,Episode",
                  Filters="IsPlayed", SortBy="DatePlayed", SortOrder="Descending", Limit=400, Fields="ProviderIds")
        items = r.get("Items") or []
        sids = sorted({i["SeriesId"] for i in items if i.get("SeriesId")})
        sers = {}
        for k in range(0, len(sids), 50):
            for s in _safe(jellyfin, "/Items", Ids=",".join(sids[k:k + 50]), Fields="ProviderIds").get("Items") or []:
                sers[s["Id"]] = s
        for i in items:
            if i.get("Type") == "Episode":
                s = sers.get(i.get("SeriesId")) or {}
                kind, tid, title = "series", (s.get("ProviderIds") or {}).get("Tmdb"), s.get("Name")
            else:
                kind, tid, title = "movie", (i.get("ProviderIds") or {}).get("Tmdb"), i.get("Name")
            if not (tid and str(tid).isdigit()):
                continue
            tid = int(tid)
            seen[kind].add(tid)
            if len(recent) < SEEDS and all((k, t) != (kind, tid) for k, t, _ in recent):
                recent.append((kind, tid, title))
    return seen, recent


# --- candidates ----------------------------------------------------------------------------------
def card(r, because=None):
    kind = "series" if r.get("mediaType") == "tv" else "movie"
    if r.get("mediaType") not in ("movie", "tv") or not r.get("id") or not r.get("posterPath"):
        return None
    date = r.get("releaseDate") or r.get("firstAirDate") or ""
    return {"kind": kind, "tmdbId": r["id"], "title": r.get("title") or r.get("name"),
            "year": int(date[:4]) if date[:4].isdigit() else None,
            "rating": round(r.get("voteAverage") or 0, 1), "votes": r.get("voteCount") or 0,
            "overview": (r.get("overview") or "")[:240], "poster": POSTER + r["posterPath"],
            "because": because, "_known": bool(r.get("mediaInfo"))}


def fetch(path, **q):
    return [r for r in (_safe(seerr, path, **q).get("results") or [])]


def hidden(c, seen):
    movies, series = known()
    return (c["_known"] or c["tmdbId"] in (movies if c["kind"] == "movie" else series)
            or c["tmdbId"] in seen[c["kind"]])


def finish(cards, seen, taken, keep=KEEP):
    out = []
    for c in cards:
        key = (c["kind"], c["tmdbId"])
        if key in taken or hidden(c, seen):
            continue
        taken.add(key)
        out.append({k: v for k, v in c.items() if not k.startswith("_") and k != "votes"})
        if len(out) >= keep:
            break
    return out


def interleave(*lists):
    out = []
    for i in range(max(map(len, lists), default=0)):
        out += [l[i] for l in lists if i < len(l)]
    return out


@cached(1800)
def discover(depth=1):
    seen, recent = watched()
    movies, series = known()  # warm before the fan-out
    jobs = {
        "trend": [FAN.submit(fetch, "/discover/trending", page=p) for p in range(1, 3 * depth + 1)],
        "top_m": [FAN.submit(fetch, "/discover/movies", sortBy="vote_average.desc", voteCountGte=3000, page=p) for p in range(1, 3 * depth + 1)],
        "top_t": [FAN.submit(fetch, "/discover/tv", sortBy="vote_average.desc", voteCountGte=1500, page=p) for p in range(1, 3 * depth + 1)],
        "pop_m": [FAN.submit(fetch, "/discover/movies", page=p) for p in range(1, 2 * depth + 1)],
        "pop_t": [FAN.submit(fetch, "/discover/tv", page=p) for p in range(1, 2 * depth + 1)],
    }
    seeds = [(title, FAN.submit(fetch, f"/{'tv' if kind == 'series' else 'movie'}/{tid}/recommendations"))
             for kind, tid, title in recent]
    flat = lambda fs: [card(r) for f in fs for r in f.result()]
    # because you watched: more seeds recommending a title first, then its vote
    agg = {}
    for title, f in seeds:
        for r in f.result():
            c = card(r, title)
            if not c:
                continue
            a = agg.setdefault((c["kind"], c["tmdbId"]), {"c": c, "n": 0, "from": []})
            a["n"] += 1
            a["from"].append(title)
    ranked = sorted(agg.values(), key=lambda a: (-a["n"], -a["c"]["rating"]))
    because = []
    for a in ranked:
        a["c"]["because"] = a["from"][0]
        because.append(a["c"])
    taken = set()
    trending = [c for c in flat(jobs["trend"]) if c]
    top = sorted([c for c in flat(jobs["top_m"]) + flat(jobs["top_t"]) + flat(jobs["pop_m"]) + flat(jobs["pop_t"])
                  if c and c["votes"] >= 500], key=lambda c: -c["rating"])
    # a title the household has seen can't be a recommendation seed's own suggestion either
    secs = [("because", "Because you watched", finish(because, seen, taken, KEEP * depth)),
            ("trending", "Trending now", finish(trending, seen, taken, KEEP * depth)),
            ("top", "Popular and top rated", finish(top, seen, taken, KEEP * depth))]
    return {"sections": [{"key": k, "title": t, "items": i} for k, t, i in secs]}


def seen_marked():
    """titles the owner marked as already seen: ["movie:123", "series:456"]"""
    try:
        return set(json.loads(SEEN_FILE.read_text()))
    except (OSError, ValueError):
        return set()


@get("/media/discover", quiet=True)
def discover_route(q):
    gone = seen_marked()
    depth = min(max(int(q.get("depth") or 1), 1), MAX_DEPTH) if str(q.get("depth") or "1").isdigit() else 1
    return {"depth": depth, "maxDepth": MAX_DEPTH,
            "sections": [{**s, "items": [i for i in s["items"] if f"{i['kind']}:{i['tmdbId']}" not in gone][:PER_SECTION * depth]}
                         for s in discover(depth)["sections"]]}


@get("/media/discover/seasons", quiet=True)
def seasons_route(q):
    tid = str(q.get("tmdbId", ""))
    if not tid.isdigit():
        raise ValueError("tmdbId must be a number")
    info = _safe(seerr, f"/tv/{tid}")
    have = {x.get("seasonNumber"): x.get("status") for x in (info.get("mediaInfo") or {}).get("seasons") or []}
    return {"seasons": [{"n": x["seasonNumber"], "episodes": x.get("episodeCount") or 0, "known": have.get(x["seasonNumber"], 1) > 1}
                        for x in info.get("seasons") or [] if x.get("seasonNumber")]}


@post("/media/discover/seen")
def seen_route(body):
    kind, tid = str(body.get("kind", "")), str(body.get("tmdbId", ""))
    if kind not in ("movie", "series") or not tid.isdigit():
        raise ValueError("kind must be movie or series and tmdbId a number")
    marks = seen_marked() | {f"{kind}:{tid}"}
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(sorted(marks)))
    if kind == "series":  # "Seen it" watches for new seasons/episodes; Dismiss records an ignore so the legacy baseline skips it
        if body.get("dismiss"):
            with _watch_lock:
                w = _watch_load()
                w[f"series:{tid}"] = {"ignore": True}
                _watch_save(w)
        else:
            threading.Thread(target=watch_add, args=(int(tid),), daemon=True).start()
    return {"ok": True}


# --- "Seen it" series: tell the owner when they gain seasons or episodes ----------------------------------
def _counts(tid):
    info = _safe(seerr, f"/tv/{tid}")
    seas = [x for x in info.get("seasons") or [] if (x.get("seasonNumber") or 0) >= 1]
    if not info.get("id") or not seas:
        return None
    return {"title": info.get("name") or f"TMDB {tid}", "seasons": len(seas), "episodes": sum(x.get("episodeCount") or 0 for x in seas)}


def _watch_load():
    try:
        return json.loads(WATCH_FILE.read_text())
    except (OSError, ValueError):
        return {}


def _watch_save(w):
    WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_FILE.write_text(json.dumps(w))


def watch_add(tid):
    c = _counts(tid)
    if c:
        with _watch_lock:
            w = _watch_load()
            w[f"series:{tid}"] = c
            _watch_save(w)


def watch_check(notify=None):
    """compare every watched series with TMDB; returns the messages sent. Series marked seen before this existed
    (in seen.json without a baseline) get their baseline silently on the first run."""
    if notify is None:
        import push
        notify = lambda title, body: push.notify("media", title, body, url="/media?s=discover")
    out = []
    with _watch_lock:
        w = _watch_load()
    for mark in sorted(seen_marked()):
        if mark.startswith("series:") and mark not in w:
            c = _counts(mark.split(":")[1])
            if c:
                w[mark] = c
    for mark, old in list(w.items()):
        if old.get("ignore"):
            continue
        c = _counts(mark.split(":")[1])
        if not c:
            continue
        if c["seasons"] > old["seasons"]:
            n = c["seasons"] - old["seasons"]
            out.append((f"New season: {c['title']}", f"{n} new season{'s' if n > 1 else ''} announced, now {c['seasons']} in total."))
        elif c["episodes"] > old["episodes"]:
            n = c["episodes"] - old["episodes"]
            out.append((f"New episodes: {c['title']}", f"{n} new episode{'s' if n > 1 else ''}, now {c['episodes']} in total."))
        w[mark] = c
    with _watch_lock:
        _watch_save({**_watch_load(), **w})
    for title, body in out:
        notify(title, body)
    return out


@on_start
def watcher():
    def loop():
        time.sleep(120)
        while True:
            try:
                watch_check()
            except Exception:
                pass
            time.sleep(WATCH_EVERY)
    threading.Thread(target=loop, daemon=True).start()


@action("media_request")
def a_media_request(args):
    """Asks Seerr for a film or a whole series; Seerr hands it to Radarr/Sonarr, which download it."""
    kind, tid = str(args.get("kind", "")), str(args.get("tmdbId", ""))
    if kind not in ("movie", "series") or not tid.isdigit():
        raise ValueError("kind must be movie or series and tmdbId a number")
    seasons = args.get("seasons")
    if seasons in (None, "", "all", []):
        seasons = None
    else:
        try:
            seasons = sorted({int(x) for x in (seasons.split(",") if isinstance(seasons, str) else seasons)})
        except (TypeError, ValueError):
            raise ValueError("seasons must be numbers")
        if kind != "series" or not seasons or min(seasons) < 1:
            raise ValueError("seasons only apply to a series and start at 1")
    info = _safe(seerr, f"/{'tv' if kind == 'series' else 'movie'}/{tid}")
    title = info.get("title") or info.get("name") or f"TMDB {tid}"
    date = info.get("releaseDate") or info.get("firstAirDate") or ""
    what = title + (f" ({date[:4]})" if date[:4].isdigit() else "")
    which = f"season {', '.join(map(str, seasons))}" if seasons else "all seasons"
    desc = (f"Request the series {what} ({which}) in Seerr; it is then downloaded" if kind == "series"
            else f"Request the film {what} in Seerr; it is then downloaded")
    return desc, ["python3", REQUEST, kind, tid, *([",".join(map(str, seasons))] if seasons else [])], 60
