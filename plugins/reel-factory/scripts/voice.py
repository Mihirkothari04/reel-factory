"""Voice-over + word timing for a production.

usage: rf voice <prod_dir> [--provider elevenlabs|edge] [--voice ID] [--speed 1.08]

Reads <prod>/storyboard.json (scenes[].vo), writes:
  public/vo.mp3      voice-over (leading/trailing silence trimmed)
  words.json         [{w, s, e, scene}]  — exact word timing mapped to scenes
Provider order: ElevenLabs (char-level timestamps, best voice) -> edge-tts (free) ; timing for edge comes from
local faster-whisper aligned back onto the script words (difflib), so captions always show the *script* spelling.
"""
import argparse, asyncio, base64, difflib, re, shutil
from pathlib import Path
from common import config, duration, eleven, eleven_ok, load_json, log, norm_tok, run, save_json, whisper


def script_words(scenes):
    """full text + per-word (text, scene_id, char_start, char_end)"""
    text, words = "", []
    for sc in scenes:
        vo = re.sub(r"\s+", " ", sc["vo"].strip())
        if text:
            text += " "
        base = len(text)
        for m in re.finditer(r"\S+", vo):
            words.append({"w": m.group(), "scene": sc["id"], "c0": base + m.start(), "c1": base + m.end()})
        text += vo
    return text, words


def tts_eleven(text, out, vcfg):
    payload = {"text": text, "model_id": vcfg.get("model_id", "eleven_v3"),
               "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.35, "speed": vcfg.get("speed", 1.08)}}
    d = eleven(["text-to-speech", "convert_with_timestamps", "--voice-id", vcfg["voice_id"], "--output-format", "mp3_44100_128"], payload)
    Path(out).write_bytes(base64.b64decode(d["audio_base64"]))
    a = d["alignment"]
    return list(zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]))


async def _edge(text, out, voice, rate):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(str(out))


def tts_edge(text, out, vcfg):
    pct = int(round((vcfg.get("speed", 1.08) - 1) * 100))
    asyncio.run(_edge(text, out, vcfg.get("edge_voice", "en-US-AndrewMultilingualNeural"), f"{pct:+d}%"))


def times_from_chars(words, chars):
    for w in words:
        seg = chars[w["c0"]:w["c1"]]
        w["s"], w["e"] = round(seg[0][1], 3), round(seg[-1][2], 3)


def times_from_asr(words, audio):
    segs, _ = whisper().transcribe(str(audio), word_timestamps=True, language=None, vad_filter=False)
    asr = [(x.word.strip(), x.start, x.end) for s in segs for x in (s.words or [])]
    a = [norm_tok(w["w"]) for w in words]
    b = [norm_tok(x[0]) for x in asr]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            words[blk.a + k]["s"], words[blk.a + k]["e"] = asr[blk.b + k][1], asr[blk.b + k][2]
    # interpolate any unmatched words between known neighbours
    if not any("s" in w for w in words):
        raise RuntimeError("alignment failed: no words matched")
    fill_gaps(words)


def fill_gaps(words):
    """spread runs of untimed words evenly between their timed neighbours"""
    n, i = len(words), 0
    while i < n:
        if "s" in words[i]:
            i += 1
            continue
        j = i
        while j < n and "s" not in words[j]:
            j += 1
        t0 = words[i - 1]["e"] if i > 0 else 0.0
        t1 = words[j]["s"] if j < n else t0 + 0.35 * (j - i)
        step = max(0.05, (t1 - t0) / (j - i))
        for k in range(i, j):
            words[k]["s"], words[k]["e"] = round(t0 + step * (k - i), 3), round(t0 + step * (k - i + 1), 3)
        i = j


def trim_lead(audio, words):
    """remove leading silence so the first word lands on frame ~0 (corpus: VO starts at 0.0s in 100% of reels)."""
    lead = max(0.0, words[0]["s"] - 0.05)
    if lead < 0.04:
        return
    tmp = Path(audio).with_suffix(".tmp.mp3")
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{lead:.3f}", "-i", audio, "-c:a", "libmp3lame", "-q:a", "2", tmp])
    tmp.replace(audio)
    for w in words:
        w["s"], w["e"] = round(w["s"] - lead, 3), round(w["e"] - lead, 3)


def tighten(audio, words, max_gap=0.22, keep=0.12, fade=0.01, floor_db=-38):
    """Editor-style pause cutting on REAL silence (ffmpeg silencedetect), so pauses hidden inside punctuation
    timing are caught too. Every silence longer than max_gap shrinks to `keep`; word timestamps are remapped.
    Corpus: ~87% speech coverage, pauses removed."""
    import numpy as np, soundfile as sf
    r = run(["ffmpeg", "-v", "info", "-i", audio, "-af", f"silencedetect=noise={floor_db}dB:d={max_gap}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    total = duration(audio)
    cuts = []
    for a, b in zip(starts, ends):
        if b >= total - 0.05:          # trailing silence: leave (render adds a tail)
            continue
        a2, b2 = a + keep / 2, b - keep / 2
        if b2 - a2 > 0.03:
            cuts.append((a2, b2))
    if not cuts:
        return 0.0
    wav = Path(audio).with_suffix(".tight.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", audio, "-ac", "1", "-ar", "44100", wav])
    x, sr = sf.read(wav)
    f = int(fade * sr)
    parts, last = [], 0
    for a2, b2 in cuts:
        seg = x[last:int(a2 * sr)].copy()
        if len(seg) > 2 * f:
            seg[-f:] *= np.linspace(1, 0, f)
            if parts:
                seg[:f] *= np.linspace(0, 1, f)
        parts.append(seg)
        last = int(b2 * sr)
    tail = x[last:].copy()
    if len(tail) > 2 * f:
        tail[:f] *= np.linspace(0, 1, f)
    parts.append(tail)
    sf.write(wav, np.concatenate(parts), sr)

    def remap(t):
        d = 0.0
        for a2, b2 in cuts:
            if t >= b2:
                d += b2 - a2
            elif t > a2:            # inside a cut: snap to the cut point
                return round(a2 - d, 3)
        return round(t - d, 3)

    for w in words:
        w["s"], w["e"] = remap(w["s"]), max(remap(w["e"]), remap(w["s"]) + 0.05)
    run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-c:a", "libmp3lame", "-q:a", "2", audio])
    wav.unlink()
    return sum(b2 - a2 for a2, b2 in cuts)


def retempo(audio, words, target_wpm=200, max_factor=1.18):
    """Pitch-preserving speed-up (ffmpeg atempo) toward target wpm, capped so the voice stays natural."""
    dur = duration(audio)
    wpm = len(words) / (dur / 60)
    factor = min(max_factor, target_wpm / wpm)
    if factor <= 1.02:
        return 1.0
    tmp = Path(audio).with_suffix(".tmp.mp3")
    run(["ffmpeg", "-y", "-v", "error", "-i", audio, "-filter:a", f"atempo={factor:.4f}", "-c:a", "libmp3lame", "-q:a", "2", tmp])
    tmp.replace(audio)
    for w in words:
        w["s"], w["e"] = round(w["s"] / factor, 3), round(w["e"] / factor, 3)
    return factor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prod")
    ap.add_argument("--provider")
    ap.add_argument("--voice")
    ap.add_argument("--speed", type=float)
    ap.add_argument("--retime", action="store_true", help="re-run pause cutting + tempo on the existing take (no new TTS)")
    ap.add_argument("--footage", help="presenter mode: the user's own recorded clip reading the script (its audio becomes the VO)")
    a = ap.parse_args()
    prod = Path(a.prod)
    sb = load_json(prod / "storyboard.json")
    if sb.get("meta", {}).get("mode") == "silent" or (sb.get("voice") or {}).get("none"):
        save_json(prod / "words.json", [])
        return log(prod, "voice: silent mode -> no voice-over (music + on-screen text carry the reel)")
    if a.footage:
        return footage(prod, sb, Path(a.footage))
    vcfg = dict(config().get("voice", {}))
    vcfg.update({k: v for k, v in (sb.get("voice") or {}).items() if v})
    out = prod / "public" / "vo.mp3"
    raw = prod / "public" / "vo_raw.mp3"
    if a.retime:
        if not raw.exists():
            raise SystemExit("no raw take saved (vo_raw.mp3); run voice without --retime first")
        shutil.copy2(raw, out)
        words = load_json(prod / "words_raw.json")
        return finish(prod, out, words, vcfg, "retime")
    if a.voice: vcfg["voice_id"] = a.voice
    if a.speed: vcfg["speed"] = a.speed
    provider = a.provider or vcfg.get("provider", "elevenlabs")
    text, words = script_words(sb["scenes"])
    out.parent.mkdir(parents=True, exist_ok=True)
    if provider == "elevenlabs" and eleven_ok() < len(text) + 200:
        log(prod, "voice: ElevenLabs unavailable or out of credits -> edge-tts fallback")
        provider = "edge"
    if provider == "elevenlabs":
        try:
            chars = tts_eleven(text, out, vcfg)
            if len(chars) != len(text):
                raise RuntimeError(f"alignment length {len(chars)} != text {len(text)}")
            times_from_chars(words, chars)
        except Exception as e:
            log(prod, f"voice: ElevenLabs failed ({str(e)[:160]}) -> edge-tts")
            provider = "edge"
    if provider == "edge":
        tts_edge(text, out, vcfg)
        times_from_asr(words, out)
    trim_lead(out, words)
    shutil.copy2(out, raw)
    save_json(prod / "words_raw.json", words)
    finish(prod, out, words, vcfg, provider)


def footage(prod, sb, clip):
    """Own-footage presenter: keep the take untouched (cutting audio would desync the face), align script words to it."""
    pub = prod / "public"
    pub.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-c:v", "libx264", "-crf", "18", "-an", "-movflags", "+faststart", pub / "avatar.mp4"])
    run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-vn", "-ac", "1", "-ar", "44100", "-b:a", "192k", pub / "vo.mp3"])
    _, words = script_words(sb["scenes"])
    times_from_asr(words, pub / "vo.mp3")
    save_json(prod / "words.json", [{"w": w["w"], "s": w["s"], "e": w["e"], "scene": w["scene"]} for w in words])
    sb.setdefault("avatar", {})["src"] = "avatar.mp4"
    sb["meta"]["layout"] = "split-avatar"
    save_json(prod / "storyboard.json", sb)
    dur = duration(pub / "vo.mp3")
    log(prod, f"voice: own footage {clip.name} · {len(words)} words · {dur:.1f}s · {len(words) / (dur / 60):.0f} wpm · first word {words[0]['s']:.2f}s (trim the clip if > 0.3s)")


def finish(prod, out, words, vcfg, provider):
    cut = tighten(out, words, max_gap=vcfg.get("max_gap", 0.22))
    factor = retempo(out, words, target_wpm=vcfg.get("target_wpm", 200), max_factor=vcfg.get("max_tempo", 1.18))
    dur = duration(out)
    save_json(prod / "words.json", [{"w": w["w"], "s": w["s"], "e": w["e"], "scene": w["scene"]} for w in words])
    wpm = len(words) / (dur / 60)
    log(prod, f"voice: {provider} · {len(words)} words · {dur:.1f}s · {wpm:.0f} wpm · pauses cut {cut:.1f}s · tempo x{factor:.2f}")
    if not 165 <= wpm <= 245:
        log(prod, f"voice WARNING: {wpm:.0f} wpm outside 165-245 target (corpus median 204)")


if __name__ == "__main__":
    main()
