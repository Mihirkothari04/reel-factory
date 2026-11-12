"""System probe: detect what THIS machine can do, decide how each pipeline stage will run, and list what to ask for.

usage: rf probe [--json] [--quiet]

Runs with any Python 3.8+ (no venv needed, stdlib only), so it works before `rf setup`.
Writes ~/.reel-factory/profile.json:
  system       os, arch, cpus, RAM, free disk, GPU (NVIDIA name + VRAM, or Apple Silicon)
  required     python>=3.10, node>=20, npm, ffmpeg, ffprobe, >=3 GB free disk  -> missing = blocker (with install hint)
  optional     uv, elevenlabs CLI + login + credits, ELEVENLABS_API_KEY, agent-browser, network
  runtime      venv, engine deps, sfx kit, version match
  plan         per stage: provider chosen + quality note (premium / free / degraded)
  blockers     things that stop a run (must be fixed or installed)
  asks         decisions/inputs worth asking the user once (premium voice? brand? footage?)
The skill reads this file at stage 0 and either asks for what is missing or proceeds with what is there.
"""
import json, os, platform, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
HOME = Path(os.environ.get("REEL_FACTORY_HOME", Path.home() / ".reel-factory"))
PLUGIN = Path(__file__).resolve().parent.parent
WIN = os.name == "nt"
OSN = {"Windows": "windows", "Darwin": "macos"}.get(platform.system(), "linux")

HINTS = {
    "node": {"windows": "winget install OpenJS.NodeJS.LTS", "macos": "brew install node", "linux": "install Node 20+ (e.g. https://nodejs.org or `sudo apt install nodejs npm` on recent distros)"},
    "ffmpeg": {"windows": "winget install Gyan.FFmpeg", "macos": "brew install ffmpeg", "linux": "sudo apt install ffmpeg  (or dnf/pacman equivalent)"},
    "python": {"windows": "winget install Python.Python.3.12", "macos": "brew install python@3.12", "linux": "sudo apt install python3.12 python3.12-venv"},
    "uv": {"windows": "winget install astral-sh.uv", "macos": "brew install uv", "linux": "curl -LsSf https://astral.sh/uv/install.sh | sh"},
    "elevenlabs": {"all": "npm i -g @elevenlabs/cli  then  elevenlabs auth login  (or: set ELEVENLABS_API_KEY and run `rf setup`)"},
    "agent-browser": {"all": "npm i -g agent-browser && agent-browser install  (optional; only used when browser_capture is enabled)"},
}


def run(cmd, timeout=20):
    exe = shutil.which(cmd[0]) or (shutil.which(cmd[0] + ".cmd") if WIN else None)
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception:
        return None


def ver(text):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    return tuple(int(x or 0) for x in m.groups()) if m else None


def ram_gb():
    try:
        if WIN:
            import ctypes
            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("avail", ctypes.c_ulonglong),
                            ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong)]
            m = MS(); m.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.total / 2**30, 1)
        if OSN == "macos":
            return round(int(run(["sysctl", "-n", "hw.memsize"]).strip()) / 2**30, 1)
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30, 1)
    except Exception:
        return None


def gpu():
    out = run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    if out and "," in out:
        name, mem = out.strip().splitlines()[0].split(",")[:2]
        return {"kind": "nvidia", "name": name.strip(), "vram_gb": round(int(mem.strip()) / 1024, 1)}
    if OSN == "macos" and platform.machine() == "arm64":
        return {"kind": "apple", "name": "Apple Silicon", "vram_gb": None}
    return None


def online(url):
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers={"User-Agent": "reel-factory-probe"}), timeout=6)
        return True
    except Exception as e:
        return getattr(e, "code", None) is not None  # an HTTP error still means we reached the host


def eleven_state():
    st = {"cli": bool(shutil.which("elevenlabs") or (WIN and shutil.which("elevenlabs.cmd"))), "logged_in": False, "credits": None, "tier": None,
          "env_key": bool(os.environ.get("ELEVENLABS_API_KEY"))}
    if st["cli"]:
        out = run(["elevenlabs", "user", "subscription", "get", "--format", "json"], timeout=30)
        try:
            d = json.loads(out[out.index("{"):out.rindex("}") + 1])
            st.update(logged_in=True, credits=d["character_limit"] - d["character_count"], tier=d.get("tier"))
        except Exception:
            pass
    return st


def main():
    sysinfo = {"os": OSN, "os_version": platform.release(), "arch": platform.machine(), "cpus": os.cpu_count(), "ram_gb": ram_gb(),
               "disk_free_gb": round(shutil.disk_usage(HOME.parent if HOME.parent.exists() else Path.home()).free / 2**30, 1), "gpu": gpu()}
    py = sys.version_info[:3]
    node = ver(run(["node", "--version"]))
    req = {
        "python": {"ok": py >= (3, 10), "found": ".".join(map(str, py)), "need": ">=3.10"},
        "node": {"ok": bool(node and node >= (20, 0, 0)), "found": ".".join(map(str, node)) if node else None, "need": ">=20"},
        "npm": {"ok": bool(shutil.which("npm") or shutil.which("npm.cmd")), "need": "with node"},
        "ffmpeg": {"ok": bool(shutil.which("ffmpeg")), "need": "any recent"},
        "ffprobe": {"ok": bool(shutil.which("ffprobe")), "need": "ships with ffmpeg"},
        "disk": {"ok": sysinfo["disk_free_gb"] >= 3, "found": f"{sysinfo['disk_free_gb']} GB", "need": ">=3 GB free"},
    }
    el = eleven_state()
    opt = {"uv": bool(shutil.which("uv")), "elevenlabs": el, "agent_browser": bool(shutil.which("agent-browser")),
           "claude_cli": bool(shutil.which("claude")),
           "network": {"github": online("https://api.github.com"), "openverse": online("https://api.openverse.org/v1/audio/?q=test"),
                       "edge_tts": online("https://speech.platform.bing.com")}}
    vpy = HOME / "venv" / ("Scripts/python.exe" if WIN else "bin/python")
    pv = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
    hv = (HOME / "VERSION").read_text().strip() if (HOME / "VERSION").exists() else None
    rt = {"venv": vpy.exists(), "engine": (HOME / "engine" / "node_modules").exists(), "sfx": (HOME / "sfx" / "whoosh.wav").exists(),
          "config": (HOME / "config.json").exists(), "version": hv, "plugin_version": pv, "current": hv == pv}
    cfg = json.loads((HOME / "config.json").read_text()) if rt["config"] else {}

    g = sysinfo["gpu"]
    premium = el["logged_in"] and (el["credits"] or 0) > 3000
    low_ram = (sysinfo["ram_gb"] or 8) < 6
    plan = {
        "voice": "elevenlabs (premium, exact timestamps)" if premium else ("edge-tts (free neural voice) + Whisper alignment" if opt["network"]["edge_tts"] else "BLOCKED: no TTS reachable (edge-tts needs internet)"),
        "music": "elevenlabs music (custom, exact length)" if premium else ("openverse CC library (free, credited)" if opt["network"]["openverse"] else "none (render without a bed)"),
        "images": f"elevenlabs flows (budget {cfg.get('images', {}).get('max_per_reel', 4)}/reel)" if premium else "none: rebuilt UI, diagrams and og:images only",
        "video_broll": "elevenlabs flows" if premium and cfg.get("video_gen", {}).get("enabled") else "off",
        "avatar": "creatify-aurora" if premium and cfg.get("avatar", {}).get("enabled") and cfg.get("avatar", {}).get("image") else "off (presenter mode needs your own footage)",
        "whisper": ("CUDA (" + g["name"] + ")") if g and g["kind"] == "nvidia" else ("CPU int8 (base model: low RAM)" if low_ram else "CPU int8 (small model; slower but fine)"),
        "trends": "GitHub + HN + Hugging Face + Lobsters" if opt["network"]["github"] else "web search only",
        "browser_capture": "agent-browser (enabled)" if opt["agent_browser"] and cfg.get("browser_capture") else "off (APIs, og:images, rebuilt UI)",
        "render": "remotion (local)" if req["node"]["ok"] else "BLOCKED: needs node 20+",
    }
    blockers = [{"what": k, "need": v["need"], "found": v.get("found"), "fix": (HINTS.get(k if k != "ffprobe" else "ffmpeg") or {}).get(OSN) or "free disk space"}
                for k, v in req.items() if not v["ok"]]
    blockers += [{"what": k, "need": "network", "fix": "check the internet connection"} for k, v in plan.items() if str(v).startswith("BLOCKED") and k == "voice"]
    asks = []
    if not premium:
        asks.append({"id": "premium", "why": "voice, music and images run on free fallbacks (good, not top tier)",
                     "options": ["stay free", "log in to ElevenLabs (elevenlabs auth login)", "provide ELEVENLABS_API_KEY"],
                     "hint": HINTS["elevenlabs"]["all"] if not el["cli"] else ("env key found: rf setup stores it in the CLI keyring" if el["env_key"] else "elevenlabs auth login")})
    elif el["credits"] is not None and el["credits"] < 20000:
        asks.append({"id": "credits_low", "why": f"only {el['credits']} ElevenLabs credits left (~1,000-2,500 per reel)"})
    if not (cfg.get("brand") or {}).get("handle"):
        asks.append({"id": "brand", "why": "no handle/accent set: reels ship unbranded", "options": ["set brand.handle and brand.accent", "skip"]})
    if not opt["uv"]:
        asks.append({"id": "uv", "why": "optional: makes setup ~5x faster", "hint": HINTS["uv"][OSN]})
    if not rt["venv"] or not rt["current"]:
        asks.append({"id": "setup", "why": "runtime missing or out of date", "hint": "rf setup (5-10 min, downloads ~1.5 GB: Python packages, Remotion, Chromium headless)"})

    prof = {"system": sysinfo, "required": req, "optional": opt, "runtime": rt, "plan": plan, "blockers": blockers, "asks": asks,
            "ready": not blockers and rt["venv"] and rt["engine"] and rt["current"]}
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / "profile.json").write_text(json.dumps(prof, indent=2), encoding="utf-8")
    if "--json" in sys.argv:
        print(json.dumps(prof, indent=1)); return
    if "--quiet" in sys.argv:
        sys.exit(1 if blockers else 0)
    s = sysinfo
    print(f"system   {s['os']} {s['os_version']} {s['arch']} · {s['cpus']} cpu · {s['ram_gb']} GB RAM · {s['disk_free_gb']} GB free · GPU {g['name'] if g else 'none'}")
    for k, v in req.items():
        print(("OK  " if v["ok"] else "MISS"), f"{k:8} {v.get('found') or ''} (need {v['need']})")
    print(f"runtime  venv {rt['venv']} · engine {rt['engine']} · version {rt['version']} vs plugin {rt['plugin_version']}")
    print("plan:"); [print(f"  {k:15} {v}") for k, v in plan.items()]
    for b in blockers:
        print(f"BLOCKER  {b['what']} ({b['need']}) -> {b['fix']}")
    for a in asks:
        print(f"ASK      {a['id']}: {a['why']}" + (f"  [{a['hint']}]" if a.get("hint") else ""))
    print("READY" if prof["ready"] else ("NOT READY: fix the blockers above, then run `rf setup`" if blockers else "NOT READY: run `rf setup` once"))
    sys.exit(1 if blockers else 0)


if __name__ == "__main__":
    main()
