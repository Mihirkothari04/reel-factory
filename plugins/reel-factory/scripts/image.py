"""Generate visual assets declared in storyboard.json (images and optional b-roll clips) via ElevenLabs Flows.

usage: rf image <prod_dir> [--dry-run]

Each scene may declare  "assets": [{"kind": "image"|"video", "prompt": "...", "out": "img/s3.png", "aspect": "9:16"|"4:5"|"1:1"|"16:9", "seconds": 5}]
Budgets come from ~/.reel-factory/config.json (images.max_per_reel, video_gen.enabled/max_clips).
Skips assets whose file already exists (idempotent re-runs). Writes assets.json with what was produced / skipped.
"""
import argparse
from pathlib import Path
import requests
from common import config, eleven, load_json, log, save_json

STYLE_GUARD = ("No text, no letters, no watermarks, no logos of real companies, no recognisable real people. "
               "Clean composition with clear subject, generous negative space.")


def gen(kind, a, cfg):
    if kind == "image":
        icfg = cfg.get("images", {})
        body = {"model_id": icfg.get("model_id", "gpt-image-2"), "prompt": f"{a['prompt']}. {STYLE_GUARD}", "aspect_ratio": a.get("aspect", "4:5")}
        if body["model_id"].startswith("gpt-image"):
            body["quality"] = icfg.get("quality", "medium")
        return eleven(["flows", "image", "create-and-wait", "--wait-timeout", "300"], body)
    vcfg = cfg.get("video_gen", {})
    body = {"model_id": vcfg.get("model_id", "bytedance-seedance-v2-fast"), "prompt": f"{a['prompt']}. No text overlays, no real people.",
            "aspect_ratio": "9:16", "duration_secs": int(a.get("seconds", 5)), "generate_audio": False, "resolution": "720p"}
    return eleven(["flows", "video", "create-and-wait", "--wait-timeout", "600"], body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prod")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    prod = Path(a.prod)
    cfg = config()
    sb = load_json(prod / "storyboard.json")
    budget = {"image": cfg.get("images", {}).get("max_per_reel", 4),
              "video": cfg.get("video_gen", {}).get("max_clips", 1) if cfg.get("video_gen", {}).get("enabled") else 0}
    used = {"image": 0, "video": 0}
    report = []
    for sc in sb["scenes"]:
        for asset in sc.get("assets", []):
            kind = asset.get("kind", "image")
            out = prod / "public" / asset["out"]
            if out.exists():
                report.append({"scene": sc["id"], "out": asset["out"], "status": "exists"}); continue
            if used[kind] >= budget[kind]:
                report.append({"scene": sc["id"], "out": asset["out"], "status": f"skipped: {kind} budget"}); continue
            if a.dry_run:
                report.append({"scene": sc["id"], "out": asset["out"], "status": "dry-run"}); continue
            try:
                d = gen(kind, asset, cfg)
                if d.get("status") != "completed":
                    raise RuntimeError(d.get("error_message") or d.get("status"))
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(requests.get(d["content_url"], timeout=120).content)
                used[kind] += 1
                report.append({"scene": sc["id"], "out": asset["out"], "status": "generated", "id": d["id"]})
                log(prod, f"asset: {kind} {asset['out']} generated")
            except Exception as e:
                report.append({"scene": sc["id"], "out": asset["out"], "status": f"failed: {str(e)[:160]}"})
                log(prod, f"asset: {kind} {asset['out']} FAILED ({str(e)[:120]})")
    save_json(prod / "assets.json", report)
    print(f"images {used['image']}/{budget['image']} · videos {used['video']}/{budget['video']}")


if __name__ == "__main__":
    main()
