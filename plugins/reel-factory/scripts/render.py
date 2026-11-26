"""Render props.json with the Remotion engine, master loudness to -14 LUFS, export cover + caption.

usage: rf render <prod_dir> [--draft]      (--draft = half resolution, fast preview)

Outputs: out/reel.mp4 (1080x1920 H.264/AAC, -14 LUFS, -1.5 dBTP, faststart), out/cover.jpg, out/caption.txt, out/post-kit.md
"""
import argparse, json, math, re, shutil, subprocess, time
from pathlib import Path
from common import HOME, WIN, load_json, log, run


def chunked(prod, cmd, raw, step=60, tries=6):
    """Fallback when Remotion's compositor reports "No frame found" (seen with ~0 free RAM: frames get evicted before use).
    Bundle once, render short muted chunks (each retried), render the audio once (no video decode), join without re-encoding."""
    eng, tmp = HOME / "engine", raw.parent / "chunks"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    lg = open(raw.parent / "render.log", "a", encoding="utf-8", errors="replace")
    sh = lambda c, t: subprocess.run(list(map(str, c)), cwd=eng, stdout=lg, stderr=subprocess.STDOUT, timeout=t).returncode  # noqa: E731
    if sh([cmd[0], "remotion", "bundle", "src/index.ts", f"--out-dir={tmp / 'bundle'}", f"--public-dir={prod / 'public'}"], 1800):
        raise SystemExit("render failed: remotion bundle (see out/render.log)")
    keep = [c for c in cmd[5:] if c.startswith("--") and not c.startswith(("--public-dir", "--concurrency", "--log"))]
    base = [cmd[0], "remotion", "render", tmp / "bundle", cmd[4]] + keep + ["--log=error", "--concurrency=1", "--offthreadvideo-cache-size-in-bytes=600000000"]  # ponytail: tuned for ~0.1 GB free RAM; raise step/concurrency on a healthy machine
    props = load_json(prod / "props.json")
    total = max(1, math.ceil(props["durationSec"] * props.get("fps", 30)))  # = Root.tsx durationInFrames
    parts = []
    for a in range(0, total, step):
        f = tmp / f"v{a:05d}.mp4"
        if not any(sh(base + [f, f"--frames={a}-{min(total, a + step) - 1}", "--muted"], 1800) == 0 for _ in range(tries)):
            raise SystemExit(f"render failed: frames {a}-{min(total, a + step) - 1} after {tries} tries (see out/render.log)")
        parts.append(f)
        log(prod, f"render: chunk {len(parts)}/{math.ceil(total / step)}")
    wav = tmp / "audio.wav"
    if sh([c for c in base if not c.startswith(("--codec", "--crf", "--audio-codec", "--audio-bitrate"))] + [wav, "--codec=wav"], 1800):
        raise SystemExit("render failed: audio pass (see out/render.log)")
    (tmp / "list.txt").write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt", "-i", wav, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", raw])
    lg.close()
    shutil.rmtree(tmp, ignore_errors=True)


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
    comp = "Studio" if "layouts" in load_json(prod / "props.json") else "Reel"
    cmd = [npx, "remotion", "render", "src/index.ts", comp, str(raw), f"--props={prod / 'props.json'}", f"--public-dir={prod / 'public'}",
           "--log=error", "--codec=h264", "--crf=18", "--audio-codec=aac", "--audio-bitrate=192k"]
    if comp == "Studio":  # many alpha/H.264 streams decode at once; more workers race the compositor ("No frame found")
        cmd.append("--concurrency=3")
    if a.draft:
        cmd.append("--scale=0.5")
    t0 = time.time()
    # stream Remotion's progress into out/render.log (long renders must be watchable; a silent hang wastes time)
    import subprocess
    cmd = [c if c != "--log=error" else "--log=info" for c in cmd]
    with open(out / "render.log", "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen(list(map(str, cmd)), cwd=HOME / "engine", stdout=lf, stderr=subprocess.STDOUT)
        last, size = time.time(), 0
        while p.poll() is None:
            time.sleep(5)
            s = (out / "render.log").stat().st_size
            if s != size:
                last, size = time.time(), s
            elif time.time() - last > 900:
                p.kill()
                raise SystemExit("render stalled: no progress for 15 min (see out/render.log)")
    if p.returncode != 0 and not a.draft and "No frame found" in (out / "render.log").read_text(encoding="utf-8", errors="replace"):
        log(prod, "render: compositor dropped frames (No frame found; usually low free RAM) -> chunked render")
        chunked(prod, cmd, raw)
    elif p.returncode != 0:
        raise SystemExit(f"render failed (see out/render.log): {(out / 'render.log').read_text(encoding='utf-8', errors='replace')[-800:]}")
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
    e = sb.get("engagement") or {}
    if e.get("caption_question") and e["caption_question"] not in cap:
        cap = f"{cap}\n\n{e['caption_question']}".strip()
    (out / "caption.txt").write_text("\n\n".join(x for x in [cap, sources, credits, tags] if x), encoding="utf-8")
    if e:  # attention.md §4: what the team posts around the reel
        kit = ["# Post kit", "", "## Caption", "", (out / "caption.txt").read_text(encoding="utf-8"), "",
               "## Pin this comment right after posting", "", e.get("pinned_comment", ""), ""]
        if e.get("keyword"):
            kit += ["## Comment keyword -> DM", "", f"Keyword **{e['keyword']}** -> DM: {e.get('deliverable', '')}. "
                    "Commenters must follow first; `rf dm arm P` runs it automatically (else by hand within the hour).", ""]
        kit += ["## Share line / follow promise", "", f"- {e.get('share_line', '')}", f"- {e.get('follow_promise', '')}", "",
                "## Stories (funnel)", ""] + [f"{i}. {s}" for i, s in enumerate(e.get("stories") or [], 1)]
        (out / "post-kit.md").write_text("\n".join(kit) + "\n", encoding="utf-8")
    log(prod, f"render: final -> {final}")
    # production history: lets the next run vary mode/theme (rf modes shows it)
    m = sb.get("meta", {})
    hist = {"date": time.strftime("%Y-%m-%d"), "title": m.get("title"), "mode": m.get("mode", "kinetic"), "skeleton": sb.get("skeleton"),
            "theme": m.get("theme"), "dur": round(load_json(prod / "props.json")["durationSec"], 1), "path": str(final)}
    with open(HOME / "history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(hist, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
