"""Free, key-less trend scan across developer/AI sources -> ranked candidate list.

usage: rf trends [--days 7] [--out FILE] [--niche "ai,llm,agent,claude,..."]

Sources: GitHub search (new repos by stars), GitHub trending (daily+weekly HTML), Hacker News (Algolia),
Hugging Face trending models, Lobsters. Social platforms (X, Reddit, YouTube, IG) and news are covered by the
trend-scout agent with web search — this script supplies the hard momentum numbers.

Score = normalised momentum per source + convergence bonus (same entity in >1 source) + recency.
Convergence is the strongest signal found in the corpus (several creators covering the same repo within days).
"""
import argparse, datetime as dt, json, math, re, sys, time
from collections import defaultdict
import requests
from common import save_json

UA = {"User-Agent": "Mozilla/5.0 (compatible; reel-factory/1.0)"}
DEFAULT_NICHE = ("ai,llm,gpt,claude,anthropic,openai,gemini,agent,agents,mcp,rag,model,diffusion,video,voice,tts,"
                 "copilot,cursor,codex,prompt,ml,neural,transformer,inference,open-source,ollama,deepseek,qwen,llama,"
                 "automation,vibe,skill,skills,plugin,generative,robot,vision,ocr,embedding,fine-tune")


def niche_hit(text, words):
    t = (text or "").lower()
    return any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", t) for w in words)


SPAM = re.compile(r"(crack|keygen|serial key|license key|activat|full version|standalone|installer|setup with|free download|"
                  r"premium unlocked|mod apk|20\d\d.*(edition|desktop|pro)|adobe|aida|autocad|photoshop|office 20)", re.I)


def spam(full_name, desc):
    """malware-lure repos (fake stars, 'Pro 2026 standalone installer') are common in GitHub search results"""
    owner = full_name.split("/")[0]
    return bool(SPAM.search(f"{full_name} {desc or ''}")) or len(re.findall(r"\d", owner)) >= 4


def key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().split("/")[-1])[:40]


def github_new(days, words):
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    out = []
    for q in [f"created:>{since} stars:>150", f"created:>{since} stars:>80 topic:llm", f"created:>{since} stars:>80 topic:ai-agents"]:
        try:
            r = requests.get("https://api.github.com/search/repositories", params={"q": q, "sort": "stars", "order": "desc", "per_page": 50}, headers=UA, timeout=30)
            for it in r.json().get("items", []):
                blob = f"{it['full_name']} {it.get('description')} {' '.join(it.get('topics', []))}"
                if niche_hit(blob, words) and not spam(it["full_name"], it.get("description")):
                    age = max(1, (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(it["created_at"].replace("Z", "+00:00"))).days)
                    out.append({"source": "github-new", "title": it["full_name"], "desc": it.get("description"), "url": it["html_url"],
                                "metric": it["stargazers_count"], "velocity": it["stargazers_count"] / age, "key": key(it["full_name"])})
            time.sleep(1)
        except Exception as e:
            print("github search failed:", e, file=sys.stderr)
    return out


def github_trending(words):
    out = []
    for since in ["daily", "weekly"]:
        try:
            html = requests.get(f"https://github.com/trending?since={since}", headers=UA, timeout=30).text
            for row in html.split('<article class="Box-row">')[1:]:
                m = re.search(r'<h2[^>]*>\s*<a[^>]+href="/([^"/]+/[^"/]+)"', row)
                d = re.search(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', row, re.S)
                g = re.search(r"([\d,]+)\s+stars\s+(today|this week)", row)
                if not m:
                    continue
                desc = re.sub(r"<[^>]+>", "", d.group(1)).strip() if d else ""
                if niche_hit(f"{m.group(1)} {desc}", words) and not spam(m.group(1), desc):
                    out.append({"source": f"gh-trending-{since}", "title": m.group(1), "desc": desc, "url": f"https://github.com/{m.group(1)}",
                                "metric": int(g.group(1).replace(",", "")) if g else 0, "key": key(m.group(1))})
        except Exception as e:
            print("github trending failed:", e, file=sys.stderr)
    return out


def hackernews(days, words):
    since = int(time.time() - days * 86400)
    out = []
    try:
        d = requests.get("https://hn.algolia.com/api/v1/search", params={"tags": "story", "numericFilters": f"points>80,created_at_i>{since}", "hitsPerPage": 200}, timeout=30).json()
        for h in d.get("hits", []):
            if niche_hit(h["title"] + " " + (h.get("url") or ""), words):
                out.append({"source": "hackernews", "title": h["title"], "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                            "hn": f"https://news.ycombinator.com/item?id={h['objectID']}", "metric": h["points"], "comments": h.get("num_comments"),
                            "key": key((h.get("url") or "").rstrip("/").split("github.com/")[-1]) if "github.com" in (h.get("url") or "") else key(h["title"])})
    except Exception as e:
        print("hn failed:", e, file=sys.stderr)
    return out


def huggingface():
    out = []
    try:
        for m in requests.get("https://huggingface.co/api/models", params={"sort": "trendingScore", "limit": 25}, timeout=30).json():
            out.append({"source": "hf-trending", "title": m["id"], "url": f"https://huggingface.co/{m['id']}", "metric": m.get("trendingScore") or m.get("likes", 0),
                        "desc": m.get("pipeline_tag"), "key": key(m["id"])})
    except Exception as e:
        print("hf failed:", e, file=sys.stderr)
    return out


def lobsters(words):
    out = []
    try:
        for s in requests.get("https://lobste.rs/hottest.json", headers=UA, timeout=30).json():
            if niche_hit(s["title"] + " " + " ".join(s.get("tags", [])), words):
                out.append({"source": "lobsters", "title": s["title"], "url": s.get("url") or s["short_id_url"], "metric": s["score"], "key": key(s["title"])})
    except Exception as e:
        print("lobsters failed:", e, file=sys.stderr)
    return out


def rank(items):
    by_src = defaultdict(list)
    for it in items:
        by_src[it["source"].split("-")[0]].append(it)
    for src, lst in by_src.items():
        mx = max(math.log1p(x.get("velocity", x["metric"]) or 0) for x in lst) or 1
        for x in lst:
            x["norm"] = math.log1p(x.get("velocity", x["metric"]) or 0) / mx
    groups = defaultdict(list)
    for it in items:
        groups[it["key"]].append(it)
    ranked = []
    for k, g in groups.items():
        srcs = sorted({x["source"].split("-")[0] for x in g})
        best = max(g, key=lambda x: x["norm"])
        score = round(best["norm"] + 0.6 * (len(srcs) - 1) + 0.15 * (len({x["source"] for x in g}) - 1), 3)
        ranked.append({"score": score, "title": best["title"], "desc": next((x.get("desc") for x in g if x.get("desc")), None), "url": best["url"],
                       "sources": sorted({x["source"] for x in g}), "signals": [{"source": x["source"], "metric": x["metric"], **({"hn": x["hn"]} if x.get("hn") else {})} for x in g]})
    return sorted(ranked, key=lambda x: -x["score"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out")
    ap.add_argument("--niche", default=DEFAULT_NICHE)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    words = [w.strip().lower() for w in a.niche.split(",") if w.strip()]
    items = github_new(a.days, words) + github_trending(words) + hackernews(min(a.days, 4), words) + huggingface() + lobsters(words)
    ranked = rank(items)[: a.top]
    payload = {"generated": dt.datetime.now().isoformat(timespec="minutes"), "days": a.days, "n_raw": len(items), "candidates": ranked}
    if a.out:
        save_json(a.out, payload)
    for i, c in enumerate(ranked, 1):
        print(f"{i:2}. [{c['score']:.2f}] {c['title'][:70]}  ({', '.join(c['sources'])})\n      {(c['desc'] or '')[:110]}\n      {c['url']}")


if __name__ == "__main__":
    main()
