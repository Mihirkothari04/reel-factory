"""Optional AI presenter: lip-synced talking-head clip from a portrait + the reel's voice-over (ElevenLabs Flows, Creatify Aurora).

usage: rf avatar <prod_dir> [--image PATH]

Requires config.avatar.enabled = true and a portrait (config.avatar.image or --image): a well-lit, front-facing,
chest-up photo of a person who CONSENTED to being animated (e.g. the channel owner) or an original AI-generated character.
Never use a photo of a real third party. Writes public/avatar.mp4 and sets storyboard.avatar.src + meta.layout=split-avatar.
Credit-heavy: run only after voice is final.
"""
import argparse, base64, mimetypes
from pathlib import Path
import requests
from common import config, eleven, load_json, log, save_json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prod")
    ap.add_argument("--image")
    a = ap.parse_args()
    prod = Path(a.prod)
    acfg = config().get("avatar", {})
    if not acfg.get("enabled"):
        raise SystemExit("avatar disabled (rf config set avatar.enabled true)")
    img = Path(a.image or acfg.get("image") or "")
    if not img.is_file():
        raise SystemExit("no portrait image: set avatar.image in config or pass --image")
    vo = prod / "public" / "vo.mp3"
    mime = mimetypes.guess_type(img.name)[0] or "image/png"
    body = {"model_id": acfg.get("model_id", "creatify-aurora"), "resolution": "720p",
            "image": {"type": "inline_base64", "mime_type": mime, "content_base64": base64.b64encode(img.read_bytes()).decode()},
            "audio": {"type": "inline_base64", "mime_type": "audio/mpeg", "content_base64": base64.b64encode(vo.read_bytes()).decode()}}
    d = eleven(["flows", "video", "create-and-wait", "--wait-timeout", "1200"], body)
    if d.get("status") != "completed":
        raise SystemExit(f"avatar failed: {d.get('error_message') or d.get('status')}")
    out = prod / "public" / "avatar.mp4"
    out.write_bytes(requests.get(d["content_url"], timeout=300).content)
    sb = load_json(prod / "storyboard.json")
    sb["avatar"] = {"src": "avatar.mp4"}
    sb["meta"]["layout"] = "split-avatar"
    save_json(prod / "storyboard.json", sb)
    log(prod, f"avatar: generated {out.name} ({d['id']}) -> layout split-avatar")


if __name__ == "__main__":
    main()
