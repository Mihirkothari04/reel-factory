"""Voice-over + word timing for a production (voice pipeline v2).

usage: rf voice <prod_dir> [--provider elevenlabs|edge] [--voice ID] [--model ID]
       rf voice <prod_dir> --retime            re-shape pauses on the saved raw take (no new TTS)
       rf voice <prod_dir> --regen p3 [p5..]   regenerate only these narration paragraphs, keep the rest
       rf voice <prod_dir> --report            listening report on the current take (no TTS)
       rf voice <prod_dir> --footage clip.mp4  presenter mode with the owner's own recording

Script source (storyboard.json), in order of preference:
  narration: [{id, role, text, tts?}]  spoken paragraphs written FIRST (speechwriting.md); `tts` = the same words
             with delivery markup (audio tags, ellipses, CAPS emphasis); scenes then attach by `cue` (a phrase of
             the narration where the scene starts), so cuts can land mid-sentence like the corpus.
  scenes[].vo                           legacy: one fragment per scene (still accepted).
Pipeline: paragraphs grouped into segments (≤ ~900 chars) → ElevenLabs with previous_text/next_text stitching and
char timestamps (edge-tts free fallback, timed by local Whisper) → segments joined with paragraph pauses → pauses
shaped by linguistic boundary (sentence / comma / paragraph / mid-phrase glitch) toward corpus targets → optional
tempo nudge (≤ max_tempo, only if over the length budget) → listening report (out/voice-report.md) with a gate.
Writes public/vo.mp3, words.json [{w, s, e, scene, para}], public/vo_raw.mp3 + words_raw.json + segments.json.
"""
import argparse, asyncio, base64, difflib, json, re
from pathlib import Path
from common import config, duration, eleven, eleven_ok, load_json, log, norm_tok, run, save_json, wer_score, whisper

TAG = re.compile(r"\[[^\]]{1,40}\]")
# corpus targets (89 English reference reels, medians/IQR): see references/voice.md
PAUSE = {"para": (0.34, 0.50), "sent": (0.18, 0.32), "comma": (0.10, 0.22), "mid": (0.0, 0.08)}
# per-structure pause profiles (corpus by mode: presenters/news pause least, story narrators most)
PAUSE_BY_MODE = {
    "presenter": {"para": (0.22, 0.34), "sent": (0.12, 0.22), "comma": (0.06, 0.16), "mid": (0.0, 0.08)},
    "newsroom": {"para": (0.24, 0.36), "sent": (0.14, 0.24), "comma": (0.08, 0.18), "mid": (0.0, 0.08)},
    "quicktake": {"para": (0.24, 0.36), "sent": (0.14, 0.24), "comma": (0.08, 0.18), "mid": (0.0, 0.08)},
    "story": {"para": (0.40, 0.60), "sent": (0.22, 0.38), "comma": (0.12, 0.24), "mid": (0.0, 0.08)},
}


# ---------- script model ----------

def paragraphs(sb):
    """[{id, text, tts}] from storyboard.narration, or one paragraph per legacy scene vo"""
    if sb.get("narration"):
        return [{"id": p.get("id") or f"p{i + 1}", "text": re.sub(r"\s+", " ", p["text"].strip()),
                 "tts": re.sub(r"\s+", " ", (p.get("tts") or p["text"]).strip())} for i, p in enumerate(sb["narration"])]
    return [{"id": sc["id"], "text": re.sub(r"\s+", " ", sc["vo"].strip()), "tts": re.sub(r"\s+", " ", (sc.get("tts") or sc["vo"]).strip()), "scene": sc["id"]}
            for sc in sb["scenes"]]


def display_words(paras):
    return [{"w": m.group(), "para": p["id"]} for p in paras for m in re.finditer(r"\S+", p["text"])]


def assign_scenes(sb, words):
    """scene of every word: legacy = its paragraph; narration mode = from each scene's `cue` phrase onward"""
    if not sb.get("narration"):
        for w in words:
            w["scene"] = w["para"]
        return
    toks = [norm_tok(w["w"]) for w in words]
    pos, starts = 0, []
    for i, sc in enumerate(sb["scenes"]):
        cue = [norm_tok(t) for t in (sc.get("cue") or "").split() if norm_tok(t)]
        if not cue:
            if i == 0:
                starts.append(0); continue
            raise SystemExit(f"voice: scene {sc['id']} has no `cue` (narration mode needs one per scene after the first)")
        hit = next((j for j in range(pos, len(toks) - len(cue) + 1) if toks[j:j + len(cue)] == cue), None)
        if hit is None:
            raise SystemExit(f"voice: cue for {sc['id']} not found after word {pos}: \"{sc.get('cue')}\" (must quote the narration, in order)")
        starts.append(hit)
        pos = hit + 1
    for k, sc in enumerate(sb["scenes"]):
        end = starts[k + 1] if k + 1 < len(starts) else len(words)
        for w in words[starts[k]:end]:
            w["scene"] = sc["id"]


def boundary(word, next_para_change):
    t = word["w"]
    if next_para_change:
        return "para"
    if re.search(r"(\.\.\.|…)$", t):  # ellipsis = a held beat, like a sentence end
        return "sent"
    if re.search(r"[.?!][\"')\]]?$", t):
        return "sent"
    if re.search(r"[,;:—–]$", t) or t in ("—", "–", "-"):
        return "comma"
    return "mid"


def segments(paras, max_chars=900):
    """group paragraphs into TTS segments (whole paragraphs only: never split a thought)"""
    segs, cur = [], []
    for p in paras:
        if cur and sum(len(x["tts"]) for x in cur) + len(p["tts"]) > max_chars:
            segs.append(cur); cur = []
        cur.append(p)
    if cur:
        segs.append(cur)
    return segs


def apply_lexicon(text, lex):
    for k, v in (lex or {}).items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text)
    return text


# ---------- TTS providers ----------

def tts_eleven(text, out, vcfg, prev="", nxt=""):
    model = vcfg.get("model_id", "eleven_v4")
    vs = {"stability": vcfg.get("stability", 0.5), "similarity_boost": vcfg.get("similarity_boost", 0.75)}
    if not model.startswith("eleven_v4"):
        vs.update({"style": vcfg.get("style", 0.3), "use_speaker_boost": True})
        if vcfg.get("speed"):
            vs["speed"] = vcfg["speed"]
    payload = {"text": text, "model_id": model, "voice_settings": vs, "apply_text_normalization": vcfg.get("normalize", "auto"),
               "language_code": vcfg.get("language", "en")}
    if prev:
        payload["previous_text"] = prev
    if nxt:
        payload["next_text"] = nxt
    d = eleven(["text-to-speech", "convert_with_timestamps", "--voice-id", vcfg["voice_id"], "--output-format", "mp3_44100_192"], payload)
    Path(out).write_bytes(base64.b64decode(d["audio_base64"]))
    a = d.get("normalized_alignment") or d["alignment"]
    return list(zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]))


async def _edge(text, out, voice, rate):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate).save(str(out))


def tts_edge(text, out, vcfg):
    pct = int(round((vcfg.get("speed", 1.0) - 1) * 100))
    asyncio.run(_edge(TAG.sub("", text), out, vcfg.get("edge_voice", "en-US-AndrewMultilingualNeural"), f"{pct:+d}%"))


# ---------- alignment ----------

def times_from_chars(dwords, chars):
    """map display words onto the spoken text's char timings: tags are skipped, tokens matched by normalised form"""
    text = "".join(c for c, _, _ in chars)
    spoken, i = [], 0
    for m in re.finditer(r"\[[^\]]{1,40}\]|\S+", text):
        if m.group().startswith("["):
            continue
        tok = norm_tok(m.group())
        if tok:
            spoken.append((tok, chars[m.start()][1], chars[m.end() - 1][2]))
    a = [norm_tok(w["w"]) for w in dwords]
    b = [t for t, _, _ in spoken]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            dwords[blk.a + k]["s"], dwords[blk.a + k]["e"] = round(spoken[blk.b + k][1], 3), round(spoken[blk.b + k][2], 3)
    hit = sum("s" in w for w in dwords)
    if hit < 0.8 * len(dwords):
        raise RuntimeError(f"alignment matched only {hit}/{len(dwords)} words")
    fill_gaps(dwords)


def times_from_asr(words, audio):
    segs, _ = whisper().transcribe(str(audio), word_timestamps=True, language=None, vad_filter=False)
    asr = [(x.word.strip(), x.start, x.end) for s in segs for x in (s.words or [])]
    a = [norm_tok(w["w"]) for w in words]
    b = [norm_tok(x[0]) for x in asr]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            words[blk.a + k]["s"], words[blk.a + k]["e"] = asr[blk.b + k][1], asr[blk.b + k][2]
    if not any("s" in w for w in words):
        raise RuntimeError("alignment failed: no words matched")
    fill_gaps(words)
    return asr


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


# ---------- audio editing ----------

def load_wav(path, sr=44100):
    import soundfile as sf
    wav = Path(path).with_suffix(".work.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), wav])
    x, _ = sf.read(wav)
    wav.unlink()
    return x


def save_audio(x, path, sr=44100):
    import soundfile as sf
    wav = Path(path).with_suffix(".work.wav")
    sf.write(wav, x, sr)
    run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k", path])
    wav.unlink()


def trim_edges(x, words, sr=44100, keep=0.04):
    """cut leading silence (first word lands on frame ~0) and trailing silence of a segment"""
    s0 = max(0.0, words[0]["s"] - keep)
    e1 = min(len(x) / sr, words[-1]["e"] + 0.12)
    for w in words:
        w["s"], w["e"] = round(w["s"] - s0, 3), round(w["e"] - s0, 3)
    return x[int(s0 * sr):int(e1 * sr)]


def silences(x, sr=44100, floor_db=-38.0, min_len=0.05):
    """real silent stretches [(a, b)] in seconds (10 ms RMS frames below floor_db)"""
    import numpy as np
    hop = int(0.01 * sr)
    n = len(x) // hop
    if n == 0:
        return []
    db = 20 * np.log10(np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
    out, start = [], None
    for k, q in enumerate(db < floor_db):
        if q and start is None:
            start = k
        if not q and start is not None:
            if (k - start) * 0.01 >= min_len:
                out.append((start * 0.01, k * 0.01))
            start = None
    if start is not None and (n - start) * 0.01 >= min_len:
        out.append((start * 0.01, n * 0.01))
    return out


def pause_map(x, words, sr=44100):
    """boundary index -> longest real silence (a, b) between word i and i+1 (timestamps are coarse; audio decides)"""
    m = {}
    for a, b in silences(x, sr):
        mid = (a + b) / 2
        i = max((k for k in range(len(words)) if words[k]["s"] <= mid), default=-1)
        if 0 <= i < len(words) - 1 and mid < words[i + 1]["e"]:
            if i not in m or (b - a) > (m[i][1] - m[i][0]):
                m[i] = (a, b)
    return m


def shape_pauses(x, words, sr=44100, targets=PAUSE, fade=0.008):
    """Set the real silence at every word boundary to that boundary's corpus range: shrink over-long pauses (incl.
    glitch pauses inside phrases), add air where a sentence/paragraph end has none. Words are never cut."""
    import numpy as np
    pm = pause_map(x, words, sr)
    edits = []  # (time, delta): delta>0 insert silence at time; delta<0 remove [time, time-delta]
    for i in range(len(words) - 1):
        kind = boundary(words[i], words[i + 1]["para"] != words[i]["para"])
        lo, hi = targets[kind]
        mid_t = (lo + hi) / 2 if kind != "mid" else 0.04
        if i in pm:
            a, b = pm[i]
            length = b - a
            if length > hi:
                edits.append((a + mid_t / 2, -(length - mid_t)))
            elif length < lo and kind in ("sent", "para"):
                edits.append(((a + b) / 2, mid_t - length))
        elif kind in ("sent", "para"):
            lo_t, hi_t = words[i]["e"] - 0.05, words[i + 1]["s"] + 0.05
            seg = x[int(max(0, lo_t) * sr):int(hi_t * sr)]
            hop = int(0.01 * sr)
            if len(seg) >= hop:
                n = len(seg) // hop
                k = int(np.argmin(np.sqrt(np.mean(seg[: n * hop].reshape(n, hop) ** 2, axis=1))))
                edits.append((max(0, lo_t) + (k + 0.5) * 0.01, mid_t))
    edits.sort()
    if not edits:
        return x, []
    f = int(fade * sr)
    out, last, kept = [], 0, []
    for t, d in edits:
        cut = int(t * sr)
        if cut < last:
            continue
        kept.append((t, d))
        piece = x[last:cut].copy()
        if len(piece) > 2 * f:
            piece[-f:] *= np.linspace(1, 0, f)
            if out:
                piece[:f] *= np.linspace(0, 1, f)
        out.append(piece)
        if d > 0:
            out.append(np.zeros(int(d * sr)))
            last = cut
        else:
            last = cut + int(-d * sr)
    tail = x[last:].copy()
    if len(tail) > 2 * f and out:
        tail[:f] *= np.linspace(0, 1, f)
    out.append(tail)

    def remap(tt):
        off = 0.0
        for et, d in kept:
            if d > 0 and tt >= et:
                off += d
            elif d < 0 and tt >= et - d:
                off += d
            elif d < 0 and tt > et:
                return et + off
        return tt + off

    for w in words:
        w["s"], w["e"] = round(remap(w["s"]), 3), round(max(remap(w["e"]), remap(w["s"]) + 0.04), 3)
    return np.concatenate(out), kept


def articulation(x, words, sr=44100):
    """words per minute of actual speech time (real silences excluded)"""
    sil = sum(b - a for a, b in silences(x, sr))
    return len(words) / max(1e-6, len(x) / sr - sil) * 60


def tempo_array(x, words, factor, sr=44100):
    """pitch-preserving time-scale of an in-memory take (ffmpeg atempo); word times scaled"""
    import soundfile as sf, tempfile, os
    if factor <= 1.005:
        return x
    d = tempfile.mkdtemp()
    a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
    sf.write(a, x, sr)
    run(["ffmpeg", "-y", "-v", "error", "-i", a, "-filter:a", f"atempo={factor:.4f}", b])
    y, _ = sf.read(b)
    for w in words:
        w["s"], w["e"] = round(w["s"] / factor, 3), round(w["e"] / factor, 3)
    return y


# ---------- listening report ----------

def report(prod, words, audio, seg_bounds, mode, asr=None):
    """Corpus-comparable narration metrics + join continuity + script/ASR diff → out/voice-report.{md,json}; gate."""
    import numpy as np, statistics as st
    gaps = {"sent": [], "comma": [], "mid": [], "para": []}
    sents, cur = [], 0
    pm = pause_map(load_wav(audio), words)  # real silences, not coarse timestamp gaps
    for i, w in enumerate(words):
        cur += 1
        k = boundary(w, i + 1 < len(words) and words[i + 1]["para"] != w["para"])
        if k in ("sent", "para") or i == len(words) - 1:
            sents.append(cur); cur = 0
        if i + 1 < len(words):
            gaps[k].append(round(pm[i][1] - pm[i][0], 3) if i in pm else 0.0)
    med = lambda xs: round(st.median(xs), 3) if xs else None
    p90 = lambda xs: round(sorted(xs)[int(0.9 * (len(xs) - 1))], 3) if xs else None
    dur = duration(audio)
    speech = dur - sum(b - a for a, b in silences(load_wav(audio)))
    x = load_wav(audio)
    joins = []

    def voiced_db(t0, t1):  # loudness of speech only (10 ms frames above the silence floor)
        y = x[max(0, int(t0 * 44100)):int(t1 * 44100)]
        n = len(y) // 441
        if n == 0:
            return None
        fr = np.sqrt(np.mean(y[: n * 441].reshape(n, 441) ** 2, axis=1))
        fr = fr[20 * np.log10(fr + 1e-9) > -38]
        return 20 * np.log10(float(np.mean(fr)) + 1e-9) if len(fr) else None

    for i in range(1, len(words)):
        if words[i].get("seg") is not None and words[i]["seg"] != words[i - 1].get("seg"):
            a_db, b_db = voiced_db(words[i - 1]["e"] - 1.5, words[i - 1]["e"]), voiced_db(words[i]["s"], words[i]["s"] + 1.5)
            if a_db is not None and b_db is not None:
                joins.append(round(abs(a_db - b_db), 1))
    if asr is None:
        segs, _ = whisper().transcribe(str(audio), word_timestamps=True, language=None, vad_filter=False)
        asr = [(x2.word.strip(), x2.start, x2.end) for s in segs for x2 in (s.words or [])]
    a_t = [norm_tok(w["w"]) for w in words]
    b_t = [norm_tok(t) for t, _, _ in asr]
    sm = difflib.SequenceMatcher(a=a_t, b=b_t, autojunk=False)
    wer = wer_score([w["w"] for w in words], [t for t, _, _ in asr])  # numbers/hyphens normalised (common.wer_tokens)
    misheard = [" ".join(w["w"] for w in words[i1:i2]) + " → " + " ".join(t for t, _, _ in asr[j1:j2])
                for op, i1, i2, j1, j2 in sm.get_opcodes() if op == "replace" and i2 - i1 <= 3][:12]
    m = {"duration": round(dur, 2), "wpm": round(len(words) / dur * 60), "artic_wpm": round(len(words) / max(1e-6, speech) * 60),
         "sentence_len_median": med(sents), "long_sentence_share": round(sum(s >= 16 for s in sents) / max(1, len(sents)), 2),
         "gap_sentence_median": med(gaps["sent"]), "gap_comma_median": med(gaps["comma"]), "gap_paragraph_median": med(gaps["para"]),
         "gap_mid_p90": p90(gaps["mid"]), "join_loudness_jump_db": joins, "wer": round(wer, 3), "misheard": misheard}
    rng = {"kinetic": (195, 245), "presenter": (175, 250),  # batch-03 presenters: 167-255 wpm
           "story": (175, 225), "quicktake": (165, 230), "silent": (0, 999)}.get(mode, (180, 245))
    fails = []
    if m["gap_sentence_median"] is not None and not 0.14 <= m["gap_sentence_median"] <= 0.40:
        fails.append(f"sentence pauses {m['gap_sentence_median']} s (target 0.18–0.32)")
    if (m["gap_mid_p90"] or 0) > 0.15:
        fails.append(f"mid-phrase gaps p90 {m['gap_mid_p90']} s (glitch pauses inside thoughts)")
    if not rng[0] <= m["wpm"] <= rng[1]:
        fails.append(f"{m['wpm']} wpm outside {rng} for {mode}")
    if any(j > 6 for j in joins):
        fails.append(f"loudness jump at a segment join {max(joins)} dB")
    if wer > 0.08:
        fails.append(f"WER {wer:.0%}: unclear or mispronounced words")
    m["gate"] = "PASS" if not fails else "FAIL"
    m["fails"] = fails
    out = Path(prod) / "out"
    out.mkdir(exist_ok=True)
    save_json(out / "voice-report.json", m)
    lines = ["# Voice report", "", f"**{m['gate']}** " + ("; ".join(fails) if fails else "(all targets met)"), "",
             "| metric | take | corpus target |", "|---|---|---|",
             f"| wpm (incl. pauses) | {m['wpm']} | {rng[0]}–{rng[1]} |", f"| articulation wpm | {m['artic_wpm']} | ~238 |",
             f"| sentence length median | {m['sentence_len_median']} | ~15 (12–18) |", f"| long sentences (≥16) | {m['long_sentence_share']} | ~0.48 |",
             f"| sentence pause median | {m['gap_sentence_median']} s | 0.24 (0.16–0.30) |", f"| comma pause median | {m['gap_comma_median']} s | 0.22 |",
             f"| paragraph pause median | {m['gap_paragraph_median']} s | 0.34–0.50 |", f"| mid-phrase gap p90 | {m['gap_mid_p90']} s | ≤ 0.08 |",
             f"| segment-join loudness jumps | {joins} dB | ≤ 6 |", f"| WER vs script | {m['wer']:.1%} | ≤ 8% |", "",
             "Possibly misheard (script → ASR): " + ("; ".join(misheard) if misheard else "none")]
    (out / "voice-report.md").write_text("\n".join(lines), encoding="utf-8")
    return m


# ---------- main ----------

def generate(prod, sb, vcfg, provider, only=None):
    """TTS per segment (stitched), aligned to display words; returns (audio array, words, segment boundaries)"""
    import numpy as np
    paras = paragraphs(sb)
    lex = vcfg.get("lexicon") or {}
    lex.update(sb.get("lexicon") or {})
    work = prod / "public" / "vo_segments"
    work.mkdir(parents=True, exist_ok=True)
    segs = segments(paras, vcfg.get("segment_chars", 900))
    old = load_json(prod / "segments.json") if only and (prod / "segments.json").exists() else {}
    pieces, all_words, bounds, meta = [], [], [], {}
    for k, seg in enumerate(segs):
        sid = "+".join(p["id"] for p in seg)
        text = " ".join(apply_lexicon(p["tts"], lex) for p in seg)
        dwords = display_words(seg)
        f = work / f"{k:02d}.mp3"
        reuse = only and not any(p["id"] in only for p in seg) and old.get(sid) and f.exists()
        if reuse:
            for w, t in zip(dwords, old[sid]["words"]):
                w["s"], w["e"] = t
        else:
            prev = " ".join(p["text"] for s2 in segs[:k] for p in s2)[-600:]
            nxt = " ".join(p["text"] for s2 in segs[k + 1:] for p in s2)[:600]
            if provider == "elevenlabs":
                try:
                    times_from_chars(dwords, tts_eleven(text, f, vcfg, prev, nxt))
                except Exception as e:
                    log(prod, f"voice: ElevenLabs failed on segment {sid} ({str(e)[:160]}) -> edge-tts")
                    provider = "edge"
            if provider == "edge":
                tts_edge(text, f, vcfg)
                times_from_asr(dwords, f)
        meta[sid] = {"words": [[w["s"], w["e"]] for w in dwords]}
        for w in dwords:
            w["seg"] = k
        x = load_wav(f)
        x = trim_edges(x, dwords)
        if pieces:
            gap = vcfg.get("paragraph_pause", 0.40)
            pieces.append(np.zeros(int(gap * 44100)))
        off = sum(len(p) for p in pieces) / 44100
        bounds.append(off)
        for w in dwords:
            w["s"], w["e"] = round(w["s"] + off, 3), round(w["e"] + off, 3)
        pieces.append(x)
        all_words += dwords
    save_json(prod / "segments.json", meta)
    return np.concatenate(pieces), all_words, bounds[1:], provider


def finish(prod, sb, x, words, bounds, vcfg, provider):
    out = prod / "public" / "vo.mp3"
    art0 = articulation(x, words)
    mode = (sb.get("meta") or {}).get("mode", "kinetic")
    target = {"presenter": 252, "newsroom": 250, "quicktake": 250, "story": 225, "cinematic": 235}.get(mode, vcfg.get("target_articulation", 245))
    factor = min(vcfg.get("max_tempo", 1.18), max(1.0, target / art0))
    x = tempo_array(x, words, factor)  # creators speak ~238 wpm of speech; slow voices are nudged, never past max_tempo
    bounds = [b / factor for b in bounds]
    x, edits = shape_pauses(x, words, targets=PAUSE_BY_MODE.get(mode, PAUSE))
    save_audio(x, out)
    budget = (sb.get("meta") or {}).get("max_seconds") or vcfg.get("max_seconds")
    if budget and duration(out) > budget * 1.02:
        log(prod, f"voice WARNING: {duration(out):.1f}s exceeds the {budget}s budget: trim the narration (speechwriting), never speed up further")
    removed = -sum(d for _, d in edits if d < 0)
    added = sum(d for _, d in edits if d > 0)
    save_json(prod / "words.json", [{"w": w["w"], "s": w["s"], "e": w["e"], "scene": w["scene"], "para": w["para"]} for w in words])
    m = report(prod, words, out, bounds, (sb.get("meta") or {}).get("mode", "kinetic"))
    log(prod, f"voice: {provider} · {len(words)} words · {m['duration']:.1f}s · {m['wpm']} wpm · articulation {art0:.0f}->{m['artic_wpm']} (x{factor:.2f}) · "
              f"pauses -{removed:.1f}s/+{added:.1f}s · sentence pause {m['gap_sentence_median']}s · WER {m['wer']:.1%} · gate {m['gate']}"
              + (f" ({'; '.join(m['fails'])})" if m["fails"] else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prod")
    ap.add_argument("--provider")
    ap.add_argument("--voice")
    ap.add_argument("--model")
    ap.add_argument("--retime", action="store_true", help="re-shape pauses on the saved raw take (no new TTS)")
    ap.add_argument("--regen", nargs="+", help="regenerate only these narration paragraph ids")
    ap.add_argument("--report", action="store_true", help="listening report on the current take")
    ap.add_argument("--footage", help="presenter mode: the owner's own recorded clip reading the script")
    a = ap.parse_args()
    prod = Path(a.prod)
    sb = load_json(prod / "storyboard.json")
    if sb.get("meta", {}).get("mode") == "silent" or (sb.get("voice") or {}).get("none"):
        save_json(prod / "words.json", [])
        return log(prod, "voice: silent mode -> no voice-over (music + on-screen text carry the reel)")
    if a.footage:
        return footage(prod, sb, Path(a.footage))
    vcfg = dict(config().get("voice", {}))
    vcfg.update({k: v for k, v in (sb.get("voice") or {}).items() if v not in (None, "")})
    if a.voice: vcfg["voice_id"] = a.voice
    if a.model: vcfg["model_id"] = a.model
    if a.report:
        words = load_json(prod / "words.json")
        m = report(prod, words, prod / "public" / "vo.mp3", [], sb.get("meta", {}).get("mode", "kinetic"))
        return print(json.dumps(m, indent=2, ensure_ascii=False))
    raw = prod / "public" / "vo_raw.wav"
    if a.retime:
        if not raw.exists():
            raise SystemExit("no raw take saved; run voice without --retime first")
        import soundfile as sf
        x, _ = sf.read(raw)
        r = load_json(prod / "words_raw.json")
        assign_scenes(sb, r["words"])  # cues may have changed since the take: re-map scenes, no new TTS
        return finish(prod, sb, x, r["words"], r["bounds"], vcfg, "retime")
    if a.regen:
        bad = set(a.regen) - {p["id"] for p in paragraphs(sb)}
        if bad:  # e.g. "p2,p3" as one token would otherwise regenerate nothing and leave stale audio
            raise SystemExit(f"--regen: unknown paragraph id(s) {sorted(bad)}; pass ids separated by spaces, e.g. --regen p2 p3")
    provider = a.provider or vcfg.get("provider", "elevenlabs")
    chars = sum(len(p["tts"]) for p in paragraphs(sb))
    if provider == "elevenlabs" and eleven_ok() < chars + 200:
        log(prod, "voice: ElevenLabs unavailable or out of credits -> edge-tts fallback")
        provider = "edge"
    x, words, bounds, provider = generate(prod, sb, vcfg, provider, only=set(a.regen) if a.regen else None)
    assign_scenes(sb, words)
    import soundfile as sf
    sf.write(raw, x, 44100)
    save_json(prod / "words_raw.json", {"words": words, "bounds": bounds})
    finish(prod, sb, x, [dict(w) for w in words], bounds, vcfg, provider)


def footage(prod, sb, clip):
    """Own-footage presenter: keep the take untouched (cutting audio would desync the face), align script words to it."""
    pub = prod / "public"
    pub.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-c:v", "libx264", "-crf", "18", "-an", "-movflags", "+faststart", pub / "avatar.mp4"])
    run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-vn", "-ac", "1", "-ar", "44100", "-b:a", "192k", pub / "vo.mp3"])
    words = display_words(paragraphs(sb))
    times_from_asr(words, pub / "vo.mp3")
    assign_scenes(sb, words)
    save_json(prod / "words.json", [{"w": w["w"], "s": w["s"], "e": w["e"], "scene": w["scene"], "para": w["para"]} for w in words])
    sb.setdefault("avatar", {})["src"] = "avatar.mp4"
    sb["meta"]["layout"] = "split-avatar"
    save_json(prod / "storyboard.json", sb)
    dur = duration(pub / "vo.mp3")
    log(prod, f"voice: own footage {clip.name} · {len(words)} words · {dur:.1f}s · {len(words) / (dur / 60):.0f} wpm · first word {words[0]['s']:.2f}s (trim the clip if > 0.3s)")


def selftest():
    import numpy as np
    sr = 44100
    w = [{"w": "Hello", "s": 0.0, "e": 0.3, "para": "p1"}, {"w": "world.", "s": 0.31, "e": 0.6, "para": "p1"},
         {"w": "Next", "s": 0.61, "e": 0.9, "para": "p1"}, {"w": "thing,", "s": 1.6, "e": 1.9, "para": "p1"},
         {"w": "new", "s": 2.6, "e": 2.9, "para": "p2"}]
    x = np.zeros(int(3.0 * sr))
    for q in w:  # voiced word = tone, gaps = digital silence
        i0, i1 = int(q["s"] * sr), int(q["e"] * sr)
        x[i0:i1] = 0.3 * np.sin(np.arange(i1 - i0) * 0.05)
    y, edits = shape_pauses(x, w)
    pm = pause_map(y, w)
    g = lambda i: (pm[i][1] - pm[i][0]) if i in pm else 0.0
    assert PAUSE["sent"][0] - 0.02 <= g(1) <= PAUSE["sent"][1] + 0.02, (g(1), w)  # sentence end gets air
    assert g(2) <= PAUSE["mid"][1] + 0.02, (g(2), w)                              # glitch pause inside a phrase shrunk
    assert PAUSE["para"][0] - 0.02 <= g(3) <= PAUSE["para"][1] + 0.02, (g(3), w)  # paragraph pause in range
    dw = [{"w": "It's", "para": "p"}, {"w": "FREE,", "para": "p"}, {"w": "for", "para": "p"}, {"w": "now.", "para": "p"}]
    text = "[excited] It's FREE... for now."
    chars = [(c, i * 0.05, i * 0.05 + 0.04) for i, c in enumerate(text)]
    times_from_chars(dw, chars)
    assert dw[0]["s"] == round(10 * 0.05, 3) and dw[1]["s"] > dw[0]["s"], dw
    sb = {"narration": [{"text": "a b c d"}], "scenes": [{"id": "s1"}, {"id": "s2", "cue": "c d"}]}
    ws = display_words(paragraphs(sb)); assign_scenes(sb, ws)
    assert [q["scene"] for q in ws] == ["s1", "s1", "s2", "s2"]
    print("ok")


if __name__ == "__main__":
    import sys
    selftest() if "--selftest" in sys.argv else main()
