"""storyboard.json + words.json -> props.json for the Remotion engine.

usage: rf build <prod_dir>

- The creation mode (meta.mode, see references/modes/modes.json) supplies defaults: layout, caption style, mix levels.
- Narrated modes: a scene starts on its first spoken word and lasts until the next scene starts, so visuals change
  exactly with the narration (corpus: one claim -> one visual, ~1.5-3 s each).
- Silent mode (no VO): scenes use their own "dur" (s); boundaries snap to the music's beat grid.
- Speech sync: list/flow items, carousel cards, quote/headline highlights and walkthrough actions with "say" are timed
  to the moment the VO says them (unless the storyboard sets the times explicitly).
- SFX cues are generated from scene entrances (whoosh/pop/swipe), terminals and typing (type), clicks, stamps (impact),
  re-hooks (riser) and the CTA (ding). A scene can override with "sfx": [{"t":0.2,"name":"tick"}] or [] to mute.
- Missing image/video assets degrade gracefully into text scenes instead of failing the render.
"""
import re, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from common import HOME, PLUGIN, config, load_json, log, save_json

TAIL = 1.4  # hold after last word (CTA readable)
ENTER_SFX = {"push": ("whoosh", 0.28), "slide": ("swipe", 0.35), "pop": ("pop", 0.45), "blur": ("swipe", 0.3), "cut": None}
MODES = PLUGIN / "skills" / "reel-factory" / "references" / "modes" / "modes.json"
STOP = {"the", "and", "for", "you", "your", "with", "that", "this", "not", "are", "its", "it's", "into", "from", "every", "use", "add"}


def mode_spec(mode_id):
    modes = {m["id"]: m for m in load_json(MODES)["modes"]} if MODES.exists() else {}
    return modes.get(mode_id or "kinetic", modes.get("kinetic", {"id": "kinetic", "defaults": {}}))


def fallback_scene(sc, prod):
    """replace scenes whose media asset is missing"""
    p = sc.get("props", {})
    if sc["type"] in ("image", "video") and p.get("src") and not (prod / "public" / p["src"]).exists() and not str(p["src"]).startswith("http"):
        log(prod, f"build: {sc['id']} asset {p['src']} missing -> title fallback")
        sc["type"] = "title"
        sc["props"] = {"lines": [p.get("caption") or p.get("fallback") or sc.get("vo", "")[:60]]}
    for key in ("image", "src"):
        if sc["type"] not in ("image", "video") and p.get(key) and not str(p[key]).startswith("http") and not (prod / "public" / p[key]).exists():
            p.pop(key)
    return sc


def stripped(x):
    return re.sub(r"[*\[\]_]", "", x)


def keytoks(x):
    return [t for t in re.findall(r"[a-z0-9]+", stripped(x).lower()) if len(t) >= 3 and t not in STOP]


def speech_sync(items, scene_words, start, dur, min_hits=None):
    """time each item to when the VO first says one of its key words; monotonic, gaps filled evenly"""
    toks = [keytoks(x) for x in items]
    spoken = [(re.sub(r"[^a-z0-9]", "", w["w"].lower()), w["s"] - start) for w in scene_words]
    at, last = [], -1.0
    for tk in toks:
        hit = next((t for n, t in spoken if t > last + 0.2 and any(n.startswith(k) or k.startswith(n) and len(n) >= 3 for k in tk)), None)
        at.append(None if hit is None else max(0.0, hit - 0.12))
        if hit is not None:
            last = hit
    if sum(a is not None for a in at) < (min_hits or max(1, len(items) // 2)):
        return None
    for i, a in enumerate(at):
        if a is None:
            prev = next((at[j] for j in range(i - 1, -1, -1) if at[j] is not None), 0.1)
            nxt = next((at[j] for j in range(i + 1, len(at)) if at[j] is not None), dur - 0.5)
            at[i] = prev + (nxt - prev) / 2
    for i in range(1, len(at)):
        at[i] = max(at[i], at[i - 1] + 0.2)
    return [round(min(a, dur - 0.4), 3) for a in at]


def beat_grid(audio, sr=22050, hop=512):
    """beat times (s) of a music file: onset envelope -> autocorrelation tempo (70-180 bpm) -> best phase"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if len(x) < sr * 2:
        return []
    n = len(x) // hop
    e = np.log1p(100 * np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1)))
    onset = np.maximum(0, np.diff(e, prepend=e[0]))
    fps = sr / hop
    ac = np.correlate(onset, onset, "full")[len(onset) - 1:]
    lags = np.arange(int(fps * 60 / 180), int(fps * 60 / 70))
    period = lags[np.argmax(ac[lags])]
    phase = max(range(period), key=lambda p: onset[p::period].sum())
    return [round(float(i / fps), 3) for i in range(phase, n, period)]


def silent_timing(sb, prod):
    """scene boundaries from scene 'dur', snapped to the nearest beat (keeps each scene >= 0.5 s)"""
    beats = []
    music = prod / "public" / "music.mp3"
    if music.exists():
        beats = beat_grid(music)
        save_json(prod / "public" / "beats.json", beats)
    t, bounds = 0.0, []
    for sc in sb["scenes"]:
        target = t + float(sc.get("dur", 2.5))
        if beats:
            cand = [b for b in beats if b >= t + 0.5]
            if cand:
                target = min(cand, key=lambda b: abs(b - target))
        bounds.append((round(t, 3), round(target, 3)))
        t = target
    log(prod, f"build: silent mode · {len(beats)} beats detected" + (f" (~{60 / np.median(np.diff(beats)):.0f} bpm)" if len(beats) > 2 else ""))
    return bounds


def main():
    prod = Path(sys.argv[1])
    sb = load_json(prod / "storyboard.json")
    cfg = config()
    brand = cfg.get("brand", {})
    meta = dict(sb["meta"])
    spec = mode_spec(meta.get("mode"))
    d = spec.get("defaults", {})
    meta["mode"] = spec.get("id", "kinetic")
    silent = meta["mode"] == "silent" or (sb.get("voice") or {}).get("none")
    words = [] if silent else load_json(prod / "words.json")

    if silent:
        bounds = silent_timing(sb, prod)
    else:
        first = {}
        for w in words:
            first.setdefault(w["scene"], w["s"])
        ids = [sc["id"] for sc in sb["scenes"]]
        bounds = [(0.0 if i == 0 else first[ids[i]], first[ids[i + 1]] if i + 1 < len(ids) else words[-1]["e"] + TAIL) for i in range(len(ids))]

    scenes = []
    for i, sc in enumerate(sb["scenes"]):
        sc = fallback_scene(dict(sc), prod)
        start, end = bounds[i]
        dur = end - start
        if dur < 0.6:
            log(prod, f"build WARNING: scene {sc['id']} only {dur:.2f}s — consider merging its VO into a neighbour")
        p = dict(sc.get("props", {}))
        sw = [w for w in words if w["scene"] == sc["id"]]
        if sw:
            if sc["type"] in ("list", "flow") and "revealAt" not in p:
                key = "items" if sc["type"] == "list" else "nodes"
                if p.get(key):
                    ra = speech_sync(p[key], sw, start, dur)
                    if ra:
                        p["revealAt"] = ra
            if sc["type"] == "carousel" and p.get("items") and "revealAt" not in p:
                ra = speech_sync([it["name"] for it in p["items"]], sw, start, dur)
                if ra:
                    p["revealAt"] = [0.0] + ra[1:]  # first card is on screen from the cut
            if sc["type"] in ("quote", "headline") and p.get("highlight") and "highlightAt" not in p:
                ha = speech_sync(p["highlight"], sw, start, dur, min_hits=1)
                if ha:
                    p["highlightAt"] = ha
            if sc["type"] == "walkthrough" and p.get("actions"):
                says = [a.get("say") for a in p["actions"]]
                if any(says) and not all("at" in a for a in p["actions"]):
                    ra = speech_sync([s or "" for s in says], sw, start, dur, min_hits=1) or []
                    p["actions"] = [{**a, "at": a.get("at", ra[j] if j < len(ra) and a.get("say") else None)} for j, a in enumerate(p["actions"])]
                    p["actions"] = [{k: v for k, v in a.items() if v is not None} for a in p["actions"]]
        scenes.append({"id": sc["id"], "type": sc["type"], "start": round(start, 3), "end": round(end, 3), "enter": sc.get("enter", "cut" if silent and i else "push"),
                       "label": sc.get("label"), "props": p, "_sfx": sc.get("sfx"), "_rehook": sc.get("rehook", False)})

    sfx = []
    for i, sc in enumerate(scenes):
        p = sc["props"]
        if sc["_sfx"] is not None:
            sfx += [{"t": round(sc["start"] + c.get("t", 0), 3), "name": c["name"], "vol": c.get("vol", 0.4)} for c in sc["_sfx"]]
            continue
        e = ENTER_SFX.get(sc["enter"])
        if e and i > 0 and not silent:
            sfx.append({"t": max(0, sc["start"] - 0.06), "name": e[0], "vol": e[1]})
        if sc["type"] == "terminal":
            sfx.append({"t": sc["start"] + 0.3, "name": "type", "vol": 0.22})
        if sc["type"] == "punch" and p.get("style") == "stamp":
            sfx.append({"t": sc["start"] + 0.05, "name": "impact", "vol": 0.5})
        if sc["type"] == "cta":
            sfx.append({"t": sc["start"] + 1.55, "name": "ding", "vol": 0.35})
        if sc["type"] == "carousel":
            sfx += [{"t": round(sc["start"] + a, 3), "name": "tick", "vol": 0.3} for a in p.get("revealAt", [])[1:]]
        if sc["type"] == "sheet" and p.get("stamp"):
            sfx.append({"t": sc["start"] + min(1.0, (sc["end"] - sc["start"]) * 0.45), "name": "impact", "vol": 0.35})
        if sc["type"] == "walkthrough":
            for a in p.get("actions", []):
                if "at" in a and a.get("type") == "click":
                    sfx.append({"t": round(sc["start"] + a["at"], 3), "name": "click", "vol": 0.45})
                if "at" in a and a.get("type") == "type":
                    sfx.append({"t": round(sc["start"] + a["at"], 3), "name": "type", "vol": 0.22})
        if sc["_rehook"]:
            sfx.append({"t": max(0, sc["start"] - 1.15), "name": "riser", "vol": 0.3})
    for sc in scenes:
        sc.pop("_sfx"), sc.pop("_rehook")

    meta.setdefault("layout", d.get("layout", "faceless"))
    if meta["layout"] == "split-avatar" and not (sb.get("avatar") or {}).get("src"):
        meta["layout"] = "faceless"
    meta.setdefault("captionStyle", "none" if silent else d.get("captionStyle", "pill"))
    if brand.get("handle") and not meta.get("handle"):
        meta["handle"] = brand["handle"]
    if brand.get("accent") and not meta.get("accent"):
        meta["accent"] = brand["accent"]
    hook = meta.get("hookTitle")
    if hook and "untilScene" in hook:
        target = hook.pop("untilScene")
        hook["until"] = next((s["end"] for s in scenes if s["id"] == target), scenes[0]["end"])
    prog = meta.get("progress")
    if prog and "scenes" in prog:  # {"items": [...], "scenes": ["s3", "s6", ...]} -> completion times
        starts = {s["id"]: s["start"] for s in scenes}
        meta["progress"] = {**{k: v for k, v in prog.items() if k != "scenes"}, "at": [starts[x] for x in prog["scenes"]]}

    pub = prod / "public"
    (pub / "sfx").mkdir(parents=True, exist_ok=True)
    for f in (HOME / "sfx").glob("*.wav"):
        shutil.copy2(f, pub / "sfx" / f.name)

    props = {"meta": meta, "durationSec": round(scenes[-1]["end"], 3), "fps": 30,
             "audio": {"vo": None if silent else "vo.mp3", "music": "music.mp3" if (pub / "music.mp3").exists() else None,
                       "musicVolume": sb.get("musicVolume", d.get("musicVolume", 0.30)), "duckTo": sb.get("duckTo", d.get("duckTo", 0.11)), "sfx": sfx},
             "words": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in words],
             "emphasis": [e.lower() for e in sb.get("emphasis", [])], "scenes": scenes}
    for k in ("vo", "music"):
        if not props["audio"][k]:
            props["audio"].pop(k)
    avatar = sb.get("avatar") or {}
    if meta["layout"] == "split-avatar":
        if avatar.get("src") and (pub / avatar["src"]).exists():
            props["avatar"] = {"src": avatar["src"]}
        else:
            log(prod, "build: avatar clip missing -> faceless layout")
            meta["layout"] = "faceless"
    save_json(prod / "props.json", props)
    avg = sum(s["end"] - s["start"] for s in scenes) / len(scenes)
    longest = max(scenes, key=lambda s: s["end"] - s["start"])
    log(prod, f"build: mode {meta['mode']} · {len(scenes)} scenes · {props['durationSec']:.1f}s · avg {avg:.2f}s/scene · longest {longest['id']} {longest['end'] - longest['start']:.1f}s · {len(sfx)} sfx")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ws = [{"w": w, "s": i * 0.4, "e": i * 0.4 + 0.3} for i, w in enumerate("first we open hallmark then taste skill and finally gsd".split())]
        assert speech_sync(["Hallmark", "Taste skill", "GSD"], ws, 0, 5) == [1.08, 1.88, 3.48], speech_sync(["Hallmark", "Taste skill", "GSD"], ws, 0, 5)
        print("ok")
    else:
        main()
