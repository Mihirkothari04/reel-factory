#!/usr/bin/env python3
"""reel-factory launcher. Works with ANY python3 on PATH; re-executes tools inside the runtime venv.

  python rf.py setup            create ~/.reel-factory (venv, engine deps, sfx kit, config)
  python rf.py doctor           check every tool / credential the pipeline can use
  python rf.py probe [--json]   system probe (works before setup): capabilities, per-stage plan, blockers, asks
  python rf.py <tool> [args]    run scripts/<tool>.py inside the runtime venv
                                tools: trends, sources, modes, voice, music, image, build, render, qa,
                                       analyze, ingest, kb, sfx_kit, config

Runtime home: $REEL_FACTORY_HOME or ~/.reel-factory  (kept outside the plugin so plugin updates never wipe it)
"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
HOME = Path(os.environ.get("REEL_FACTORY_HOME", Path.home() / ".reel-factory"))
WIN = os.name == "nt"
VPY = HOME / "venv" / ("Scripts/python.exe" if WIN else "bin/python")
REQS = ["faster-whisper", "edge-tts", "numpy", "pillow", "soundfile", "requests"]
GPU_REQS = ["nvidia-cublas-cu12", "nvidia-cudnn-cu12==9.*"]

DEFAULT_CONFIG = {
    "output_dir": None,  # null -> <cwd>/reel-productions
    "voice": {"provider": "elevenlabs", "voice_id": "TX3LPaxmHKxFdv7VOQHJ", "model_id": "eleven_v3",
              "edge_voice": "en-US-AndrewMultilingualNeural", "speed": 1.08},
    "music": {"provider": "elevenlabs", "model_id": "music_v2"},
    "images": {"provider": "elevenlabs", "model_id": "gpt-image-2", "quality": "medium", "max_per_reel": 4},
    "video_gen": {"enabled": False, "model_id": "bytedance-seedance-v2-fast", "max_clips": 1},
    "avatar": {"enabled": False, "image": None, "model_id": "creatify-aurora"},
    "brand": {"handle": "", "default_theme": None, "accent": None, "cta": "comment"},
    "language": "en",
    "browser_capture": False,  # agent-browser use needs explicit opt-in
    "modes": {"ask": True},  # ask which creation mode to use (False = AI Select every time)
    "whisper": {"model": "small"},  # tiny | base | small | medium (local transcription for alignment, QA, analysis)
}


def tuned_config():
    """first-run defaults adapted to this machine (from probe.py's profile)"""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    prof_f = HOME / "profile.json"
    if not prof_f.exists():
        return cfg
    prof = json.loads(prof_f.read_text(encoding="utf-8"))
    el = prof["optional"]["elevenlabs"]
    if not el.get("logged_in"):  # no premium services: free providers, no generated images
        cfg["voice"]["provider"] = "edge"
        cfg["music"]["provider"] = "openverse"
        cfg["images"]["max_per_reel"] = 0
    if (prof["system"].get("ram_gb") or 8) < 6 and not prof["system"].get("gpu"):
        cfg["whisper"]["model"] = "base"
    return cfg


def eleven_key_to_keyring():
    """ELEVENLABS_API_KEY set but the CLI not logged in -> store it in the CLI keyring (never printed)"""
    key = os.environ.get("ELEVENLABS_API_KEY")
    exe = which("elevenlabs") or which("elevenlabs.cmd")
    if not key or not exe:
        return
    r = subprocess.run([exe, "user", "subscription", "get", "--format", "json"], capture_output=True, text=True, shell=WIN)
    if r.returncode == 0:
        return
    r = subprocess.run([exe, "auth", "login", "--with-token"], input=key, capture_output=True, text=True, shell=WIN)
    print("elevenlabs: API key from ELEVENLABS_API_KEY stored in the CLI keyring" if r.returncode == 0 else "elevenlabs: could not store the API key (run `elevenlabs auth login` manually)")


def sh(cmd, **kw):
    print("$", " ".join(map(str, cmd)), flush=True)
    return subprocess.run(list(map(str, cmd)), **kw)


def which(x):
    return shutil.which(x)


def lock_hash():
    return hashlib.md5((PLUGIN / "engine" / "package-lock.json").read_bytes()).hexdigest()


def sync_engine():
    """copy engine source from plugin to runtime home; npm ci when the lockfile changed."""
    dst = HOME / "engine"
    dst.mkdir(parents=True, exist_ok=True)
    src = PLUGIN / "engine"
    if (dst / "src").exists():
        shutil.rmtree(dst / "src")
    shutil.copytree(src / "src", dst / "src")
    for f in ["package.json", "package-lock.json", "remotion.config.ts", "tsconfig.json"]:
        shutil.copy2(src / f, dst / f)
    stamp = dst / ".lockhash"
    if not (dst / "node_modules").exists() or not stamp.exists() or stamp.read_text() != lock_hash():
        npm = which("npm") or which("npm.cmd")
        if not npm:
            sys.exit("npm not found: install Node.js 20+ first")
        sh([npm, "ci", "--no-fund", "--no-audit", "--loglevel=error"], cwd=dst, check=True, shell=WIN)
        stamp.write_text(lock_hash())


def setup():
    HOME.mkdir(parents=True, exist_ok=True)
    if subprocess.run([sys.executable, PLUGIN / "scripts" / "probe.py", "--quiet"]).returncode != 0:
        sys.exit("blockers found: run `python rf.py probe` and install what it lists, then re-run setup")
    eleven_key_to_keyring()
    if not VPY.exists():
        uv = which("uv")
        if uv:
            sh([uv, "venv", HOME / "venv", "--python", "3.10"], check=True)
        else:
            sh([sys.executable, "-m", "venv", HOME / "venv"], check=True)
    reqs = REQS + (GPU_REQS if which("nvidia-smi") else [])
    uv = which("uv")
    if uv:
        sh([uv, "pip", "install", "--python", VPY, *reqs], check=True)
    else:
        sh([VPY, "-m", "pip", "install", "-q", *reqs], check=True)
    sync_engine()
    sh([VPY, PLUGIN / "scripts" / "sfx_kit.py", HOME / "sfx"], check=True)
    cfg = HOME / "config.json"
    if not cfg.exists():
        cfg.write_text(json.dumps(tuned_config(), indent=2))  # never overwrites an existing config
    (HOME / "VERSION").write_text(json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"])
    print(f"\nreel-factory ready at {HOME}")
    doctor()


def doctor():
    ok = lambda b: "OK  " if b else "--  "
    print(ok(VPY.exists()), "runtime venv", VPY)
    print(ok((HOME / "engine" / "node_modules").exists()), "remotion engine deps")
    print(ok((HOME / "sfx" / "whoosh.wav").exists()), "sfx kit")
    print(ok((HOME / "config.json").exists()), "config", HOME / "config.json")
    for t in ["ffmpeg", "node", "nvidia-smi", "elevenlabs", "agent-browser"]:
        print(ok(which(t)), t)
    if which("elevenlabs"):
        r = subprocess.run(["elevenlabs", "user", "subscription", "get", "--format", "json"], capture_output=True, text=True, shell=WIN)
        try:
            d = json.loads(r.stdout)
            print("OK   elevenlabs credits:", d["character_limit"] - d["character_count"], "of", d["character_limit"], f"({d['tier']})")
        except Exception:
            print("--   elevenlabs not authenticated (run: elevenlabs auth login) -> free fallbacks will be used")
    plugin_ver = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
    home_ver = (HOME / "VERSION").read_text().strip() if (HOME / "VERSION").exists() else None
    print(ok(plugin_ver == home_ver), f"runtime version {home_ver} vs plugin {plugin_ver}" + ("" if plugin_ver == home_ver else "  -> run setup"))


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "setup":
        return setup()
    if cmd == "doctor":
        return doctor()
    if cmd == "probe":  # stdlib only: must work before the venv exists
        sys.exit(subprocess.run([sys.executable, PLUGIN / "scripts" / "probe.py", *args]).returncode)
    if not VPY.exists():
        sys.exit("runtime not installed: run `python rf.py setup` first")
    # keep runtime engine in sync with plugin source on every render (cheap copy)
    if cmd == "render":
        sync_engine()
    script = PLUGIN / "scripts" / f"{cmd}.py"
    if not script.exists():
        sys.exit(f"unknown tool {cmd}")
    env = dict(os.environ, REEL_FACTORY_HOME=str(HOME), REEL_FACTORY_PLUGIN=str(PLUGIN), PYTHONIOENCODING="utf-8")
    sys.exit(subprocess.run([str(VPY), str(script), *args], env=env).returncode)


if __name__ == "__main__":
    main()
