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


if __name__ == "__main__":
    assert wer_tokens(["thirty-five", "hundred"]) == ["3500"]
    assert wer_tokens(["eighteen", "thousand"]) == wer_tokens(["18,000"]) == ["18000"]
    assert wer_tokens(["forty-five"]) == ["45"] and wer_tokens(["4pm,"]) == ["4", "pm"]
    assert wer_tokens(["9/11,"]) == wer_tokens(["9", "-11,"]) == ["9", "11"]
    assert wer_tokens(["decades-old"]) == wer_tokens(["decades", "-old"])
    assert wer_score("four to five seconds".split(), "4 -5 seconds".split()) == 0.25  # only 'to' is missing (1 of 4 ref tokens)
    print("common ok")


def slugify(s, n=48):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n] or "reel"
