"""Fetch primary-source facts and visuals without a browser.

usage:
  rf sources repo <owner/name> [--prod DIR]     GitHub facts (+ README excerpt, og image saved to <prod>/public/img/)
  rf sources og <url> --prod DIR [--name x]      download a page's og:image into <prod>/public/img/
  rf sources hn "<query>" [--days 14]           Hacker News discussions (points, comments, links)
Prints JSON. Set GITHUB_TOKEN to raise GitHub rate limits (optional).
"""
import argparse, base64, json, os, re, sys, time
from pathlib import Path
import requests
from common import slugify

H = {"User-Agent": "reel-factory/1.0", "Accept": "application/vnd.github+json"}
if os.environ.get("GITHUB_TOKEN"):
    H["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"


def save_img(url, prod, name):
    if not prod:
        return None
    r = requests.get(url, headers={"User-Agent": H["User-Agent"]}, timeout=40)
    r.raise_for_status()
    ext = ".png" if "png" in r.headers.get("content-type", "png") else ".jpg"
    rel = f"img/{name}{ext}"
    out = Path(prod) / "public" / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    return rel


def repo(full, prod=None):
    r = requests.get(f"https://api.github.com/repos/{full}", headers=H, timeout=30)
    r.raise_for_status()
    d = r.json()
    out = {k: d.get(k) for k in ["full_name", "description", "stargazers_count", "forks_count", "language", "homepage", "created_at", "pushed_at", "topics", "open_issues_count"]}
    out["license"] = (d.get("license") or {}).get("spdx_id")
    out["owner"], out["name"] = d["owner"]["login"], d["name"]
    out["url"] = d["html_url"]
    try:
        rd = requests.get(f"https://api.github.com/repos/{full}/readme", headers=H, timeout=30).json()
        txt = base64.b64decode(rd["content"]).decode("utf-8", "replace")
        txt = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", "", txt)
        out["readme_excerpt"] = re.sub(r"\n{3,}", "\n\n", txt).strip()[:6000]
    except Exception:
        out["readme_excerpt"] = None
    try:
        out["og_image"] = save_img(f"https://opengraph.githubassets.com/{int(time.time())}/{full}", prod, f"repo-{slugify(d['name'], 30)}")
    except Exception:
        out["og_image"] = None
    return out


def og(url, prod, name=None):
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0 reel-factory"}, timeout=30).text
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html) or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', html)
    title = re.search(r"<title[^>]*>([^<]+)", html)
    if not m:
        return {"url": url, "og_image": None, "title": title.group(1).strip() if title else None}
    img = requests.compat.urljoin(url, m.group(1))
    return {"url": url, "title": title.group(1).strip() if title else None, "og_image": save_img(img, prod, name or slugify(url, 30))}


def hn(q, days=14):
    since = int(time.time() - days * 86400)
    d = requests.get("https://hn.algolia.com/api/v1/search", params={"query": q, "tags": "story", "numericFilters": f"created_at_i>{since}"}, timeout=30).json()
    return [{"title": h["title"], "points": h.get("points"), "comments": h.get("num_comments"), "url": h.get("url"), "hn": f"https://news.ycombinator.com/item?id={h['objectID']}", "date": h.get("created_at")} for h in d.get("hits", [])[:15]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["repo", "og", "hn"])
    ap.add_argument("target")
    ap.add_argument("--prod")
    ap.add_argument("--name")
    ap.add_argument("--days", type=int, default=14)
    a = ap.parse_args()
    res = repo(a.target, a.prod) if a.kind == "repo" else og(a.target, a.prod, a.name) if a.kind == "og" else hn(a.target, a.days)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
