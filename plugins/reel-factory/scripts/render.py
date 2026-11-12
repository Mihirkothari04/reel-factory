"""Render props.json with the Remotion engine, master loudness to -14 LUFS, export cover + caption.

usage: rf render <prod_dir> [--draft]      (--draft = half resolution, fast preview)

Outputs: out/reel.mp4 (1080x1920 H.264/AAC, -14 LUFS, -1.5 dBTP, faststart), out/cover.jpg, out/caption.txt
"""
import argparse, json, re, shutil, time
from pathlib import Path
from common import HOME, WIN, load_json, log, run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prod")
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    prod = Path(a.prod).resolve()
    out = prod / "out"
    out.mkdir(exist_ok=True)
    raw = out / ("draft.mp4" if a.draft else "raw.mp4")
    npx = shutil.which("npx.cmd" if WIN else "npx") or shutil.which("npx")
    cmd = [npx, "remotion", "render", "src/index.ts", "Reel", str(raw), f"--props={prod / 'props.json'}", f"--public-dir={prod / 'public'}",
           "--log=error", "--codec=h264", "--crf=18", "--audio-codec=aac", "--audio-bitrate=192k"]
    if a.draft:
        cmd.append("--scale=0.5")
    t0 = time.time()
    run(cmd, cwd=HOME / "engine")
    log(prod, f"render: {'draft' if a.draft else 'full'} in {time.time() - t0:.0f}s")
    if a.draft:
        return
    final = out / "reel.mp4"
    # two-pass loudnorm: measure, then apply linear normalisation -> lands on -14.0 LUFS (Instagram's target)
    meas = run(["ffmpeg", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-vn", "-f", "null", "-"]).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-c:v", "copy", "-af", ln, "-ar", "48000",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
    raw.unlink()
    sb = load_json(prod / "storyboard.json")
    cover_t = sb.get("cover_at", 1.2)
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(cover_t), "-i", final, "-frames:v", "1", "-q:v", "2", out / "cover.jpg"])
    cap = sb.get("caption", "").strip()
    tags = " ".join("#" + re.sub(r"[^A-Za-z0-9_]", "", h) for h in sb.get("hashtags", []))
    credits = (prod / "credits.txt").read_text(encoding="utf-8").strip() if (prod / "credits.txt").exists() else ""
    sources = "\n".join(f"Source: {s}" for s in sb.get("sources_in_caption", []))
    (out / "caption.txt").write_text("\n\n".join(x for x in [cap, sources, credits, tags] if x), encoding="utf-8")
    log(prod, f"render: final -> {final}")
    # production history: lets the next run vary mode/theme (rf modes shows it)
    m = sb.get("meta", {})
    hist = {"date": time.strftime("%Y-%m-%d"), "title": m.get("title"), "mode": m.get("mode", "kinetic"), "skeleton": sb.get("skeleton"),
            "theme": m.get("theme"), "dur": round(load_json(prod / "props.json")["durationSec"], 1), "path": str(final)}
    with open(HOME / "history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(hist, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
