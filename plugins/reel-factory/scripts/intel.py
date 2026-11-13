"""Source intelligence: discover and read where AI/tech news actually originates and gets attention.

usage (every command prints JSON items; add --prod P to append them to P/research/sources.json, deduped):
  rf intel news "<query>" [--days 7]            Google News RSS search across hundreds of publishers
  rf intel feeds "<keywords>" [--tier press|official|all] [--days 7]   registry publication + company newsroom feeds
  rf intel x <post-url-or-id> [...]              an X post via X's official oEmbed + public embed data: text, author,
                                                 verified, date, likes, replies (discovery: search engines + handles)
  rf intel handles [org|topic]                   registry of official/founder/researcher X handles to check
  rf intel reddit "<query>" [--subs a,b] [--days 7]  Reddit: OAuth API (scores, comments) when REDDIT_CLIENT_ID/
                                                 REDDIT_CLIENT_SECRET are set, else subreddit RSS (no scores)
  rf intel github "<query>" [--days 30] [--active]  NEW repos created in the window, by stars (--active: established, pushed)
  rf intel repo <owner/name>                     stars, star velocity, forks, releases, contributors, 30-day commits
  rf intel hn "<query>" [--days 14]              Hacker News stories with points and comments
  rf intel papers "<query>"                      arXiv + Hugging Face daily papers (upvotes)
  rf intel read <url>                            full article text + metadata (trafilatura); on 403/paywall prints the
                                                 capture ladder instead of guessing
  rf intel score --prod P                        score and rank the ledger (credibility, originality, recency,
                                                 engagement, corroboration) and print diversity warnings

Official, supported access only: public RSS, official APIs (GitHub, arXiv, HN Algolia, Reddit OAuth), X's official
oEmbed/embed endpoints. Never log in, never bypass paywalls or bot walls. Popularity ranks discovery; it never
replaces verification.
"""
import argparse, datetime as dt, email.utils, html, json, math, os, re, subprocess, sys, time
import urllib.parse as up
from defusedxml.ElementTree import fromstring as xml_parse  # remote XML: no XXE / entity expansion
from pathlib import Path
import requests
from common import HOME, PLUGIN, load_json, save_json

UA = {"User-Agent": "reel-factory/2.0 research (+https://github.com/Mihirkothari04/reel-factory)"}
REG = PLUGIN / "skills/reel-factory/references/sources.json"
NOW = dt.datetime.now(dt.timezone.utc)


def env(k):
    if os.environ.get(k):
        return os.environ[k]
    f = HOME / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def get(url, **kw):
    for i in range(3):
        r = requests.get(url, headers={**UA, **kw.pop("headers", {})}, timeout=30, **kw)
        if r.status_code != 429:
            return r
        time.sleep(2 * (i + 1))
    return r


def iso(s):
    if not s:
        return None
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(dt.timezone.utc).isoformat()
    except Exception:
        try:
            return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc).isoformat()
        except Exception:
            return s


def age_days(ts):
    try:
        return (NOW - dt.datetime.fromisoformat(ts)).total_seconds() / 86400
    except Exception:
        return None


def registry():
    return json.loads(REG.read_text(encoding="utf-8"))


def publisher_info(domain_or_name):
    reg = registry()
    key = (domain_or_name or "").lower()
    for p in reg["publishers"]:
        if key and (key in [d.lower() for d in p["domains"]] or key == p["name"].lower() or any(key.endswith("." + d.lower()) or key == d.lower() for d in p["domains"])):
            return p
    return None


def item(platform, url, title="", text="", publisher=None, author=None, published_at=None, engagement=None, is_original=False, extra=None):
    dom = up.urlparse(url).netloc.lower().removeprefix("www.")
    # the publisher decides credibility, not the link host (Google News links point at news.google.com)
    pi = publisher_info(publisher or "") or publisher_info((extra or {}).get("publisher_domain") or "") or (None if dom == "news.google.com" else publisher_info(dom))
    d = {"platform": platform, "url": url, "title": html.unescape(title or "").strip(), "text": (text or "").strip()[:1200],
         "publisher": publisher or (pi or {}).get("name") or dom, "author": author, "published_at": iso(published_at),
         "engagement": engagement or {}, "is_original": is_original, "tier": (pi or {}).get("tier", "unknown"),
         "onscreen_ok": (pi or {}).get("onscreen_ok", True), "retrieved_at": NOW.isoformat()}
    if extra:
        d.update(extra)
    return d


def rss(url, days=None, kw=None):
    r = get(url)
    try:
        root = xml_parse(r.content) if r.status_code == 200 and r.content.strip() else None
    except Exception:
        root = None
    if root is None:
        print(f"feed unavailable ({r.status_code}{', rate-limited' if r.status_code == 429 or not r.content.strip() else ''}): {url}", file=sys.stderr)
        return []
    out = []
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        f = {c.tag.split("}")[-1]: c for c in it}
        link = f.get("link")
        href = (link.get("href") if link is not None and link.get("href") else (link.text if link is not None else "")) or ""
        title = f["title"].text if "title" in f and f["title"].text else ""
        date = next((f[k].text for k in ("pubDate", "published", "updated", "date") if k in f and f[k].text), None)
        desc = next((f[k].text for k in ("description", "summary", "content") if k in f and f[k].text), "") or ""
        src = f.get("source")
        auth = f.get("author") or f.get("creator")
        aname = None
        if auth is not None:
            aname = auth.text or next((c.text for c in auth if c.tag.split("}")[-1] == "name"), None)
        out.append({"url": href.strip(), "title": title, "text": re.sub(r"<[^>]+>", " ", html.unescape(desc)), "date": iso(date),
                    "source": src.text if src is not None else None, "source_url": src.get("url") if src is not None else None, "author": aname})
    if days:
        out = [o for o in out if not o["date"] or (age_days(o["date"]) or 0) <= days]
    if kw:
        words = [w.lower() for w in re.findall(r"\w+", kw) if len(w) > 2]
        out = [o for o in out if all(w in (o["title"] + " " + o["text"]).lower() for w in words[:3])]
    return out


# ---------- connectors ----------

def news(q, days=7):
    url = "https://news.google.com/rss/search?" + up.urlencode({"q": f"{q} when:{days}d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
    res = []
    for o in rss(url):
        title = re.sub(r"\s+-\s+[^-]+$", "", o["title"])
        dom = up.urlparse(o.get("source_url") or "").netloc.removeprefix("www.")
        res.append(item("news", o["url"], title, publisher=o.get("source"), published_at=o["date"],
                        extra={"publisher_domain": dom, "note": "Google News link: open it to reach the article; cite the publisher's URL"}))
    return res


def feeds(kw, tier="all", days=7):
    out = []
    for p in registry()["publishers"]:
        if tier != "all" and p["tier"] != tier:
            continue
        for f in p.get("feeds", []):
            try:
                for o in rss(f, days, kw):
                    out.append(item("official" if p["tier"] == "official" else "news", o["url"], o["title"], o["text"], p["name"], o["author"], o["date"],
                                    is_original=p["tier"] == "official"))
            except Exception as e:
                print(f"feed failed {p['name']}: {str(e)[:80]}", file=sys.stderr)
    return out


def x_post(ref):
    pid = re.search(r"(\d{8,})", ref).group(1)
    url = ref if ref.startswith("http") else f"https://x.com/i/status/{pid}"
    o = get("https://publish.twitter.com/oembed?" + up.urlencode({"url": url, "omit_script": 1}))
    oe = o.json() if o.status_code == 200 else {}
    s = get(f"https://cdn.syndication.twimg.com/tweet-result?id={pid}&token=a")
    d = s.json() if s.status_code == 200 and s.text.strip().startswith("{") else {}
    u = d.get("user") or {}
    handle = u.get("screen_name") or (oe.get("author_url", "").rstrip("/").split("/")[-1] or None)
    text = d.get("text") or re.sub(r"<[^>]+>", " ", html.unescape(oe.get("html", "")))
    eng = {k: d[k] for k in ("favorite_count", "conversation_count") if k in d}
    return item("x", f"https://x.com/{handle}/status/{pid}" if handle else url, text[:120], text, publisher=f"@{handle}" if handle else "X",
                author=u.get("name") or oe.get("author_name"), published_at=d.get("created_at"), engagement=eng, is_original=True,
                extra={"verified": bool(u.get("is_blue_verified") or u.get("verified")), "followers_hint": None,
                       "embed_url": f"https://platform.twitter.com/embed/Tweet.html?id={pid}",
                       "registry_handle": next((h for h in registry()["x_handles"] if h["handle"].lower() == (handle or "").lower()), None)})


def handles(q=None):
    hs = registry()["x_handles"]
    if q:
        ql = q.lower()
        hs = [h for h in hs if ql in (h["org"] + " " + h["name"] + " " + " ".join(h.get("topics", []))).lower()]
    return hs


def reddit(q, subs=None, days=7):
    cid, sec = env("REDDIT_CLIENT_ID"), env("REDDIT_CLIENT_SECRET")
    out = []
    if cid and sec:
        tok = requests.post("https://www.reddit.com/api/v1/access_token", auth=(cid, sec), data={"grant_type": "client_credentials"},
                            headers=UA, timeout=30).json().get("access_token")
        H = {"Authorization": f"bearer {tok}", **UA}
        t = "week" if days <= 7 else "month" if days <= 31 else "year"
        paths = [f"/r/{s}/search?restrict_sr=1&" for s in subs] if subs else ["/search?"]
        for pth in paths:
            r = requests.get(f"https://oauth.reddit.com{pth}" + up.urlencode({"q": q, "sort": "top", "t": t, "limit": 25}), headers=H, timeout=30).json()
            for c in r.get("data", {}).get("children", []):
                p = c["data"]
                out.append(item("reddit", "https://www.reddit.com" + p["permalink"], p["title"], p.get("selftext", ""), f"r/{p['subreddit']}",
                                p.get("author"), dt.datetime.fromtimestamp(p["created_utc"], dt.timezone.utc).isoformat(),
                                {"score": p.get("score"), "comments": p.get("num_comments"), "upvote_ratio": p.get("upvote_ratio")},
                                extra={"outbound": p.get("url")}))
        return out
    for n, s in enumerate(subs or registry()["subreddits"]["default"]):
        if n:
            time.sleep(2.5)  # reddit rate-limits unauthenticated RSS hard
        for o in rss(f"https://www.reddit.com/r/{s}/top/.rss?t=week", days, q):
            out.append(item("reddit", o["url"], o["title"], o["text"], f"r/{s}", o["author"], o["date"],
                            extra={"note": "RSS: no scores (set REDDIT_CLIENT_ID/SECRET for scores and search)"}))
    return out


def gh(path):
    tok = env("GITHUB_TOKEN")
    if tok:
        return requests.get("https://api.github.com/" + path, headers={**UA, "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}, timeout=30).json()
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0:
        return json.loads(r.stdout)
    return requests.get("https://api.github.com/" + path, headers=UA, timeout=30).json()


def github(q, days=30, active=False):
    """new repos (created in the window) ranked by stars = what is gaining attention now; --active = established + pushed"""
    since = (NOW - dt.timedelta(days=days)).date().isoformat()
    d = gh("search/repositories?" + up.urlencode({"q": f"{q} {'pushed' if active else 'created'}:>{since}", "sort": "stars", "order": "desc", "per_page": 15}))
    out = []
    for r in d.get("items", []):
        age = max(1, (NOW - dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).days)
        out.append(item("github", r["html_url"], r["full_name"], r.get("description") or "", "GitHub", r["owner"]["login"], r["created_at"],
                        {"stars": r["stargazers_count"], "forks": r["forks_count"], "stars_per_day": round(r["stargazers_count"] / age, 1)},
                        is_original=True, extra={"pushed_at": r["pushed_at"], "license": (r.get("license") or {}).get("spdx_id")}))
    return out


def repo(full):
    r = gh(f"repos/{full}")
    rel = gh(f"repos/{full}/releases?per_page=3")
    con = gh(f"repos/{full}/contributors?per_page=100&anon=1")
    since = (NOW - dt.timedelta(days=30)).isoformat()
    com = gh(f"repos/{full}/commits?since={since}&per_page=100")
    age = max(1, (NOW - dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).days)
    return [item("github", r["html_url"], r["full_name"], r.get("description") or "", "GitHub", r["owner"]["login"], r["created_at"],
                 {"stars": r["stargazers_count"], "forks": r["forks_count"], "watchers": r.get("subscribers_count"), "open_issues": r["open_issues_count"],
                  "stars_per_day": round(r["stargazers_count"] / age, 1), "contributors": len(con) if isinstance(con, list) else None,
                  "commits_30d": len(com) if isinstance(com, list) else None}, is_original=True,
                 extra={"pushed_at": r["pushed_at"], "license": (r.get("license") or {}).get("spdx_id"), "topics": r.get("topics"),
                        "releases": [{"tag": x["tag_name"], "date": x["published_at"], "name": x.get("name")} for x in rel] if isinstance(rel, list) else []})]


def hn(q, days=14):
    since = int(time.time() - days * 86400)
    d = get("https://hn.algolia.com/api/v1/search?" + up.urlencode({"query": q, "tags": "story", "numericFilters": f"created_at_i>{since}"})).json()
    return [item("hn", f"https://news.ycombinator.com/item?id={h['objectID']}", h["title"], "", "Hacker News", h.get("author"), h.get("created_at"),
                 {"points": h.get("points"), "comments": h.get("num_comments")}, extra={"outbound": h.get("url")}) for h in d.get("hits", [])[:15]]


def papers(q):
    out = []
    terms = " AND ".join(f'all:"{w}"' for w in re.findall(r"[\w-]+", q))
    r = get("https://export.arxiv.org/api/query?" + up.urlencode({"search_query": terms, "sortBy": "relevance", "max_results": 8}))
    if r.status_code == 200:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in xml_parse(r.content).findall("a:entry", ns):
            out.append(item("arxiv", e.find("a:id", ns).text, e.find("a:title", ns).text, e.find("a:summary", ns).text, "arXiv",
                            ", ".join(a.find("a:name", ns).text for a in e.findall("a:author", ns)[:4]), e.find("a:published", ns).text, is_original=True))
    hfp = get("https://huggingface.co/api/daily_papers")
    if hfp.status_code == 200:
        words = [w.lower() for w in re.findall(r"\w+", q) if len(w) > 2]
        for p in hfp.json():
            pp = p.get("paper", {})
            blob = (pp.get("title", "") + " " + pp.get("summary", "")).lower()
            if all(w in blob for w in words[:2]):
                out.append(item("hf_papers", f"https://huggingface.co/papers/{pp.get('id')}", pp.get("title"), pp.get("summary"), "Hugging Face Papers",
                                None, pp.get("publishedAt"), {"upvotes": pp.get("upvotes")}, is_original=True))
    return out


def read(url):
    import trafilatura
    r = get(url)
    if r.status_code in (401, 402, 403, 429, 503) or len(r.text) < 2000:
        return [item("read", url, extra={"error": f"HTTP {r.status_code}", "next": "capture ladder: agent-browser read/screenshot "
                 "(headless 412x915@3x -> --headed isolated session) -> Firecrawl (proxy stealth) -> for X posts the official embed "
                 "platform.twitter.com/embed/Tweet.html?id=<id>. Never cite a secondary outlet instead of fixing access."})]
    meta = trafilatura.extract_metadata(r.text)
    text = trafilatura.extract(r.text, include_comments=False, include_tables=False) or ""
    return [item("read", url, getattr(meta, "title", "") or "", text, getattr(meta, "sitename", None), getattr(meta, "author", None),
                 getattr(meta, "date", None), extra={"chars": len(text), "full_text_saved": False})]


# ---------- ledger + scoring ----------

TIER_W = {"official": 1.0, "press": 0.9, "trade": 0.7, "community": 0.6, "aggregator": 0.4, "unknown": 0.5}


def ledger_add(prod, items):
    p = Path(prod) / "research" / "sources.json"
    led = load_json(p) if p.exists() else []
    seen = {x["url"] for x in led}
    led += [i for i in items if i.get("url") and i["url"] not in seen]
    save_json(p, led)
    return len(led)


def score(prod):
    p = Path(prod) / "research" / "sources.json"
    led = load_json(p)
    for s in led:
        e = s.get("engagement") or {}
        eng = max([e.get(k, 0) or 0 for k in ("favorite_count", "score", "points", "stars", "upvotes", "comments", "conversation_count")] + [0])
        a = age_days(s.get("published_at") or "") if s.get("published_at") else None
        rec = 1.0 if a is None else max(0.2, 1 - a / 30)
        cor = len(s.get("corroborated_by") or [])
        s["score"] = round(0.35 * TIER_W.get(s.get("tier"), 0.5) + 0.2 * (1 if s.get("is_original") else 0) + 0.2 * min(1, math.log10(eng + 1) / 4)
                           + 0.15 * rec + 0.1 * min(1, cor / 3), 3)
    led.sort(key=lambda s: -s["score"])
    save_json(p, led)
    used = [s for s in led if s.get("claims")]
    warn = []
    pubs = {}
    for s in used:
        pubs[s["publisher"]] = pubs.get(s["publisher"], 0) + len(s["claims"])
    tot = sum(pubs.values()) or 1
    for k, v in pubs.items():
        if v / tot > 0.3 and len(pubs) > 1:
            warn.append(f"{k} supports {v / tot:.0%} of claims (>30%): diversify")
    if used and not any(s.get("is_original") for s in used):
        warn.append("no original/primary source supports any claim: find the official post, repo, paper or announcement")
    if used and not any(s["platform"] in ("reddit", "hn", "x") and not s.get("is_original") for s in led):
        warn.append("no community signal (Reddit/HN/X reactions) in the ledger")
    if any(not s.get("onscreen_ok", True) and s.get("onscreen") for s in led):
        warn.append("a source marked onscreen_ok=false is planned on screen: replace it with the original or a recognised masthead")
    return {"sources": len(led), "top": [{k: s.get(k) for k in ("score", "platform", "publisher", "title", "url")} for s in led[:12]], "warnings": warn}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--prod")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--tier", default="all")
    ap.add_argument("--subs")
    ap.add_argument("--active", action="store_true", help="github: established repos pushed recently instead of new ones")
    a = ap.parse_args()
    q = " ".join(a.args)
    c = a.cmd
    if c == "news": res = news(q, a.days)
    elif c == "feeds": res = feeds(q, a.tier, a.days)
    elif c == "x": res = [x_post(r) for r in a.args]
    elif c == "handles": return print(json.dumps(handles(q or None), indent=2, ensure_ascii=False))
    elif c == "reddit": res = reddit(q, a.subs.split(",") if a.subs else None, a.days)
    elif c == "github": res = github(q, a.days if a.days != 7 else 30, a.active)
    elif c == "repo": res = repo(a.args[0])
    elif c == "hn": res = hn(q, a.days if a.days != 7 else 14)
    elif c == "papers": res = papers(q)
    elif c == "read": res = read(a.args[0])
    elif c == "score": return print(json.dumps(score(a.prod), indent=2, ensure_ascii=False))
    else: raise SystemExit(__doc__)
    if a.prod:
        n = ledger_add(a.prod, res)
        print(f"ledger: {n} sources in {Path(a.prod) / 'research' / 'sources.json'}", file=sys.stderr)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
