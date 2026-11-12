"""Turn a real page screenshot into a reel-ready source shot: clean, crop, and locate the exact phrases to highlight.

usage:
  rf shot <image-path-or-url> --prod DIR --name tc --find "more like Google" [--find "..."]
          [--erase x,y,w,h ...] [--crop x,y,w,h | --aspect 1.0] [--pad 0.06]

- <image>: the capture (Firecrawl `screenshot` URL, or an agent-browser PNG). Use a phone viewport (mobile layout)
  so the headline is legible at reel size.
- --find: exact phrases from the page (case/punctuation-insensitive). Located with local OCR (RapidOCR, free).
- --erase: paint over cookie/paywall banners or ads (pixels of the ORIGINAL capture) with the surrounding colour.
  Never erase or alter the outlet's own words: overlays go on top, the page itself stays as published.
- --crop: manual crop in original pixels; default auto: the found phrases, centred, at --aspect (w/h) with the
  masthead kept when it fits.
Writes <prod>/public/img/shot-<name>.png + shot-<name>.json ({src, w, h, marks:[{text, rects}], focus}) and prints
the storyboard props for a `source` scene. Coordinates are fractions of the cropped image.
"""
import argparse, io, json, re, sys
from pathlib import Path
import requests
from PIL import Image, ImageStat

norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def load(src):
    if re.match(r"https?://", src):
        r = requests.get(src, timeout=60, headers={"User-Agent": "Mozilla/5.0 reel-factory"})
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    return Image.open(src).convert("RGB")


def erase(im, x, y, w, h):
    """fill a banner region with the median colour of a thin ring around it (flat page backgrounds)"""
    W, H = im.size
    ring = [im.crop((max(0, x - 6), max(0, y - 6), min(W, x + w + 6), max(0, y))) if y > 0 else None,
            im.crop((max(0, x - 6), min(H, y + h), min(W, x + w + 6), min(H, y + h + 6))) if y + h < H else None]
    ring = [r for r in ring if r and r.size[0] and r.size[1]]
    col = tuple(int(v) for v in ImageStat.Stat(ring[0]).median) if ring else (255, 255, 255)
    im.paste(col, (x, y, x + w, y + h))


def ink_words(im, x0, y0, x1, y1, text):
    """split an OCR text-line box into its word spans using the empty pixel columns between words"""
    import numpy as np
    n = len(text.split())
    if n < 2:
        return [(x0, x1)] if n == 1 else None
    g = np.asarray(im.crop((int(x0), int(y0), int(x1), int(y1))).convert("L"), dtype=np.int16)
    if g.size == 0:
        return None
    bg = np.median(g)
    ink = (np.abs(g - bg) > 60).any(axis=0)
    runs, start = [], None
    for x, v in enumerate(ink):
        if v and start is None:
            start = x
        if not v and start is not None:
            runs.append([start, x]); start = None
    if start is not None:
        runs.append([start, len(ink)])
    if len(runs) < n:
        return None
    # word spaces = wide gaps; pick, for each space the character count predicts, the nearest wide gap
    width = lambda i: runs[i][0] - runs[i - 1][1]
    ws = sorted(width(i) for i in range(1, len(runs)))
    wide = [i for i in range(1, len(runs)) if width(i) >= max(6, 1.4 * ws[len(ws) // 2])]
    if len(wide) < n - 1:
        return None
    L = len(ink)
    expect = [L * i / max(1, len(text)) for i, ch in enumerate(text.strip()) if ch == " "]
    if len(expect) != n - 1:
        return None
    cuts = []
    for e in expect:
        best = min((i for i in wide if i not in cuts), key=lambda i: abs((runs[i][0] + runs[i - 1][1]) / 2 - e), default=None)
        if best is None:
            return None
        cuts.append(best)
    if cuts != sorted(cuts):
        return None
    bounds = [0] + cuts + [len(runs)]
    return [(x0 + runs[a][0], x0 + runs[b - 1][1]) for a, b in zip(bounds, bounds[1:])]


def words(im):
    """OCR -> word boxes [(text, x0, y0, x1, y1)] in reading order; line boxes are split by character share"""
    from rapidocr_onnxruntime import RapidOCR
    res, _ = RapidOCR()(im)
    out = []
    for quad, text, conf in res or []:
        xs, ys = [p[0] for p in quad], [p[1] for p in quad]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        toks = text.split()
        segs = ink_words(im, x0, y0, x1, y1, text)
        if segs:  # exact word extents from the pixel gaps between words
            out += [(tk, a, y0, b, y1) for tk, (a, b) in zip(toks, segs)]
            continue
        total = max(1, len(text))  # fallback: split the line box by character share
        pos = 0
        for tk in toks:
            i = text.index(tk, pos)
            out.append((tk, x0 + (x1 - x0) * i / total, y0, x0 + (x1 - x0) * (i + len(tk)) / total, y1))
            pos = i + len(tk)
    # reading order: cluster into lines by vertical overlap (word heights vary with font size), then left to right
    lines = []
    for w in sorted(out, key=lambda w: (w[2] + w[4]) / 2):
        yc, hh = (w[2] + w[4]) / 2, w[4] - w[2]
        ln = next((l for l in lines if abs(l["yc"] - yc) < 0.5 * max(hh, l["h"])), None)
        if ln:
            ln["w"].append(w)
        else:
            lines.append({"yc": yc, "h": hh, "w": [w]})
    return [w for l in sorted(lines, key=lambda l: l["yc"]) for w in sorted(l["w"], key=lambda w: w[1])]


def find(ws, phrase):
    """consecutive OCR words matching the phrase -> one rect per text line"""
    want = [norm(t) for t in phrase.split() if norm(t)]
    have = [norm(w[0]) for w in ws]
    for i in range(len(have)):
        j, k, used = i, 0, []
        while k < len(want) and j < len(have):
            h = have[j]
            if not h:
                j += 1
                continue
            glued = next((m for m in range(2, 5) if k + m <= len(want) and h == "".join(want[k:k + m])), 0)  # OCR merged words
            if glued:
                used.append(j)
                k += glued
                j += 1
            elif h == want[k] or (len(h) >= 3 and (h.startswith(want[k]) or want[k].startswith(h))):  # trailing punctuation / plurals
                used.append(j)
                k += 1
                j += 1
            else:
                break
        if k == len(want):
            lines = {}
            for u in used:
                t, x0, y0, x1, y1 = ws[u]
                key = round((y0 + y1) / 2 / max(8, (y1 - y0) * 0.6))
                b = lines.setdefault(key, [x0, y0, x1, y1])
                b[:] = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
            return [tuple(b) for b in lines.values()]
    return None


def auto_crop(W, H, boxes, aspect, pad):
    fx0, fy0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    fx1, fy1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    cw = W  # keep the page's full width: margins and masthead are part of what makes it read as real
    ch = min(H, max(cw / aspect, (fy1 - fy0) * (1 + 4 * pad)))
    cy = (fy0 + fy1) / 2
    y0 = 0 if fy1 + pad * ch <= ch else min(H - ch, max(0, cy - ch * 0.45))  # keep the top (logo, date) if it fits
    return (0, int(y0), int(cw), int(y0 + ch))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("--prod", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--find", action="append", default=[]); ap.add_argument("--erase", action="append", default=[])
    ap.add_argument("--crop"); ap.add_argument("--aspect", type=float, default=1.0); ap.add_argument("--pad", type=float, default=0.06)
    a = ap.parse_args()
    im = load(a.src)
    for e in a.erase:
        erase(im, *[int(float(v)) for v in e.split(",")])
    ws = words(im)
    found, missing = [], []
    for ph in a.find:
        r = find(ws, ph)
        (found if r else missing).append((ph, r))
    if missing:
        print("not found on the page (check spelling / capture): " + "; ".join(p for p, _ in missing), file=sys.stderr)
    W, H = im.size
    if a.crop:
        x, y, w, h = [int(float(v)) for v in a.crop.split(",")]
        box = (x, y, x + w, y + h)
    elif found:
        box = auto_crop(W, H, [b for _, rs in found for b in rs], a.aspect, a.pad)
    else:
        box = (0, 0, W, min(H, int(W / a.aspect)))
    crop = im.crop(box)
    cw, ch = crop.size
    marks = []
    for ph, rs in found:
        rects = []
        for x0, y0, x1, y1 in rs:
            mx, my = (y1 - y0) * 0.12, (y1 - y0) * 0.08  # marker overhang, like a real highlighter
            rects.append({k: round(v, 4) for k, v in {"x": (x0 - box[0] - mx) / cw, "y": (y0 - box[1] - my) / ch,
                                                     "w": (x1 - x0 + 2 * mx) / cw, "h": (y1 - y0 + 2 * my) / ch}.items()})
        # a multiply highlighter only reads on light pages; dark pages get a bright underline marker instead
        lum = sum(ImageStat.Stat(crop.convert("L").crop((int(x0 - box[0]), int(y0 - box[1]), int(x1 - box[0]), int(y1 - box[1])))).median[0] for x0, y0, x1, y1 in rs) / len(rs)
        marks.append({"text": ph, "rects": rects, "style": "marker" if lum > 120 else "underline"})
    allr = [r for m in marks for r in m["rects"]]
    focus = {"x": min(r["x"] for r in allr), "y": min(r["y"] for r in allr), "w": 0, "h": 0} if allr else None
    if focus:
        focus["w"] = round(max(r["x"] + r["w"] for r in allr) - focus["x"], 4)
        focus["h"] = round(max(r["y"] + r["h"] for r in allr) - focus["y"], 4)
    out = Path(a.prod) / "public" / "img" / f"shot-{a.name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if cw > 1600:
        crop = crop.resize((1600, round(ch * 1600 / cw)), Image.LANCZOS)
    crop.save(out)
    meta = {"src": f"img/{out.name}", "w": crop.width, "h": crop.height, "marks": marks, "focus": focus}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"type": "source", "props": {"shot": f"img/{out.stem}.json"}, "found": [p for p, _ in found], "missing": [p for p, _ in missing]}, indent=2))
    if missing:
        sys.exit(2)


def selftest():
    ws = [("making", 0, 0, 100, 40), ("ChatGPT", 110, 0, 260, 40), ("just", 270, 0, 330, 40), ("a", 0, 60, 20, 100),
          ("little", 30, 60, 120, 100), ("more", 130, 60, 210, 100), ("like", 220, 60, 290, 100), ("Google", 300, 60, 420, 100)]
    assert find(ws, "more like Google") == [(130, 60, 420, 100)], find(ws, "more like Google")
    assert len(find(ws, "ChatGPT just a little")) == 2  # spans two lines -> two rects
    assert find(ws, "like Bing") is None
    assert find([("more", 0, 0, 80, 40), ("likeGoogle", 90, 0, 300, 40)], "more like Google") == [(0, 0, 300, 40)]  # glued words
    print("ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
