"""Newsletter intel: ingest the daily Gmail-newsletter routine's ZIP and serve its stories as reel LEADS.

usage:
  rf news ingest [ZIP_OR_DIR ...] [--force] [--no-resolve] [--no-media]
        default input: every new *_AI-Tech-Newsletters.zip in ~/Downloads. Safe-extracts into the store, dedups emails
        by Gmail message ID, parses stories (stories.json from the routine, else the digest .md), resolves tracking
        redirects to real URLs, downloads images the cloud sandbox could not fetch, links the same story across days.
  rf news leads [--days 3] [--q "kw"] [--top 25] [--json]
        stories ranked by newsletter coverage (distinct newsletters, all days) then recency. Momentum signal.
  rf news grep "<query>" [--days 14] [--max 20]
        all-terms search over stories and raw email bodies; prints file, newsletter, snippets.

Store: config.json -> news.dir (default ~/.reel-factory/news): <date>/ (archive + stories.json), index.jsonl (one
row per story), emails.jsonl (one row per Gmail message), links.json (redirect cache), ingested.json.
Stories are NEWSLETTER CLAIMS. They are leads: verify against the primary source before a reel states anything.
"""
import argparse, base64, datetime as dt, html, json, re, shutil, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import urllib.parse as up
import requests
from common import HOME, config, load_json, save_json

STORE = Path((config().get("news") or {}).get("dir") or HOME / "news")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
TRACKERS = re.compile(r"(substack\.com/redirect/|link\.mail\.beehiiv\.com|awstrack\.me|list-manage\.com/track|/click\?|"
                      r"click\.[a-z0-9-]+\.[a-z]+/|links\.[a-z0-9-]+\.[a-z]+/|mailchi\.mp|lnkd\.in|t\.co/)", re.I)
URL = re.compile(r"https?://[^\s)\]>\"'`]+")
SKIP_SECTIONS = re.compile(r"top 10|promotional|synthesis", re.I)
SKIP_IMG = re.compile(r"start your substack|logo|avatar|icon|pixel|spacer", re.I)
TODAY = dt.date.today()


# ---------- store helpers ----------
def jl_read(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def jl_write(p, rows):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def jget(p, default):
    return load_json(p) if Path(p).exists() else default


def days_ago(d):
    return (TODAY - dt.date.fromisoformat(d)).days


# ---------- extraction ----------
def safe_extract(zp, dest):
    """zip-slip safe; untrusted archive. Returns the archive root folder inside dest."""
    dest = dest.resolve()
    with zipfile.ZipFile(zp) as z:
        if sum(i.file_size for i in z.infolist()) > 800 * 2 ** 20:
            sys.exit(f"{zp}: archive over 800 MB, refusing")
        for i in z.infolist():
            t = (dest / i.filename).resolve()
            if dest != t and dest not in t.parents:
                sys.exit(f"{zp}: unsafe path {i.filename!r}, refusing")
        z.extractall(dest)
    kids = [k for k in dest.iterdir() if k.is_dir()]
    return kids[0] if len(kids) == 1 and not (dest / "emails").exists() else dest


def archive_date(name):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else TODAY.isoformat()


# ---------- parsing ----------
def parse_email(md):
    """header table of an archived email file -> dict"""
    f = {}
    for line in md.read_text(encoding="utf-8").splitlines()[:40]:  # header is a table or a '- **Field:** value' list
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$", line) or re.match(r"[-*]\s+\*\*([^*:]+):?\*\*:?\s*(.+)", line)
        if m and m.group(1) not in ("Field", "---"):
            f.setdefault(m.group(1).strip().lower(), m.group(2))
    pick = lambda *ks: next((f[k] for k in ks if f.get(k)), "")
    link = lambda v: (re.search(r"https?://[^\s)\]]+", v or "") or [None])[0]
    date = pick("date (utc)", "date", "received")
    return {"file": md.name, "newsletter": re.sub(r"\s*\(.*$", "", pick("newsletter")).strip(), "subject": pick("subject"),
            "received_utc": re.split(r"\s*/\s*", date)[0], "gmail_id": (re.findall(r"[0-9a-f]{12,}", pick("gmail message id", "gmail id")) or [md.stem])[0],
            "gmail_url": link(pick("gmail viewurl", "gmail link", "gmail url", "gmail")), "web_url": link(pick("web version", "web url"))}


def email_codes(root):
    """INDEX.md table: code -> email file name"""
    idx = root / "INDEX.md"
    if not idx.exists():
        return {}
    return {m.group(1): m.group(2) for m in re.finditer(r"^\|\s*(E\d+)\s*\|.*?\(emails/([^)]+\.md)\)", idx.read_text(encoding="utf-8"), re.M)}


def parse_digest(md):
    """'## section' / '### N.N title' / '**a) sub**' blocks -> stories"""
    stories, section, cur = [], "", None
    for line in md.read_text(encoding="utf-8").splitlines():
        h2, h3 = re.match(r"^## (.+)", line), re.match(r"^### (\S+)\s+(.+)", line)
        sub = re.match(r"^\*\*([a-z])\)\s*(.+?)\*\*", line)
        if h2 or h3 or (sub and cur):
            if cur:
                stories.append(cur)
            cur = None
        if h2:
            section = re.sub(r"^[^A-Za-z]*\d*\.?\s*", "", h2.group(1)).strip()
            continue
        if SKIP_SECTIONS.search(section):
            continue
        if h3:
            cur = {"id": h3.group(1), "section": section, "headline": h3.group(2).strip(), "lines": []}
        elif sub and stories and stories[-1]["section"] == section:
            parent = stories[-1]["id"].rstrip("abcdefgh")
            cur = {"id": parent + sub.group(1), "section": section, "headline": sub.group(2).strip(), "lines": []}
        if cur:
            cur["lines"].append(line)
    if cur:
        stories.append(cur)
    out = []
    for s in stories:
        text = "\n".join(s.pop("lines"))
        if len(text) < 80:  # a heading-only umbrella (e.g. 2.1 intro) is covered by its sub-stories
            continue
        what = re.search(r"\*\*What (?:happened|it is|changed)[^*]*:\*\*\s*(.+)", text)
        out.append({**s, "what": (what.group(1) if what else re.sub(r"[*#\[\]]", "", text.split("\n", 1)[-1]).strip())[:600],
                    "text": text[:6000], "emails": sorted(set(re.findall(r"\[(E\d+)\]", text)), key=lambda c: int(c[1:])),
                    "links": [{"url": u.rstrip(".,;")} for u in dict.fromkeys(URL.findall(text))]})
    return out


def from_routine_json(p):
    """stories.json written by the routine itself (preferred over parsing markdown)"""
    d = load_json(p)
    out = []
    for s in d.get("stories", []):
        links = [{"url": l["url"], "final": l.get("decoded"), "label": l.get("label"), "outlet": l.get("outlet")} if isinstance(l, dict) else {"url": l}
                 for l in s.get("links", [])]
        out.append({"id": str(s.get("id")), "section": s.get("section", ""), "headline": s.get("headline", ""),
                    "what": s.get("what_happened", ""), "kind": s.get("kind"), "entities": s.get("entities", []),
                    "numbers": s.get("numbers", []), "text": json.dumps(s, ensure_ascii=False)[:6000],
                    "emails": s.get("emails", []), "links": links})
    return out


# ---------- links ----------
def jwt_dest(u):
    """substack.com/redirect/2/<jwt>: destination sits in the token payload ('e'), no network needed"""
    m = re.search(r"/redirect/2/([\w-]+)\.([\w-]+)\.", u)
    if not m:
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(m.group(2) + "=" * (-len(m.group(2)) % 4))).get("e")
    except Exception:
        return None


def clean(u):
    p = up.urlsplit(u)
    q = [(k, v) for k, v in up.parse_qsl(p.query, keep_blank_values=True)
         if not k.lower().startswith(("utm_", "mc_")) and k not in ("j", "r", "token", "isFreemail", "_bhlid")]
    return up.urlunsplit((p.scheme, p.netloc, p.path, up.urlencode(q), p.fragment))


def resolve(u):
    d = jwt_dest(u)
    if d:
        return clean(d)
    try:
        for _ in range(4):  # HTTP redirects, then <meta refresh> pages (substack serves those to non-browser clients)
            r = requests.get(u, headers=UA, timeout=15, allow_redirects=True, stream=True)
            body = next(r.iter_content(65536, decode_unicode=False), b"").decode("utf-8", "replace") if TRACKERS.search(r.url) else ""
            r.close()
            m = re.search(r"http-equiv=[\"']?refresh[\"']?[^>]*?url=([^\"'>\s]+)", body, re.I)
            if not m:
                return clean(r.url)
            u = html.unescape(m.group(1))
        return clean(u)
    except Exception as e:
        return f"unresolved: {type(e).__name__}"


def resolve_all(stories):
    cache = jget(STORE / "links.json", {})
    todo = {l["url"] for s in stories for l in s["links"]
            if not l.get("final") and TRACKERS.search(l["url"]) and (l["url"] not in cache or TRACKERS.search(cache[l["url"]]) or cache[l["url"]].startswith("unresolved"))}
    if todo:
        print(f"resolving {len(todo)} tracking links ...", flush=True)
        with ThreadPoolExecutor(8) as ex:
            cache.update(zip(todo, ex.map(resolve, todo)))
        save_json(STORE / "links.json", cache)
    for s in stories:
        for l in s["links"]:
            l["final"] = clean(l["final"]) if l.get("final") else cache.get(l["url"], clean(l["url"]))
    bad = sum(1 for s in stories for l in s["links"] if l["final"].startswith("unresolved"))
    if bad:
        print(f"  {bad} links unresolved (kept original)")


# ---------- media ----------
def fetch_media(root):
    """download remote images the cloud run could not; rewrite the reference to the local file, keep the original as comment"""
    got = fail = 0
    for md in sorted((root / "emails").glob("*.md")):
        text = md.read_text(encoding="utf-8")
        mf = re.search(r"\]\(\.\./media/([^/)]+)/?\)", text)
        folder = root / "media" / (mf.group(1) if mf else md.stem)
        n = len(list(folder.glob("r-*"))) if folder.exists() else 0

        def swap(m):
            nonlocal n, got, fail
            alt, url = m.group(1), m.group(2)
            if SKIP_IMG.search(alt) or SKIP_IMG.search(url[:120]):
                return m.group(0)
            try:
                r = requests.get(url, headers=UA, timeout=20)
                ct = r.headers.get("content-type", "")
                if r.status_code != 200 or not ct.startswith("image/") or len(r.content) > 15 * 2 ** 20:
                    raise ValueError(ct or r.status_code)
                n += 1
                ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(ct.split("/")[1].split(";")[0], ct.split("/")[1].split(";")[0])
                folder.mkdir(parents=True, exist_ok=True)
                (folder / f"r-{n:02d}.{ext}").write_bytes(r.content)
                got += 1
                return f"![{alt}](../media/{folder.name}/r-{n:02d}.{ext})<!-- original: {url} -->"
            except Exception:
                fail += 1
                return m.group(0)

        new = re.sub(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)", swap, text)
        if new != text:
            md.write_text(new, encoding="utf-8")
    print(f"media: {got} images downloaded, {fail} failed (left remote)")


# ---------- threads across days ----------
STOP = set("the a an and or of to for in on with by is are its it new now from at as vs".split())


def toks(s):
    return {w for w in re.findall(r"[a-z0-9.]+", s.lower()) if w not in STOP and len(w) > 1}


def thread_for(s, prior):
    t = toks(s["headline"])
    best, score = None, 0.0
    for p in prior:
        o = toks(p["headline"])
        j = len(t & o) / max(1, len(t | o))
        if j > score:
            best, score = p, j
    return best["thread"] if best and score >= 0.5 else f"{s['date']}:{s['id']}"


# ---------- commands ----------
def ingest_one(src, a):
    src = Path(src)
    date = archive_date(src.name)
    reg = jget(STORE / "ingested.json", {})
    sig = f"{src.name}:{src.stat().st_size if src.is_file() else 'dir'}"
    if sig in reg and not a.force:
        print(f"skip {src.name} (already ingested as {reg[sig]})")
        return
    dest = STORE / date
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    if src.is_file():
        root = safe_extract(src, dest)
    else:
        shutil.copytree(src, dest / src.name)
        root = dest / src.name
    # emails + dedup by Gmail id
    seen = {e["gmail_id"]: e for e in jl_read(STORE / "emails.jsonl")}
    codes = email_codes(root)
    by_file = {}
    for md in sorted((root / "emails").glob("*.md")):
        e = parse_email(md)
        e["code"] = next((c for c, f in codes.items() if f == md.name), None)
        e["date"], e["path"] = date, str(md)
        e["repeat"] = e["gmail_id"] in seen and seen[e["gmail_id"]]["date"] != date
        if not e["repeat"]:
            seen[e["gmail_id"]] = e
        by_file[md.name] = e
    jl_write(STORE / "emails.jsonl", list(seen.values()))
    by_code = {e["code"]: e for e in by_file.values() if e["code"]}
    # stories
    rj = root / "stories.json"
    digest = next(root.glob("*Intelligence-Digest*.md"), None)
    stories = from_routine_json(rj) if rj.exists() else parse_digest(digest) if digest else []
    if not stories:
        print(f"warning: {src.name}: no stories.json or digest found")
    if not a.no_resolve:
        resolve_all(stories)
    if not a.no_media:
        fetch_media(root)
    prior = [r for r in jl_read(STORE / "index.jsonl") if r["date"] != date]
    recent = [r for r in prior if days_ago(r["date"]) <= 14]
    rows = []
    for s in stories:
        es = [by_code[c] for c in s["emails"] if c in by_code]
        s.update(date=date, newsletters=sorted({e["newsletter"] for e in es}), gmail_ids=[e["gmail_id"] for e in es],
                 email_files=[e["path"] for e in es], fresh=not es or any(not e["repeat"] for e in es))
        s["thread"] = thread_for(s, recent)
        rows.append(s)
    save_json(dest / "stories.json", {"date": date, "source": src.name, "stories": rows})
    jl_write(STORE / "index.jsonl", prior + rows)
    reg[sig] = date
    save_json(STORE / "ingested.json", reg)
    rep = sum(e["repeat"] for e in by_file.values())
    print(f"ingested {src.name} -> {dest}\n  {len(by_file)} emails ({rep} already seen), {len(rows)} stories, "
          f"{sum(1 for s in rows if not s['thread'].startswith(date))} continue earlier threads")


def ingest(a):
    srcs = a.inputs or sorted((Path.home() / "Downloads").glob("*_AI-Tech-Newsletters.zip"))
    if not srcs:
        print("no *_AI-Tech-Newsletters.zip in ~/Downloads")
    for s in srcs:
        ingest_one(s, a)


def threads(days):
    # repeat rows (only already-seen emails) add no momentum
    rows = [r for r in jl_read(STORE / "index.jsonl") if days_ago(r["date"]) <= days and r.get("fresh", True)]
    th = {}
    for r in rows:
        t = th.setdefault(r["thread"], {"headline": r["headline"], "first": r["date"], "last": r["date"], "newsletters": set(),
                                        "days": set(), "links": [], "stories": []})
        t["newsletters"] |= set(r["newsletters"])
        t["days"].add(r["date"])
        t["first"], t["last"] = min(t["first"], r["date"]), max(t["last"], r["date"])
        if r["date"] == t["last"]:
            t["headline"] = r["headline"]
        t["links"] += [l.get("final", l["url"]) for l in r["links"] if l.get("final", l["url"]) not in t["links"]]
        t["stories"].append({"date": r["date"], "id": r["id"], "section": r["section"], "what": r["what"], "email_files": r["email_files"]})
    for t in th.values():
        t["coverage"] = len(t["newsletters"])
        t["score"] = 2 * t["coverage"] + len(t["days"]) + max(0, 3 - days_ago(t["last"]))
    return th


def leads(a):
    th = threads(a.days)
    items = sorted(th.items(), key=lambda kv: (kv[1]["score"], kv[1]["last"]), reverse=True)
    if a.q:
        terms = a.q.lower().split()
        items = [kv for kv in items if all(w in (kv[1]["headline"] + " ".join(s["what"] for s in kv[1]["stories"])).lower() for w in terms)]
    items = items[:a.top]
    if a.json:
        print(json.dumps([{"thread": k, **{**v, "newsletters": sorted(v["newsletters"]), "days": sorted(v["days"])}} for k, v in items],
                         indent=1, ensure_ascii=False))
        return
    if not items:
        print(f"no stories in the last {a.days} days (store {STORE}); run `rf news ingest`")
        return
    print(f"{'score':>5} {'nl':>2} {'last':10}  headline / first real link")
    for k, v in items:
        link = next((l for l in v["links"] if not TRACKERS.search(l) and not l.startswith("unresolved")), v["links"][0] if v["links"] else "")
        print(f"{v['score']:>5} {v['coverage']:>2} {v['last']:10}  {v['headline'][:90]}\n{'':20}{', '.join(sorted(v['newsletters']))[:90]}\n{'':20}{link[:110]}")
    print(f"\nnl = distinct newsletters covering it. Leads only: verify every claim at the primary source. Store: {STORE}")


def grep(a):
    terms = a.query.lower().split()
    hits = 0
    for r in jl_read(STORE / "index.jsonl"):
        if days_ago(r["date"]) <= a.days and r.get("fresh", True) and all(w in r["text"].lower() for w in terms):
            print(f"[story {r['date']} {r['id']}] {r['headline']}\n   {r['what'][:240]}\n   links: {', '.join(l.get('final', l['url']) for l in r['links'][:4])}")
            hits += 1
    for e in jl_read(STORE / "emails.jsonl"):
        if days_ago(e["date"]) > a.days or not Path(e["path"]).exists() or hits >= a.max:
            continue
        body = Path(e["path"]).read_text(encoding="utf-8")
        low = body.lower()
        if all(w in low for w in terms):
            hits += 1
            print(f"[email {e['date']} {e.get('code') or ''}] {e['newsletter']}: {e['subject']}\n   {e['path']}")
            for i in [m.start() for m in re.finditer(re.escape(terms[0]), low)][:3]:
                print("   …" + re.sub(r"\s+", " ", body[max(0, i - 120):i + 160]) + "…")
    if not hits:
        print(f"no matches for {a.query!r} in the last {a.days} days")


def selftest(_):
    import tempfile
    tok = base64.urlsafe_b64encode(json.dumps({"e": "https://x.com/a?utm_source=s&id=1"}).encode()).decode().rstrip("=")
    assert jwt_dest(f"https://substack.com/redirect/2/eyJ.{tok}.sig") == "https://x.com/a?utm_source=s&id=1"
    assert clean("https://x.com/a?utm_source=s&id=1&r=2") == "https://x.com/a?id=1"
    with tempfile.TemporaryDirectory() as d:
        md = Path(d) / "digest.md"
        md.write_text("## ⚡ Top 10 at a glance\n1. skip me [E09]\n## 1. 🧠 Models\n### 1.1 Gemini 4 Neon ships\n- **What happened:** Google released it. [E03][E05]\n"
                      "- **Source:** https://substack.com/redirect/abc\n## 2. 🤖 Agents\n### 2.1 Verification theme\nSix newsletters land on one message.\n"
                      "**a) Anthropic guide** [E12]\n- **The claim:** 90% of code is reviewed by Claude, long enough text here.\n", encoding="utf-8")
        s = parse_digest(md)
        assert [x["id"] for x in s] == ["1.1", "2.1a"], [x["id"] for x in s]
        assert s[0]["emails"] == ["E03", "E05"] and s[0]["section"] == "Models" and s[0]["what"].startswith("Google released")
        e = Path(d) / "e.md"
        e.write_text("# T\n\n- **Newsletter:** The Agent Stack (by X)\n- **Gmail message ID:** 1a206ca33ab9b787\n"
                     "- **Date:** 2026-11-23 05:01:51 UTC / 10:31 IST\n", encoding="utf-8")
        p = parse_email(e)
        assert p["newsletter"] == "The Agent Stack" and p["gmail_id"] == "1a206ca33ab9b787" and p["received_utc"] == "2026-11-23 05:01:51 UTC", p
    assert thread_for({"headline": "Google Gemini 4 Neon pricing", "date": "d", "id": "1"}, [{"headline": "Gemini 4 Neon pricing explained", "thread": "T"}]) == "T"
    print("news selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    i = sp.add_parser("ingest"); i.add_argument("inputs", nargs="*"); i.add_argument("--force", action="store_true")
    i.add_argument("--no-resolve", action="store_true"); i.add_argument("--no-media", action="store_true")
    l = sp.add_parser("leads"); l.add_argument("--days", type=int, default=3); l.add_argument("--q"); l.add_argument("--top", type=int, default=25)
    l.add_argument("--json", action="store_true")
    g = sp.add_parser("grep"); g.add_argument("query"); g.add_argument("--days", type=int, default=14); g.add_argument("--max", type=int, default=20)
    sp.add_parser("selftest")
    a = ap.parse_args()
    {"ingest": ingest, "leads": leads, "grep": grep, "selftest": selftest}[a.cmd](a)


if __name__ == "__main__":
    main()
