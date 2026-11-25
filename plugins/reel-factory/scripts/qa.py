"""Automated QA of a rendered reel against corpus-derived production standards.

usage: rf qa <prod_dir>

Re-measures the final MP4 the same way the 88 reference reels were measured (analyze.py), then checks:
 loudness, VO start, pace, duration, visual-change cadence, black/frozen frames, audio clipping,
 and VO intelligibility (local Whisper transcript vs script, word error rate).
Writes out/qa/{report.json, report.md, sheet.jpg}. The qa-reviewer agent then inspects sheet.jpg visually.
Exit code 0 = no blocking failures.
"""
import re, sys
from pathlib import Path
from analyze import analyze, sh
from build import mode_spec
from common import consistency_issues, load_json, save_json, wer_score

# targets from analysis/REEL_ANALYSIS.md §1 (medians / IQR of 88 reels)
T = {"lufs": (-15.0, -13.0), "first_word_max": 0.35, "wpm": (165, 245), "dur": (15, 95), "max_scene": 6.5, "avg_scene": (1.2, 3.8), "wer_max": 0.12}


def wer(ref, hyp):
    return wer_score(ref, hyp)  # numbers/hyphens normalised (common.wer_tokens)


def edit_metrics(video):
    """how alive the edit is, measured like the reference reels (4 fps, 72x128 grey): big picture changes per minute,
    % of seconds with no visible change, and the longest still stretch. References: 48-129 changes/min, 0-6 % static."""
    import numpy as np, subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "fps=4,scale=72:128,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, 128, 72).astype(np.int16)
    d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    n = len(d) // 4
    per_s = d[: n * 4].reshape(n, 4).max(axis=1)
    still = per_s < 1.0
    run = best = 0
    for s in still:
        run = run + 1 if s else 0
        best = max(best, run)
    return {"changes_per_min": round(float((d > 12).sum()) / (len(a) / 4) * 60, 1), "static_pct": round(float(still.mean()) * 100, 1), "longest_still_s": int(best)}


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
    if script and sb.get("soundbites"):  # the soundbites' own speech is part of what the viewer hears
        from studio import soundbite_plan
        vw = load_json(prod / "words.json")
        seq = sorted([(w["s"], 0, w["w"]) for w in vw] + [(s["at"] + 1e-3 * (i + 1), 1, w["w"]) for s in soundbite_plan(prod, sb, vw)
                                                         for i, w in enumerate(s["words"])])
        script = [w for _, _, w in seq]
    studio = "layouts" in props
    scenes = props["shots"] if studio else props["scenes"]
    lens = [s["to"] - s["from"] for s in scenes] if studio else [s["end"] - s["start"] for s in scenes]

    blk = sh(["ffmpeg", "-i", str(video), "-vf", "blackdetect=d=0.25:pix_th=0.02:pic_th=0.995", "-an", "-f", "null", "-"]).stderr
    frz = sh(["ffmpeg", "-i", str(video), "-vf", "freezedetect=n=0.002:d=2.5", "-an", "-f", "null", "-"]).stderr
    peak = sh(["ffmpeg", "-i", str(video), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"]).stderr
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", peak)
    hyp = list(tr["words"])
    if studio and sb.get("soundbites"):  # long-form Whisper drifts at a change of speaker and drops whole soundbites: re-hear each span alone
        from common import whisper
        for s in (x for x in scenes if str(x.get("id", "")).startswith("sb")):
            hyp = [x for x in hyp if not s["from"] + 0.3 <= x["s"] < s["to"] - 0.3]  # keep edge words, re-hear the clip itself
            wav = qa / f"{s['id']}.wav"
            sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{s['from']:.3f}", "-to", f"{s['to']:.3f}", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
            segs, _ = whisper().transcribe(str(wav), language=sb.get("language", "en"), word_timestamps=True, vad_filter=False)
            hyp += [{"w": x.word.strip(), "s": s["from"] + x.start} for g in segs for x in (g.words or [])]
            wav.unlink()
        hyp.sort(key=lambda x: x["s"])
    w = wer(script, [x["w"] for x in hyp]) if script else 0.0
    vr = load_json(prod / "out" / "voice-report.json") if (prod / "out" / "voice-report.json").exists() else {}  # rf voice listening gate

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
        ("voice_delivery", vr.get("gate", "PASS") == "PASS", ("; ".join(vr.get("fails", [])) or f"sentence pauses {vr.get('gap_sentence_median')}s, mid-gap p90 {vr.get('gap_mid_p90')}s") if vr else "no voice report (legacy take)", bool(vr)),
        ("music_bed", props["audio"].get("music") is not None, "music present" if props["audio"].get("music") else "no music bed (84% of corpus has one)", bool(spec.get("qa", {}).get("require_music"))),
    ]
    if studio:  # layered edit: judge the picture itself, not scene lengths (a full-frame presenter beat has no shot change)
        em = edit_metrics(video)
        from studio import presenter_windows
        pres = sum(b - a for a, b in presenter_windows(props["layouts"], props["durationSec"])) if props.get("presenter") else 0.0
        checks = [c for c in checks if c[0] not in ("longest_scene", "avg_scene")] + [
            ("edit_change_rate", em["changes_per_min"] >= 40, f"{em['changes_per_min']} big picture changes/min (references 48-129, floor 40)", True),
            ("edit_static", em["static_pct"] <= 3.0, f"{em['static_pct']}% static seconds (references 0-6%, max 3%)", True),
            ("edit_longest_still", em["longest_still_s"] <= 2, f"longest still stretch {em['longest_still_s']}s", False),
            ("presenter_share", not props.get("presenter") or 0.2 <= pres / props["durationSec"] <= 0.75, f"presenter on screen {pres:.1f}s of {props['durationSec']:.1f}s", False),
        ]
    ci = consistency_issues(sb)
    checks.append(("numbers_keyword_consistent", not ci, "; ".join(ci) or "numbers and CTA keyword agree across VO, screen and caption", False))
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
