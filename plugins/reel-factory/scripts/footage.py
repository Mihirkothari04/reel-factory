"""Footage department: real video for the content track, every clip logged with its source for the on-screen label.

usage:
  rf footage find "<query>" [--source youtube|commons|nasa|archive|all] [--n 6]
        list candidate clips (title, channel/author, duration, licence, url). Pick the one that shows exactly what the
        narration says at that moment — the person, the product, the event — not something merely related.
  rf footage get <url> --prod DIR --name NAME [--start S] [--dur D] [--label "CNBC"]
        download a short section (default 6 s), muted, H.264, ≤1080p -> <prod>/public/footage/NAME.mp4 and record it in
        <prod>/footage.json (url, label, licence). Use the label as the shot's `label` chip ("Source: CNBC").

Policy (owner decision 2026-11-14): official/press media and free-licence stock first; news and YouTube clips of
real people are allowed as short excerpts (≤ ~6 s each, a few per reel) with a visible source label, never
re-uploaded whole, never edited to change what was said.
"""
import argparse, json, subprocess, sys, urllib.parse
from pathlib import Path
import requests
from common import load_json, log, save_json

UA = {"User-Agent": "reel-factory/3.0 (personal research tool)"}


def ytdlp():
    return [sys.executable, "-m", "yt_dlp"]


def find_youtube(q, n):
    r = subprocess.run(ytdlp() + ["--flat-playlist", "--dump-json", "--no-warnings", f"ytsearch{n}:{q}"], capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = []
    for line in r.stdout.splitlines():
        try:
            j = json.loads(line)
        except Exception:
            continue
        out.append({"source": "youtube", "title": j.get("title"), "by": j.get("channel") or j.get("uploader"), "dur": j.get("duration"),
                    "url": j.get("url") if str(j.get("url", "")).startswith("http") else f"https://www.youtube.com/watch?v={j.get('id')}",
                    "licence": "standard YouTube licence — short excerpt with source label"})
    return out


def find_commons(q, n):
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} filetype:video", "gsrnamespace": 6, "gsrlimit": n,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata|mediatype"}).json()
    out = []
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        out.append({"source": "commons", "title": p.get("title"), "by": (md.get("Artist", {}).get("value") or "")[:80], "dur": None,
                    "url": ii.get("url"), "licence": md.get("LicenseShortName", {}).get("value")})
    return out


def find_nasa(q, n):
    r = requests.get("https://images-api.nasa.gov/search", params={"q": q, "media_type": "video"}, headers=UA, timeout=30).json()
    out = []
    for it in r.get("collection", {}).get("items", [])[:n]:
        d = (it.get("data") or [{}])[0]
        try:
            assets = requests.get(it["href"], timeout=30).json()
            mp4 = next((a for a in assets if a.endswith("~medium.mp4") or a.endswith("~orig.mp4")), None)
        except Exception:
            mp4 = None
        if mp4:
            out.append({"source": "nasa", "title": d.get("title"), "by": d.get("center") or "NASA", "dur": None, "url": mp4.replace("http://", "https://"), "licence": "NASA media (public domain, credit NASA)"})
    return out


def find_archive(q, n):
    r = requests.get("https://archive.org/advancedsearch.php", headers=UA, timeout=30, params={
        "q": f"({q}) AND mediatype:movies", "fl[]": ["identifier", "title", "licenseurl", "creator"], "rows": n, "output": "json"}).json()
    return [{"source": "archive", "title": d.get("title"), "by": d.get("creator"), "dur": None, "url": f"https://archive.org/details/{d['identifier']}",
             "licence": d.get("licenseurl") or "check item page"} for d in r.get("response", {}).get("docs", [])]


FINDERS = {"youtube": find_youtube, "commons": find_commons, "nasa": find_nasa, "archive": find_archive}


def get(url, prod, name, start=0.0, dur=6.0, label=None):
    prod = Path(prod)
    out = prod / "public" / "footage" / f"{name}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".src.mp4")
    direct = url.lower().split("?")[0].endswith((".mp4", ".webm", ".ogv", ".mov"))
    if direct:
        with requests.get(url, headers=UA, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for ch in r.iter_content(1 << 20):
                    f.write(ch)
    else:
        sec = f"*{start:.2f}-{start + dur + 1:.2f}"
        cmd = ytdlp() + ["-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/bv*+ba/b", "--download-sections", sec,
                         "--force-keyframes-at-cuts", "--merge-output-format", "mp4", "--no-playlist", "--no-warnings", "-o", str(tmp), url]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        if r.returncode != 0 or not tmp.exists():
            raise SystemExit(f"footage: download failed: {(r.stderr or r.stdout)[-400:]}")
        start = 0.0  # the section download already starts at `start`
    vf = "scale='min(1920,iw)':-2:flags=lanczos,fps=30,format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.2f}", "-i", str(tmp), "-t", f"{dur:.2f}", "-an", "-vf", vf,
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", str(out)], check=True)
    tmp.unlink(missing_ok=True)
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
    w, h = (int(x) for x in pr.split(",")[:2])
    rec = load_json(prod / "footage.json") if (prod / "footage.json").exists() else {}
    rec[name] = {"url": url, "label": label, "src": f"footage/{name}.mp4", "start": start, "dur": dur, "aspect": round(w / h, 4)}
    save_json(prod / "footage.json", rec)
    log(prod, f"footage: {name} <- {url} ({dur:.1f}s, {w}x{h}{', label ' + label if label else ''})")
    print(json.dumps({"kind": "video", "src": rec[name]["src"], "aspect": rec[name]["aspect"], "fit": "cover" if w / h < 0.8 else "blurfill", **({"label": label} if label else {})}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find"); f.add_argument("q"); f.add_argument("--source", default="all"); f.add_argument("--n", type=int, default=6)
    g = sub.add_parser("get"); g.add_argument("url"); g.add_argument("--prod", required=True); g.add_argument("--name", required=True)
    g.add_argument("--start", type=float, default=0.0); g.add_argument("--dur", type=float, default=6.0); g.add_argument("--label")
    a = ap.parse_args()
    if a.cmd == "find":
        res = []
        for s in (FINDERS if a.source == "all" else [a.source]):
            try:
                res += FINDERS[s](a.q, a.n)
            except Exception as e:
                print(f"{s}: {str(e)[:120]}", file=sys.stderr)
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        get(a.url, a.prod, a.name, a.start, a.dur, a.label)


if __name__ == "__main__":
    main()
