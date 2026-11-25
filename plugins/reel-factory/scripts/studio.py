"""Studio timeline compiler: storyboard (engine "studio") + words.json -> props for the Studio composition.

The storyboard keeps narration beats (scenes, one VO segment each). Each beat adds edit decisions anchored to words:
  "layout": "split"            or  [{"at": "phrase", "layout": "full"}, ...]      presenter framing
  "motion": "leans in, sceptical, points up-left at the graphic"                  presenter performance direction
  "shots":  [{"at": "phrase", "kind": "image|video|scene|color", ...}]            content-track visuals
  "gfx":    [{"at": "phrase", "dur": 1.6, "kind": "sticker|label|slam|counter|scene", ...}]
"at" = a phrase from this beat's narration (the shot starts as it is spoken); absent = beat start (first) or evenly
spaced. Shots run until the next shot starts (also across beats), so the content track never goes empty.
Image shots: "highlight": ["exact phrase on the image", ...] uses the rf shot JSON marks; "cam" keyframes optional —
by default the camera opens on the masthead and pans/zooms to each highlight as it is spoken.
"""
import re
from pathlib import Path
from common import load_json, log

TRANS = 0.42  # layout transition (engine layout.ts)
ENTER_SFX = {"whip": ("whoosh", 0.32), "zoom": ("whoosh", 0.25), "blur": ("swipe", 0.22), "slide": ("swipe", 0.28), "flash": ("impact", 0.25)}
STOP = {"the", "and", "for", "you", "your", "with", "that", "this", "are", "its", "into", "from", "was", "has", "have", "but"}
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def phrase_time(phrase, sw, fallback):
    """time of the first word of `phrase` inside the beat's words (sequence match, tolerant to punctuation)"""
    if phrase is None:
        return fallback
    if isinstance(phrase, (int, float)):
        return (sw[0]["s"] if sw else fallback) + float(phrase)
    toks = [norm(t) for t in str(phrase).split() if norm(t)]
    seq = [norm(w["w"]) for w in sw]
    for i in range(len(seq)):
        if toks and seq[i] and (seq[i] == toks[0] or (len(toks[0]) > 3 and seq[i].startswith(toks[0][:4]))):
            ok = all(i + j < len(seq) and (seq[i + j] == tk or seq[i + j].startswith(tk[:4])) for j, tk in enumerate(toks[:3]))
            if ok:
                return max(0.0, sw[i]["s"] - 0.08)
    keys = [t for t in toks if len(t) > 3 and t not in STOP]
    for w in sw:
        if any(norm(w["w"]).startswith(k[:5]) for k in keys):
            return max(0.0, w["s"] - 0.08)
    return fallback


def image_shot(sh, prod, start, sw):
    """image / screenshot shot: aspect, highlight marks timed to speech, and an automatic camera path"""
    p = dict(sh)
    meta = {}
    if p.get("shot"):  # rf shot JSON
        j = prod / "public" / p["shot"]
        if j.exists():
            meta = load_json(j)
            p.setdefault("src", meta.get("src"))
    src = p.get("src")
    f = prod / "public" / src if src else None
    if not f or not f.exists():
        return None
    if "aspect" not in p:
        try:
            from PIL import Image
            with Image.open(f) as im:
                p["aspect"] = round(im.width / im.height, 4)
        except Exception:
            p["aspect"] = 0.75
    marks = []
    want = p.get("highlight") or []
    style = p.get("markStyle")
    for m in meta.get("marks", []):
        if want and not any(norm(h) in norm(m["text"]) or norm(m["text"]) in norm(h) for h in want):
            continue
        at = phrase_time(m.get("say") or m["text"], sw, start + 0.6) - start
        marks.append({"rects": m["rects"], "at": round(max(0.25, at), 3), **({"style": style or m.get("style")} if (style or m.get("style")) else {})})
    for m in p.get("marks", []):  # explicit marks in the storyboard
        marks.append({**m, "at": round(phrase_time(m.get("say"), sw, start + 0.6) - start, 3) if "say" in m else m.get("at", 0.6)})
    marks.sort(key=lambda m: m["at"])
    if marks:
        p["marks"] = marks
    if not p.get("cam"):
        cam = [{"t": 0, "x": 0.5, "y": 0.0, "z": 1.0}]  # open on the masthead / top of the page
        for m in marks:
            r = m["rects"]
            x0, x1 = min(q["x"] for q in r), max(q["x"] + q["w"] for q in r)
            y0, y1 = min(q["y"] for q in r), max(q["y"] + q["h"] for q in r)
            z = max(1.0, min(1.7, 0.86 / max(0.1, x1 - x0)))
            cam.append({"t": round(max(0.05, m["at"] - 0.35), 3), "x": round((x0 + x1) / 2, 4), "y": round((y0 + y1) / 2, 4), "z": round(z, 3)})
        if len(cam) == 1:
            cam.append({"t": 0.4, "x": 0.5, "y": 0.35, "z": 1.08})
        p["cam"] = cam
    for k in ("shot", "highlight", "markStyle", "at"):
        p.pop(k, None)
    return p


def compile_studio(prod, sb, words, tail=1.4):
    first = {}
    for w in words:
        first.setdefault(w["scene"], w["s"])
    scenes = sb["scenes"]
    ids = [s["id"] for s in scenes]
    end_all = words[-1]["e"] + tail
    bounds = {}
    for i, s in enumerate(scenes):
        bounds[s["id"]] = (0.0 if i == 0 else first[s["id"]], first[ids[i + 1]] if i + 1 < len(ids) else end_all)

    layouts, shots, gfx, sfx = [], [], [], []
    for i, sc in enumerate(scenes):
        a, b = bounds[sc["id"]]
        sw = [w for w in words if w["scene"] == sc["id"]]
        # layout events
        lay = sc.get("layout")
        if isinstance(lay, str):
            layouts.append({"t": round(a, 3), "layout": lay})
        elif isinstance(lay, list):
            for k, e in enumerate(lay):
                layouts.append({"t": round(a if k == 0 and "at" not in e else phrase_time(e.get("at"), sw, a), 3), "layout": e["layout"],
                                **({"motion": e["motion"], "scene": sc["id"]} if e.get("motion") else {})})  # per-layout gesture (presenter.py)
        # shots
        items = list(sc.get("shots") or [])
        if not items and sc.get("type") and sc["type"] != "presenter":
            items = [{"kind": "scene", "type": sc["type"], "props": sc.get("props", {}), "enter": sc.get("enter")}]
        n = len(items)
        for k, sh in enumerate(items):
            t0 = a if k == 0 and "at" not in sh else phrase_time(sh.get("at"), sw, a + (b - a) * k / max(1, n))
            kind = sh.get("kind", "scene")
            if kind == "scene" and sh.get("type") == "source":  # legacy source scene -> camera-moved image shot
                pr = sh.get("props", {})
                sh = {"kind": "image", "shot": pr.get("shot"), "src": pr.get("src"), "highlight": [m["text"] for m in pr.get("marks", [])] or None,
                      "label": " · ".join(x for x in [pr.get("outlet"), pr.get("date")] if x) or None, "enter": sh.get("enter")}
                kind = "image"
            if kind == "image":
                p = image_shot(sh, prod, t0, sw)
                if not p:
                    log(prod, f"studio: {sc['id']} image {sh.get('src') or sh.get('shot')} missing -> skipped")
                    continue
            elif kind == "video":
                p = dict(sh)
                if not (prod / "public" / p.get("src", "")).exists():
                    log(prod, f"studio: {sc['id']} video {p.get('src')} missing -> skipped")
                    continue
            else:
                p = dict(sh)
                if kind == "scene":  # speech-synced reveals inside legacy components, relative to the shot start
                    from build import speech_sync
                    pr = dict(p.get("props") or {})
                    nxt = items[k + 1] if k + 1 < n else None
                    t1 = phrase_time(nxt.get("at"), sw, b) if nxt else b
                    if p.get("type") in ("list", "flow") and "revealAt" not in pr:
                        key = "items" if p["type"] == "list" else "nodes"
                        ra = speech_sync(pr.get(key) or [], [w for w in sw if w["s"] >= t0 - 0.05], t0, max(0.8, t1 - t0))
                        if ra:
                            pr["revealAt"] = ra
                    if p.get("type") in ("quote", "headline") and pr.get("highlight") and "highlightAt" not in pr:
                        ha = speech_sync(pr["highlight"], [w for w in sw if w["s"] >= t0 - 0.05], t0, max(0.8, t1 - t0), min_hits=1)
                        if ha:
                            pr["highlightAt"] = ha
                    p["props"] = pr
            p = {k2: v for k2, v in p.items() if v is not None and k2 != "at"}
            p.update({"id": f"{sc['id']}-{k}", "from": round(t0, 3), "kind": kind})
            if not shots and i == 0 and k == 0:
                p["enter"] = "cut"
            shots.append(p)
        # graphics
        for k, g in enumerate(sc.get("gfx") or []):
            t0 = phrase_time(g.get("at"), sw, a + 0.2)
            t1 = phrase_time(g["until"], sw, b) if g.get("until") else min(b + 0.1, t0 + float(g.get("dur", 1.8)))
            gfx.append({**{k2: v for k2, v in g.items() if k2 not in ("at", "until", "dur")}, "id": f"{sc['id']}-g{k}", "from": round(t0, 3), "to": round(max(t0 + 0.5, t1), 3)})

    shots.sort(key=lambda s: s["from"])
    for j, s in enumerate(shots):
        s["to"] = shots[j + 1]["from"] if j + 1 < len(shots) else round(end_all, 3)
    shots = [s for s in shots if s["to"] - s["from"] >= 0.25]
    layouts.sort(key=lambda e: e["t"])
    dedup = []
    for e in layouts:
        if not dedup or dedup[-1]["layout"] != e["layout"]:
            dedup.append(e)
    layouts = dedup or [{"t": 0, "layout": "off"}]

    # sound design: transitions, layout moves, graphic hits
    for s in shots[1:]:
        e = ENTER_SFX.get(s.get("enter", "cut"))
        if e:
            sfx.append({"t": round(max(0, s["from"] - 0.05), 3), "name": e[0], "vol": e[1]})
    for e in layouts[1:]:
        sfx.append({"t": round(max(0, e["t"] - 0.04), 3), "name": "swipe", "vol": 0.16})
    for g in gfx:
        nm = {"sticker": ("pop", 0.4), "slam": ("impact", 0.42), "counter": ("tick", 0.3), "label": ("tick", 0.2), "callout": ("pop", 0.3)}.get(g["kind"])
        if nm:
            sfx.append({"t": round(g["from"], 3), "name": nm[0], "vol": nm[1]})
    return {"layouts": layouts, "shots": shots, "gfx": gfx, "sfx": sorted(sfx, key=lambda c: c["t"]), "duration": round(end_all, 3), "bounds": bounds}


def presenter_windows(layouts, duration, merge_gap=1.2, pad=0.15):
    """reel-time spans where the presenter is visible (layout != off), incl. the transitions in and out"""
    spans, on = [], None
    for e in layouts:
        vis = e["layout"] != "off"
        if vis and on is None:
            on = e["t"]
        elif not vis and on is not None:
            spans.append([on, e["t"] + TRANS])
            on = None
    if on is not None:
        spans.append([on, duration])
    out = []
    for s in spans:
        s = [max(0.0, s[0] - pad), min(duration, s[1] + pad)]
        if out and s[0] - out[-1][1] < merge_gap:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return [[round(a, 3), round(b, 3)] for a, b in out]


# ---------- soundbites: real people speaking with their own voice ----------
# storyboard "soundbites": [{"after": "<narration phrase>", "src": "footage/x.mp4" (rf footage get --audio), "trim": 0,
#   "dur": 4.5, "label": "Outlet · Name, role", "fit": "cover"}]
# The narration pauses after the phrase; the clip plays full-frame (presenter off) with its own sound and captions.
# Everything is planned in voice-over time and warped at build time only, so presenter renders (sliced from vo.mp3) never change.

def clip_words(src):
    """word timings of a clip's own speech (local Whisper), cached next to the clip"""
    from common import load_json as lj, save_json, whisper
    cache = Path(src).with_suffix(".words.json")
    if cache.exists():
        return lj(cache)
    segs, _ = whisper().transcribe(str(src), word_timestamps=True, vad_filter=True, language="en")
    ws = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in (s.words or [])]
    save_json(cache, ws)
    return ws


def _db(src, a, b):
    """mean loudness (dBFS) of [a, b] s of a clip's audio"""
    import subprocess
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{max(0, a):.3f}", "-to", f"{b:.3f}", "-i", str(src), "-vn", "-af", "volumedetect",
                        "-f", "null", "-"], capture_output=True, text=True, timeout=60)
    m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
    return float(m.group(1)) if m else -99.0


def soundbite_plan(prod, sb, words, transcribe=True):
    """soundbites in voice-over time: at = end of the `after` phrase; words = the clip's speech inside [trim, trim+dur]"""
    out = []
    seq = [norm(w["w"]) for w in words]
    for x in sb.get("soundbites") or []:
        toks = [norm(t) for t in x["after"].split() if norm(t)]
        at = next((words[i + len(toks) - 1]["e"] for i in range(len(seq) - len(toks) + 1) if seq[i:i + len(toks)] == toks), None)
        if at is None:
            raise SystemExit(f"soundbite {x.get('src')}: phrase not in the narration: {x['after']!r}")
        trim, dur = float(x.get("trim", 0)), float(x["dur"])
        cw = clip_words(Path(prod) / "public" / x["src"]) if transcribe else []
        ws = [w for w in cw if w["s"] >= trim - 0.05 and w["e"] <= trim + dur + 0.05]
        last = max((w["e"] for w in cw if w["s"] < trim + dur), default=None)  # the speech actually playing at the cut
        warn = None
        # owner 2026-11-25: Isaacson's last word "Nvidia" was clipped. Whisper word ends drift (a token can swallow the
        # pause after it), so only warn when the audio is also loud right before the cut.
        if last is not None and trim + dur - last < 0.25 and transcribe and _db(Path(prod) / "public" / x["src"], trim + dur - 0.15, trim + dur) > -30:
            warn = f"cut at {trim + dur:.2f}s is {trim + dur - last:+.2f}s from the last word's end ({last:.2f}s) and still loud: end in the silence after it (>= +0.25 s)"
        if x.get("text") and ws:  # verified wording for the captions on Whisper's timing (ASR mishears names and endings)
            toks = x["text"].split()
            if len(toks) == len(ws):
                ws = [{**w, "w": t} for w, t in zip(ws, toks)]
            else:  # ponytail: even spread over the spoken span when the counts differ; per-word alignment if it ever drifts
                a, b = ws[0]["s"], ws[-1]["e"]
                step = (b - a) / len(toks)
                ws = [{"w": t, "s": round(a + i * step, 3), "e": round(a + (i + 1) * step - 0.02, 3)} for i, t in enumerate(toks)]
        out.append({**x, "at": round(at, 3), "trim": trim, "dur": dur, "words": ws, **({"warn": warn} if warn else {})})
    return sorted(out, key=lambda s: s["at"])


def apply_soundbites(r, words, windows, sbs):
    """warp the compiled timeline (voice-over time -> reel time) and splice in the soundbite clips"""
    if not sbs:
        return r, words, windows
    # edit events up to 0.12 s before the pause belong to the speech that follows it (phrase_time starts them 0.08 s early)
    W = lambda t, eps=0.12: round(t + sum(s["dur"] for s in sbs if t >= s["at"] - eps), 3)
    starts, off = [], 0.0
    for s in sbs:
        starts.append(round(s["at"] + off, 3))
        off += s["dur"]
    shots = [{**x, "from": W(x["from"])} for x in r["shots"]]
    for k, s in enumerate(sbs):
        shots.append({"id": f"sb{k}", "kind": "video", "src": s["src"], "trim": s["trim"], "fit": s.get("fit", "cover"), "from": starts[k],
                      "enter": s.get("enter", "cut"), **({"label": s["label"]} if s.get("label") else {})})
    shots.sort(key=lambda x: x["from"])
    end = round(r["duration"] + off, 3)
    for j, x in enumerate(shots):
        x["to"] = shots[j + 1]["from"] if j + 1 < len(shots) else end
    lay = [{**e, "t": W(e["t"])} for e in r["layouts"]]
    for k, s in enumerate(sbs):
        cur = [e for e in r["layouts"] if e["t"] <= s["at"] + 1e-6]
        back = cur[-1]["layout"] if cur else "off"
        lay += [{"t": starts[k], "layout": "off"}, {"t": round(starts[k] + s["dur"], 3), "layout": back}]
    lay.sort(key=lambda e: e["t"])
    dedup = []
    for e in lay:
        if not dedup or dedup[-1]["layout"] != e["layout"]:
            dedup.append(e)
    gfx = []
    for g in r["gfx"]:
        to = W(g["to"])
        for k, s in enumerate(sbs):  # a graphic never runs over a soundbite: it ends where the soundbite starts
            if g["from"] < s["at"] - 0.12 and s["at"] < g["to"]:
                to = min(to, starts[k])
        gfx.append({**g, "from": W(g["from"]), "to": to})
    sfx = [{**c, "t": W(c["t"])} for c in r["sfx"]] + [{"t": max(0, st - 0.05), "name": "whoosh", "vol": 0.22} for st in starts]
    nw = [{**w, "s": W(w["s"], 1e-3), "e": W(w["s"], 1e-3) + round(w["e"] - w["s"], 3)} for w in words]
    for k, s in enumerate(sbs):
        nw += [{"w": w["w"], "s": round(starts[k] + w["s"] - s["trim"], 3), "e": round(starts[k] + w["e"] - s["trim"], 3), "soundbite": True}
               for w in s["words"]]
    nw.sort(key=lambda w: w["s"])
    win = []
    for w in windows or []:
        # a window that opens just before the pause (its lead-in pad) moves whole: lips stay on the speech after the soundbite
        if any(w["start"] < s["at"] - 0.45 and s["at"] < w["end"] for s in sbs):
            raise SystemExit(f"soundbite inside presenter window {w['start']}-{w['end']}: move it to a moment where the presenter is off")
        sh = sum(s["dur"] for s in sbs if w["start"] >= s["at"] - 0.45)
        win.append({**w, "start": round(w["start"] + sh, 3), "end": round(w["end"] + sh, 3)})
    r2 = {**r, "shots": shots, "layouts": dedup, "gfx": gfx, "sfx": sorted(sfx, key=lambda c: c["t"]), "duration": end,
          "bounds": {k: (W(a), W(b)) for k, (a, b) in r["bounds"].items()}}
    return r2, nw, win


def soundbite_audio(pub, sbs):
    """vo_sb.mp3 = the voice-over with each soundbite's own sound spliced in at its pause (vo.mp3 stays untouched)"""
    import subprocess
    fmt = "aresample=44100,aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono"
    ins, fc, parts, prev = ["-i", str(pub / "vo.mp3")], [], [], 0.0
    for k, s in enumerate(sbs):
        ins += ["-i", str(pub / s["src"])]
        d = s["dur"]
        fc.append(f"[0:a]atrim={prev}:{s['at']},asetpts=PTS-STARTPTS,{fmt}[v{k}]")
        fc.append(f"[{k + 1}:a]atrim={s['trim']}:{s['trim'] + d},asetpts=PTS-STARTPTS,loudnorm=I=-19:TP=-3,volume={float(s.get('gain', 0))}dB,{fmt},"
                  f"afade=t=in:d=0.05,afade=t=out:st={max(0, d - 0.12):.3f}:d=0.12,apad=whole_dur={d},atrim=0:{d}[s{k}]")
        parts += [f"[v{k}]", f"[s{k}]"]
        prev = s["at"]
    fc.append(f"[0:a]atrim=start={prev},asetpts=PTS-STARTPTS,{fmt}[vend]")
    parts.append("[vend]")
    fc.append("".join(parts) + f"concat=n={len(parts)}:v=0:a=1[out]")
    out = pub / "vo_sb.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fc), "-map", "[out]", "-b:a", "192k", str(out)], check=True)
    return out.name


if __name__ == "__main__":
    ws = [{"w": w, "s": i * 0.5, "e": i * 0.5 + 0.4, "scene": "s1" if i < 6 else "s2"} for i, w in enumerate("OpenAI just put your business inside ChatGPT. Here's how it works".split())]
    sb = {"scenes": [{"id": "s1", "layout": "split", "shots": [{"kind": "color", "bg": "#000"}, {"at": "business", "kind": "color", "bg": "#fff", "enter": "whip"}]},
                     {"id": "s2", "layout": [{"layout": "full"}, {"at": "works", "layout": "off"}], "gfx": [{"at": "how", "kind": "label", "text": "x"}]}]}
    r = compile_studio(Path("."), sb, ws)
    assert [s["from"] for s in r["shots"]] == [0.0, 1.92], r["shots"]
    assert [e["layout"] for e in r["layouts"]] == ["split", "full", "off"], r["layouts"]
    assert r["layouts"][2]["t"] == 4.92, r["layouts"]
    assert presenter_windows(r["layouts"], r["duration"]) == [[0.0, 5.49]], presenter_windows(r["layouts"], r["duration"])
    assert presenter_windows([{"t": 0, "layout": "full"}, {"t": 2, "layout": "off"}, {"t": 8, "layout": "corner"}], 10) == [[0.0, 2.57], [7.85, 10]]
    # soundbite after "works": everything later shifts by 3 s, the clip is an off-layout shot with its own caption words
    sbs = [{"after": "it works", "src": "footage/x.mp4", "at": 5.46, "trim": 1.0, "dur": 3.0, "words": [{"w": "wow", "s": 1.2, "e": 1.6}]}]
    r2, w2, win2 = apply_soundbites(r, ws, [{"start": 0.0, "end": 5.2, "src": "p.webm"}], sbs)
    assert r2["duration"] == round(r["duration"] + 3, 3) and r2["shots"][-1]["id"] == "sb0" and r2["shots"][-1]["from"] == 5.46, r2["shots"]
    assert r2["layouts"][-1]["layout"] == "off" and win2 == [{"start": 0.0, "end": 5.2, "src": "p.webm"}], (r2["layouts"], win2)
    assert [w["w"] for w in w2][-1] == "wow" and w2[-1]["s"] == 5.66, w2[-3:]
    r3, _, _ = apply_soundbites({**r, "gfx": [{"id": "g", "kind": "label", "from": 4.0, "to": 7.0}]}, ws, [], sbs)
    assert r3["gfx"][0]["to"] == 5.46, r3["gfx"]  # clipped at the soundbite, not pushed past it
    print("ok")
