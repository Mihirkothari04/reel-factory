"""Creation-mode catalog with live availability (what this PC/config can produce right now) + recent history.

usage: rf modes [--json]

Availability:
  avatar_or_footage    -> ready if config avatar.enabled + avatar.image exists; otherwise "needs --footage <clip>"
  video_gen_or_images  -> ready if video_gen.enabled or images.max_per_reel > 0 (else falls back to its fallback mode)
History (~/.reel-factory/history.jsonl) lets the Creative Director avoid repeating the same mode/theme back to back.
"""
import json, sys
from pathlib import Path
from build import MODES
from common import HOME, config, load_json


def premium():
    """ElevenLabs logged in (from the last `rf probe`); unknown -> assume yes and let the tools fall back"""
    f = HOME / "profile.json"
    if not f.exists():
        return True
    return bool(json.loads(f.read_text(encoding="utf-8"))["optional"]["elevenlabs"].get("logged_in"))


def availability(req, cfg):
    if req == "avatar_or_footage":
        av = cfg.get("avatar", {})
        if av.get("enabled") and av.get("image") and Path(av["image"]).exists() and premium():
            return "ready (AI avatar)"
        return "needs your footage (--footage clip.mp4) or avatar setup"
    if req == "video_gen_or_images":
        if not premium():
            return "unavailable (no ElevenLabs login: no generated images/video)"
        if cfg.get("video_gen", {}).get("enabled"):
            return "ready (video b-roll)"
        if cfg.get("images", {}).get("max_per_reel", 0) > 0:
            return "ready (generated stills; video_gen off)"
        return "unavailable"
    return "ready"


def history(n=5):
    f = HOME / "history.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()][-n:]


def main():
    cfg = config()
    reg = load_json(MODES)
    rows = []
    for m in reg["modes"]:
        status = [availability(r, cfg) for r in m.get("requires", [])] or ["ready"]
        ok = all(s.startswith("ready") for s in status)
        rows.append({"id": m["id"], "name": m["name"], "one_liner": m["one_liner"], "status": "; ".join(status),
                     "available": ok, "fallback": m.get("fallback"), "skeletons": m["skeletons"], "cost": m["cost"]})
    if "--json" in sys.argv:
        print(json.dumps({"modes": rows, "history": history()}, indent=1, ensure_ascii=False))
        return
    print("| id | mode | status | cost | skeletons |\n|---|---|---|---|---|")
    for r in rows:
        st = r["status"] + ("" if r["available"] else f" → falls back to {r['fallback']}" if r["fallback"] else "")
        print(f"| {r['id']} | {r['name']} | {st} | {r['cost']} | {', '.join(r['skeletons'])} |")
    h = history()
    if h:
        print("\nRecent productions (newest last): " + " · ".join(f"{x.get('date')} {x.get('mode')}/{x.get('skeleton', '?')}/{x.get('theme')}" for x in h))


if __name__ == "__main__":
    main()
