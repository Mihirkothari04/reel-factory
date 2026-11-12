"""Automated QA of a rendered reel against corpus-derived production standards.

usage: rf qa <prod_dir>

Re-measures the final MP4 the same way the 88 reference reels were measured (analyze.py), then checks:
 loudness, VO start, pace, duration, visual-change cadence, black/frozen frames, audio clipping,
 and VO intelligibility (local Whisper transcript vs script, word error rate).
Writes out/qa/{report.json, report.md, sheet.jpg}. The qa-reviewer agent then inspects sheet.jpg visually.
Exit code 0 = no blocking failures.
"""
import difflib, re, sys
from pathlib import Path
from analyze import analyze, sh
from build import mode_spec
from common import load_json, norm_tok, save_json

# targets from analysis/REEL_ANALYSIS.md §1 (medians / IQR of 88 reels)
T = {"lufs": (-15.0, -13.0), "first_word_max": 0.35, "wpm": (165, 245), "dur": (15, 95), "max_scene": 6.5, "avg_scene": (1.2, 3.8), "wer_max": 0.12}


def wer(ref, hyp):
    a, b = [norm_tok(x) for x in ref if norm_tok(x)], [norm_tok(x) for x in hyp if norm_tok(x)]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    matched = sum(bl.size for bl in sm.get_matching_blocks())
    return 1 - matched / max(1, len(a))


def main():
    prod = Path(sys.argv[1])
    video = prod / "out" / "reel.mp4"
    qa = prod / "out" / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    sb = load_json(prod / "storyboard.json")
    spec = mode_spec(sb.get("meta", {}).get("mode"))
    T.update({k: tuple(v) if isinstance(v, list) else v for k, v in spec.get("qa", {}).items() if k not in ("skip", "require_music")})
    skip = set(spec.get("qa", {}).get("skip", []))
    o = analyze(video, qa, language=sb.get("language", "en"), force=True)
    m = load_json(o / "metrics.json")
    tr = load_json(o / "transcript.json")
    props = load_json(prod / "props.json")
    script = [w["w"] for w in load_json(prod / "words.json")] if (prod / "words.json").exists() else []
    scenes = props["scenes"]
    lens = [s["end"] - s["start"] for s in scenes]

    blk = sh(["ffmpeg", "-i", str(video), "-vf", "blackdetect=d=0.25:pix_th=0.02:pic_th=0.995", "-an", "-f", "null", "-"]).stderr
    frz = sh(["ffmpeg", "-i", str(video), "-vf", "freezedetect=n=0.002:d=2.5", "-an", "-f", "null", "-"]).stderr
    peak = sh(["ffmpeg", "-i", str(video), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"]).stderr
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", peak)
    w = wer(script, [x["w"] for x in tr["words"]]) if script else 0.0

    checks = [
        ("loudness", T["lufs"][0] <= (m["lufs"] or -99) <= T["lufs"][1], f"{m['lufs']} LUFS (target -14)", True),
        ("vo_starts_immediately", (m["first_word_at"] if m["first_word_at"] is not None else 9) <= T["first_word_max"], f"first word at {m['first_word_at']}s", True),
        ("pace", T["wpm"][0] <= m["wpm"] <= T["wpm"][1], f"{m['wpm']} wpm (target {T['wpm'][0]}-{T['wpm'][1]} for mode {spec['id']})", False),
        ("duration", T["dur"][0] <= m["dur"] <= T["dur"][1], f"{m['dur']}s (corpus median 51s)", False),
        ("longest_scene", max(lens) <= T["max_scene"], f"longest scene {max(lens):.1f}s (visual change needed every <=6.5s)", False),
        ("avg_scene", T["avg_scene"][0] <= sum(lens) / len(lens) <= T["avg_scene"][1], f"avg scene {sum(lens) / len(lens):.2f}s", False),
        ("no_black_frames", "black_start" not in blk, "black frames detected" if "black_start" in blk else "none", True),
        ("no_frozen_video", "freeze_start" not in frz, "frozen segment >2.5s" if "freeze_start" in frz else "none", False),
        ("no_clipping", not tp or float(tp[-1]) <= -0.5, f"true peak {tp[-1] if tp else '?'} dBFS", True),
        ("vo_intelligible", w <= T["wer_max"], f"WER vs script {w:.1%} (local Whisper)", True),
        ("music_bed", props["audio"].get("music") is not None, "music present" if props["audio"].get("music") else "no music bed (84% of corpus has one)", bool(spec.get("qa", {}).get("require_music"))),
    ]
    checks = [c for c in checks if c[0] not in skip]
    report = {"mode": spec["id"], "metrics": {k: m[k] for k in ["dur", "w", "h", "fps", "lufs", "wpm", "speech_ratio", "first_word_at", "n_cuts", "bed_db", "speech_db"]},
              "wer": round(w, 3), "scenes": len(scenes),
              "checks": [{"name": n, "pass": p, "detail": d, "blocking": b} for n, p, d, b in checks]}
    save_json(qa / "report.json", report)
    (o / "sheet.jpg").replace(qa / "sheet.jpg")
    md = ["# QA report", "", f"`{video}`", "", "| check | result | detail |", "|---|---|---|"]
    md += [f"| {c['name']} | {'PASS' if c['pass'] else ('FAIL' if c['blocking'] else 'warn')} | {c['detail']} |" for c in report["checks"]]
    md += ["", f"Contact sheet: `{qa / 'sheet.jpg'}` (review hook frames 0-2.5s, text legibility, safe zones, consistency)."]
    (qa / "report.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    sys.exit(1 if any(not c["pass"] and c["blocking"] for c in report["checks"]) else 0)


if __name__ == "__main__":
    main()
