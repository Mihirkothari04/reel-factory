"""Background music bed for a production.

usage: rf music <prod_dir> [--provider elevenlabs|openverse|none] [--prompt "..."]

Reads storyboard.music {prompt, mood} and words.json (for length). Writes public/music.mp3 (+ credits.txt for CC tracks).
Corpus: 84% of reels carry an instrumental bed ~10 dB under the VO; the engine ducks it under speech automatically.
"""
import argparse
from pathlib import Path
import requests
from common import config, eleven, load_json, log, run

H = {"User-Agent": "reel-factory/1.0"}


def el_music(prompt, seconds, out, model):
    full = (f"{prompt}. Instrumental background bed for a short-form tech explainer voice-over: steady groove, "
            "no vocals, no big drops, sits under speech, clean mix, ends with a soft resolve.")
    eleven(["music", "compose"], {"prompt": full, "music_length_ms": int(min(300, max(10, seconds)) * 1000),
                                  "force_instrumental": True, "model_id": model}, out=out)


def openverse(query, seconds, out, prod):
    r = requests.get("https://api.openverse.org/v1/audio/", params={"q": query, "license": "cc0,by", "category": "music", "page_size": 20}, headers=H, timeout=30)
    r.raise_for_status()
    hits = [h for h in r.json().get("results", []) if (h.get("duration") or 0) / 1000 >= min(seconds, 60) and h.get("url")]
    if not hits:
        raise RuntimeError("no suitable CC track")
    h = hits[0]
    tmp = Path(out).with_suffix(".src")
    tmp.write_bytes(requests.get(h["url"], headers=H, timeout=60).content)
    run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-t", str(seconds + 2), "-ac", "2", "-ar", "44100", "-c:a", "libmp3lame", "-q:a", "3", out])
    tmp.unlink()
    credit = f'Music: "{h.get("title")}" by {h.get("creator")} ({h.get("license", "").upper()} {h.get("license_version", "")}) {h.get("foreign_landing_url", "")}'
    (Path(prod) / "credits.txt").open("a", encoding="utf-8").write(credit + "\n")
    return credit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prod")
    ap.add_argument("--provider")
    ap.add_argument("--prompt")
    a = ap.parse_args()
    prod = Path(a.prod)
    sb = load_json(prod / "storyboard.json")
    spec = sb.get("music") or {}
    if spec.get("none"):
        log(prod, "music: none (storyboard)"); return
    words = load_json(prod / "words.json") if (prod / "words.json").exists() else []
    # narrated: last word + 3 s; silent: sum of scene durations + 1.5 s (beat snapping can stretch it slightly)
    seconds = words[-1]["e"] + 3 if words else sum(float(sc.get("dur", 2.5)) for sc in sb["scenes"]) + 1.5
    prompt = a.prompt or spec.get("prompt") or "minimal modern electronic, warm synth bass, light percussion, 105 bpm"
    out = prod / "public" / "music.mp3"
    mcfg = config().get("music", {})
    order = [a.provider] if a.provider else [mcfg.get("provider", "elevenlabs"), "openverse"]
    for p in order:
        try:
            if p == "elevenlabs":
                el_music(prompt, seconds, out, mcfg.get("model_id", "music_v2"))
                log(prod, f"music: elevenlabs {seconds:.0f}s · {prompt[:70]}")
            elif p == "openverse":
                c = openverse(spec.get("query") or spec.get("mood") or "lofi electronic instrumental", seconds, out, prod)
                log(prod, f"music: openverse · {c}")
            elif p == "none":
                log(prod, "music: none"); return
            return
        except Exception as e:
            log(prod, f"music: {p} failed ({str(e)[:140]})")
    log(prod, "music: all providers failed -> reel renders without a bed")


if __name__ == "__main__":
    main()
