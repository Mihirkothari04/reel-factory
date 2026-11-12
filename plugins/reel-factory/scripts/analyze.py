"""Reference-reel analysis (also used by QA on our own renders).

usage: rf analyze <out_dir> <video> [<video> ...]
Writes <out_dir>/<slug>/{metrics.json, transcript.json, transcript.txt, sheet.jpg}:
duration, resolution, scene cuts, EBU R128 loudness, music-bed level in speech gaps, word-timed transcript
(faster-whisper, local GPU), WPM, speech ratio, first-word time, and a 20-frame contact sheet weighted to the hook.
Feed the sheets + transcripts to Claude to extract new patterns (the /reel-learn command).
"""
import json, re, subprocess, sys, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from common import whisper


def sh(args, text=True):
    return subprocess.run(args, capture_output=True, text=text, encoding="utf-8" if text else None, errors="replace" if text else None)


def slug(p: Path) -> str:
    m = re.search(r"\[([A-Za-z0-9_-]{8,})\]", p.name)
    base = m.group(1) if m else re.sub(r"[^A-Za-z0-9]+", "_", p.stem)[:40]
    return base + "_" + hashlib.md5(str(p).encode()).hexdigest()[:4]


def probe(p):
    j = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)]).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    return dict(dur=round(float(j["format"]["duration"]), 2), w=v["width"], h=v["height"],
                fps=round(num / den, 2), has_audio=a is not None)


def cuts(p, thr=0.3):
    r = sh(["ffmpeg", "-i", str(p), "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"])
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def loudness(p):
    r = sh(["ffmpeg", "-i", str(p), "-af", "ebur128", "-vn", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def audio(p):
    raw = sh(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], text=False).stdout
    return np.frombuffer(raw, np.float32)


def transcribe(p, language=None):
    segs, info = whisper().transcribe(str(p), word_timestamps=True, vad_filter=True, language=language)
    words = [dict(w=w.word.strip(), s=round(w.start, 2), e=round(w.end, 2)) for s in segs for w in (s.words or [])]
    return dict(lang=info.language, lang_p=round(info.language_probability, 2), words=words)


def bed_level(x, words, sr=16000):
    """Median RMS dBFS of frames with no speech -> proxy for music/SFX bed under the VO."""
    if len(x) == 0:
        return None, None
    hop = sr // 10
    rms = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "valid")[::hop] + 1e-12)
    db = 20 * np.log10(rms)
    speech = np.zeros(len(db), bool)
    for w in words:
        speech[int(w["s"] * 10):int(w["e"] * 10) + 1] = True
    gap = db[~speech] if (~speech).any() else db
    return round(float(np.median(gap)), 1), round(float(np.median(db[speech])), 1) if speech.any() else None


def frame(p, t, w=216, h=384):
    raw = sh(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1",
              "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], text=False).stdout
    if len(raw) != w * h * 3:
        return Image.new("RGB", (w, h))
    return Image.frombuffer("RGB", (w, h), raw)


def sheet(p, dur, path):
    hook = [0, 0.5, 1.0, 1.7, 2.5]
    rest = list(np.linspace(3, max(dur - 0.3, 3.1), 15))
    ts = hook + rest
    img = Image.new("RGB", (216 * 5, 384 * 4), "black")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for i, t in enumerate(ts):
        x, y = (i % 5) * 216, (i // 5) * 384
        img.paste(frame(p, min(t, dur - 0.05)), (x, y))
        d.rectangle([x, y, x + 62, y + 22], fill="black")
        d.text((x + 3, y + 1), f"{t:5.1f}s", fill="yellow", font=font)
    img.save(path, quality=82)


def analyze(v: Path, out_dir: Path, language=None, force=False):
    if True:
        o = out_dir / slug(v)
        if (o / "metrics.json").exists() and not force:
            print("skip", o.name); return o
        o.mkdir(parents=True, exist_ok=True)
        m = dict(file=str(v), **probe(v))
        c = cuts(v)
        m.update(cuts=c, n_cuts=len(c), first_cut=c[0] if c else None,
                 avg_shot=round(m["dur"] / (len(c) + 1), 2), lufs=loudness(v) if m["has_audio"] else None)
        tr = transcribe(v, language) if m["has_audio"] else dict(lang=None, words=[])
        words = tr["words"]
        speech_t = sum(w["e"] - w["s"] for w in words)
        m.update(n_words=len(words), wpm=round(len(words) / (m["dur"] / 60), 1),
                 speech_ratio=round(speech_t / m["dur"], 2),
                 first_word_at=words[0]["s"] if words else None,
                 hook_text=" ".join(w["w"] for w in words if w["s"] < 3.0),
                 lang=tr["lang"])
        m["bed_db"], m["speech_db"] = bed_level(audio(v), words) if m["has_audio"] else (None, None)
        (o / "transcript.json").write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")
        (o / "transcript.txt").write_text(" ".join(w["w"] for w in words), encoding="utf-8")
        sheet(v, m["dur"], o / "sheet.jpg")
        (o / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        print("done", o.name, m["dur"], "s", m["n_cuts"], "cuts", m["wpm"], "wpm", flush=True)
        return o


def main():
    out = Path(sys.argv[1])
    for v in map(Path, sys.argv[2:]):
        analyze(v, out)


if __name__ == "__main__":
    main()
