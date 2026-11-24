"""Shared helpers for reel-factory tools (run inside the runtime venv)."""
import json, os, re, shutil, subprocess, sys, glob
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HOME = Path(os.environ.get("REEL_FACTORY_HOME", Path.home() / ".reel-factory"))
PLUGIN = Path(os.environ.get("REEL_FACTORY_PLUGIN", Path(__file__).resolve().parent.parent))
WIN = os.name == "nt"


def config():
    p = HOME / "config.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save_json(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


def log(prod, msg):
    print(msg, flush=True)
    with open(Path(prod) / "log.md", "a", encoding="utf-8") as f:
        f.write(f"- {msg}\n")


def run(cmd, check=True, **kw):
    r = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False, **kw)
    if check and r.returncode != 0:
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(map(str, cmd))[:300]}\n{r.stderr[-1500:]}")
    return r


def eleven(args, payload=None, out=None):
    """Call the logged-in ElevenLabs CLI (OAuth creds live in the OS keychain). Returns parsed JSON or None when -o used."""
    exe = shutil.which("elevenlabs")
    if not exe:
        raise RuntimeError("elevenlabs CLI not installed")
    cmd = [exe, *args]
    if payload is not None:
        cmd += ["--json", "-"]
    if out:
        cmd += ["-o", str(out)]
    else:
        cmd += ["--format", "json"]
    r = subprocess.run(cmd, input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"elevenlabs {' '.join(args)} failed: {r.stderr[-800:] or r.stdout[-800:]}")
    return None if out else json.loads(r.stdout)


def eleven_ok():
    try:
        d = eleven(["user", "subscription", "get"])
        return d["character_limit"] - d["character_count"]
    except Exception:
        return 0


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(r.stdout.strip())


_whisper = None


def whisper():
    """faster-whisper small, CUDA when available (nvidia wheels), else CPU int8."""
    global _whisper
    if _whisper is None:
        for d in glob.glob(str(Path(sys.prefix) / "Lib" / "site-packages" / "nvidia" / "*" / "bin")) + glob.glob(str(Path(sys.prefix) / "lib" / "python*" / "site-packages" / "nvidia" / "*" / "lib")):
            if WIN:
                os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
        from faster_whisper import WhisperModel
        model = (config().get("whisper") or {}).get("model", "small")  # setup picks base on low-RAM machines
        try:
            _whisper = WhisperModel(model, device="cuda", compute_type="int8_float16")
        except Exception:
            _whisper = WhisperModel(model, device="cpu", compute_type="int8")
    return _whisper


def norm_tok(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


_UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
                                     "fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
_SCALES = {"thousand": 1000, "million": 10 ** 6, "billion": 10 ** 9}


def wer_tokens(words):
    """Tokens for word-error-rate scoring: the script says 'forty-five', 'decades-old', '9/11';
    Whisper writes '45', 'decades -old', '9 -11'. Split on hyphens and slashes, drop thousands separators,
    split '4pm', and turn spelled-out numbers into digits so both sides compare equal."""
    toks = []
    for w in words:
        for t in re.split(r"[-/\s]+|(?<=\d)(?=[a-z])", w.lower().replace(",", "")):
            t = re.sub(r"[^a-z0-9]", "", t)
            if t:
                toks.append(t)
    out, cur, total, num = [], 0, 0, False
    for t in toks + [""]:
        if t in _UNITS or t in _TENS:
            cur, num = cur + _UNITS.get(t, _TENS.get(t, 0)), True
        elif t == "hundred" and num:
            cur = max(cur, 1) * 100
        elif t in _SCALES and num:
            total, cur = total + max(cur, 1) * _SCALES[t], 0
        else:
            if num:
                out.append(str(total + cur))
            cur, total, num = 0, 0, False
            if t:
                out.append(t)
    return out


def wer_score(ref_words, hyp_words):
    """1 - matched/len(ref) on normalised tokens (see wer_tokens)."""
    import difflib
    a, b = wer_tokens(ref_words), wer_tokens(hyp_words)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return 1 - sum(bk.size for bk in sm.get_matching_blocks()) / max(1, len(a))


_SCALE_TOK = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "b": 1e9, "billion": 1e9}
_NUM_RE = re.compile(r"(?<![\w.:])(\d[\d,]*(?:\.\d+)?)\s*(k|m|b|thousand|million|billion)?(?![\w:])", re.I)  # not clock times


def numbers(text):
    """Every number a text states, as floats: digits ('20,000', '45K', '33.5k', '1.2 billion') and spoken words
    ('forty-five thousand', 'one point two billion')."""
    vals = {float(n.replace(",", "")) * _SCALE_TOK.get((s or "").lower(), 1) for n, s in _NUM_RE.findall(text or "")}
    toks = wer_tokens(re.sub(r"\d+:\d+|\d+\.\d+\s*[a-zA-Z]*", " ", text or "").split())  # times dropped; decimals read above
    i = 0
    while i < len(toks):
        if toks[i].isdigit():
            v = float(toks[i])
            if i + 2 < len(toks) and toks[i + 1] == "point" and toks[i + 2].isdigit():  # "one point two billion" -> 1, point, 2000000000
                b = int(toks[i + 2])
                sc = next((sc for sc in (10 ** 9, 10 ** 6, 10 ** 3) if b >= sc and b % sc == 0 and b // sc < 10), None)
                v = (v + (b // sc) / 10) * sc if sc else v + b / 10 ** len(str(b))
                i += 2
            elif i + 1 < len(toks) and toks[i + 1] in _SCALE_TOK:
                v *= _SCALE_TOK[toks[i + 1]]
                i += 1
            vals.add(v)
        i += 1
    return vals


_NOT_SHOWN = {"vo", "cue", "at", "until", "motion", "src", "shot", "id", "layout", "look", "enter", "fit", "type", "kind", "markStyle",
              "url", "icon", "highlight", "tts", "say", "cam", "dur", "x", "y", "w", "h", "tx", "ty", "rot", "color", "bg", "trim", "from", "to"}


def _shown(o, key=None):
    """on-screen strings of a storyboard subtree (skips timing, paths, direction)"""
    if isinstance(o, dict):
        for k, v in o.items():
            if k not in _NOT_SHOWN:
                yield from _shown(v, k)
    elif isinstance(o, list):
        for v in o:
            yield from _shown(v, key)
    elif isinstance(o, str):
        yield o
    elif isinstance(o, (int, float)) and key in ("value", "stars", "num"):
        yield str(o)


def consistency_issues(sb):
    """Numbers and the CTA keyword must agree across voice-over, screen and caption (batch-04: 7 of 100 reference reels
    contradict themselves, e.g. VO '20k stars' vs caption '22k'). Rounding within 7 % is allowed ('40K' for 42.5k)."""
    spoken = " ".join(p.get("text", "") for p in sb.get("narration") or []) or " ".join(s.get("vo", "") for s in sb.get("scenes", []))
    screen = " | ".join(_shown(sb.get("scenes", []))) + " | " + " | ".join(_shown((sb.get("meta") or {}).get("hookTitle")))
    caption = sb.get("caption", "")
    S, C = numbers(spoken), numbers(caption)
    fmt = lambda v: f"{v:,.0f}" if v == int(v) else f"{v:,.2f}".rstrip("0")
    close = lambda a, b: abs(a - b) / max(a, b) <= 0.07
    near = lambda a, b: 0.07 < abs(a - b) / max(a, b) <= 0.4
    # ponytail: any whole number 1000-2100 counts as a calendar year ("1859", "2026") and is not compared as a quantity;
    # a real count in that range (e.g. 1,900 stars) is skipped too. Track the source format if that ever matters.
    year = lambda v: v == int(v) and 1000 <= v <= 2100
    S = {v for v in S if not year(v)}
    C = {v for v in C if not year(v)}
    out = []
    for name, vals in (("screen", numbers(screen)), ("caption", C)):
        for x in sorted(v for v in vals if v >= 100 and not year(v)):
            if any(close(x, y) for y in S):
                continue
            y = next((y for y in sorted(S) if y >= 100 and near(x, y)), None)
            if y is not None:
                out.append(f"{name} says {fmt(x)} but the voice-over says {fmt(y)}")
            elif name == "screen" and (y := next((y for y in sorted(C) if y >= 100 and near(x, y)), None)) is not None:
                out.append(f"screen says {fmt(x)} but the caption says {fmt(y)}")
    kws = set()
    stack = [sb.get("scenes", [])]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if isinstance(o.get("keyword"), str) and o["keyword"].strip():
                kws.add(o["keyword"].strip())
            stack += list(o.values())
        elif isinstance(o, list):
            stack += o
    for kw in sorted(kws):
        for name, text in (("voice-over", spoken), ("caption", caption)):
            if text and not re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", text, re.I):
                out.append(f"CTA keyword {kw!r} is shown but not in the {name}")
    return out


if __name__ == "__main__":
    assert numbers("forty-five thousand stars and 20k forks") >= {45000.0, 20000.0}
    assert not numbers("13 Nov, 4:16 PM") & {416.0, 16.0, 4.0}  # clock times are not quantities
    assert not consistency_issues({"narration": [{"text": "In 1859 Riemann guessed it."}], "caption": "1859 to 2026",
                                   "scenes": [{"gfx": [{"kind": "label", "text": "Riemann (1826-1866)"}]}]})  # years
    assert 1.2e9 in numbers("one point two billion people") and 1.2e9 in numbers("1.2 billion") and 33500.0 in numbers("33.5k")
    sb = {"narration": [{"text": "It has twenty thousand stars. Comment REPO and I'll send it."}],
          "scenes": [{"id": "s1", "vo": "x", "shots": [{"at": "stars", "kind": "image", "src": "shot-a-111.png", "label": "★ 22,000"}],
                      "gfx": [{"at": "send", "kind": "scene", "type": "cta", "props": {"kind": "comment", "keyword": "REPO"}}]}],
          "caption": "40K devs use it. Comment LINK for the link."}
    iss = consistency_issues(sb)
    assert any("22,000" in i and "20,000" in i for i in iss) and any("'REPO'" in i and "caption" in i for i in iss), iss
    assert not any("111" in i for i in iss) and not any("40,000" in i for i in iss), iss  # paths ignored; 40K unrelated (>40 % off)
    assert wer_tokens(["thirty-five", "hundred"]) == ["3500"]
    assert wer_tokens(["eighteen", "thousand"]) == wer_tokens(["18,000"]) == ["18000"]
    assert wer_tokens(["forty-five"]) == ["45"] and wer_tokens(["4pm,"]) == ["4", "pm"]
    assert wer_tokens(["9/11,"]) == wer_tokens(["9", "-11,"]) == ["9", "11"]
    assert wer_tokens(["decades-old"]) == wer_tokens(["decades", "-old"])
    assert wer_score("four to five seconds".split(), "4 -5 seconds".split()) == 0.25  # only 'to' is missing (1 of 4 ref tokens)
    print("common ok")


def slugify(s, n=48):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n] or "reel"
