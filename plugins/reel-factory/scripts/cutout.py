"""Cut-out stickers: remove the background from a photo of a person, product or logo (local, free) for gfx "sticker".

usage: rf cutout <image-path | image-url> --prod DIR --name NAME [--model birefnet-general|isnet-general-use|u2net_human_seg]
Writes <prod>/public/cut/NAME.png (RGBA, trimmed to the subject, max 1400 px) and prints the gfx JSON to paste.
Use press/official photos (company newsroom, Wikimedia Commons, the person's own posts) and add a label chip with
the name; never composite a real person into a scene that changes what happened.
"""
import argparse, io, json
from pathlib import Path
import requests
from PIL import Image
from common import log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("--prod", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--model", default="isnet-general-use")
    a = ap.parse_args()
    from rembg import new_session, remove
    raw = requests.get(a.src, headers={"User-Agent": "reel-factory/3.0"}, timeout=60).content if a.src.startswith("http") else Path(a.src).read_bytes()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    out = remove(im, session=new_session(a.model), post_process_mask=True)
    bbox = out.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if bbox:
        pad = 12
        out = out.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(out.width, bbox[2] + pad), min(out.height, bbox[3] + pad)))
    out.thumbnail((1400, 1400), Image.LANCZOS)
    dst = Path(a.prod) / "public" / "cut" / f"{a.name}.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    log(Path(a.prod), f"cutout: {a.name} <- {a.src[:90]} ({out.width}x{out.height})")
    print(json.dumps({"kind": "sticker", "src": f"cut/{a.name}.png", "w": 520, "x": 540, "y": 380, "text": a.name.replace("-", " ")}))


if __name__ == "__main__":
    main()
