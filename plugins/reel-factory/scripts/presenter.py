"""AI presenter: one consistent avatar, lip-synced to the reel's final voice-over.

usage:
  rf presenter setup --image PORTRAIT [--name presenter-m1] [--voice VOICE_ID]
        register an avatar: ~/.reel-factory/avatars/<name>/{portrait.png, base.mp4, profile.json}. The portrait must be an
        ORIGINAL character (generated) or a person who consented. base.mp4 = a 6 s idle clip with subtle natural head motion
        built from the portrait (local lip-sync re-animates the mouth on top of it).
  rf presenter <prod> [--provider heygen|musetalk] [--avatar NAME]
        talking-head video for <prod>/public/vo.mp3 -> <prod>/public/avatar.mp4 (same length, lips synced to the take).
        Storyboard: scenes of type "presenter" show it full-frame (cut in sync), or meta.layout "split-avatar".

Providers (config presenter.provider, fallback order presenter.fallback):
  heygen    HeyGen API v3 (image subject + our ElevenLabs audio). Key: HEYGEN_API_KEY in ~/.reel-factory/.env. Paid per minute.
  musetalk  local MuseTalk 1.5 (fp16) on the GPU: free, slow (~4-5 min per 10 s on a 4 GB laptop GPU), mouth-only.
Disclose the AI presenter in the caption (Instagram "AI info").
"""
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
import requests
from common import HOME, config, duration, load_json, log, run, save_json

AV = HOME / "avatars"
MT = HOME / "presenter" / "MuseTalk"
MPY = HOME / "presenter" / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def env(k):
    if os.environ.get(k):
        return os.environ[k]
    f = HOME / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


# ---------- avatar identity ----------

def setup(image, name, voice=None, crop=None):
    from PIL import Image
    d = AV / name
    d.mkdir(parents=True, exist_ok=True)
    im = Image.open(image).convert("RGB")
    if crop:
        x, y, w, h = [int(v) for v in crop.split(",")]
        im = im.crop((x, y, x + w, y + h))
    # 9:16 portrait canvas at >= 720 px wide (lip-sync models need a clear, large face)
    tw = max(720, im.width)
    th = int(tw * 16 / 9)
    scale = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - tw) // 2, max(0, (im.height - th) // 3)
    im = im.crop((left, top, left + tw, top + th))
    im.save(d / "portrait.png")
    # idle base clip: slow breathing zoom + gentle sway (natural head motion; lips come from the lip-sync model)
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", d / "portrait.png", "-t", "6", "-vf",
         f"scale={tw * 2}:-1,zoompan=z='1.04+0.012*sin(2*PI*on/150)':x='iw/2-(iw/zoom/2)+6*sin(2*PI*on/180)':"
         f"y='ih/2-(ih/zoom/2)+4*sin(2*PI*on/130)':d=1:s={tw}x{th}:fps=25,format=yuv420p",
         "-c:v", "libx264", "-crf", "16", d / "base.mp4"])
    (d / "base_coords.pkl").unlink(missing_ok=True)  # new idle clip -> MuseTalk landmark cache is stale
    prof = load_json(d / "profile.json") if (d / "profile.json").exists() else {}
    prof.update({"name": name, "portrait": "portrait.png", "base_clip": "base.mp4", "size": [tw, th],
                 "voice_id": voice or prof.get("voice_id") or config().get("voice", {}).get("voice_id"),
                 "disclosure": "AI-generated presenter", "created": time.strftime("%Y-%m-%d")})
    save_json(d / "profile.json", prof)
    print(json.dumps(prof, indent=2))


# ---------- providers ----------

def heygen(prof, d, vo, out):
    key = env("HEYGEN_API_KEY")
    if not key:
        raise RuntimeError("HEYGEN_API_KEY not set (rf setup heygen, or add it to ~/.reel-factory/.env)")
    H = {"x-api-key": key}
    up = lambda p: requests.post("https://api.heygen.com/v3/assets", headers=H, files={"file": open(p, "rb")}, timeout=300).json()["data"]["asset_id"]
    if not prof.get("heygen_image_asset"):
        prof["heygen_image_asset"] = up(d / "portrait.png")
        save_json(d / "profile.json", prof)
    audio = up(vo)
    body = {"type": "image", "image": {"type": "asset_id", "asset_id": prof["heygen_image_asset"]}, "audio_asset_id": audio,
            "aspect_ratio": "9:16", "resolution": "1080p", "title": f"reel-factory {d.name}"}
    r = requests.post("https://api.heygen.com/v3/videos", headers={**H, "Content-Type": "application/json"}, json=body, timeout=120).json()
    vid = (r.get("data") or {}).get("video_id") or r.get("video_id")
    if not vid:
        raise RuntimeError(f"heygen create failed: {json.dumps(r)[:300]}")
    for _ in range(240):
        time.sleep(10)
        s = requests.get(f"https://api.heygen.com/v3/videos/{vid}", headers=H, timeout=60).json()
        s = s.get("data") or s
        if s.get("status") == "completed":
            Path(out).write_bytes(requests.get(s["video_url"], timeout=600).content)
            return
        if s.get("status") in ("failed", "error"):
            raise RuntimeError(f"heygen failed: {s.get('error') or s}")
    raise RuntimeError("heygen timeout")


def musetalk(prof, d, vo, out):
    if not MPY.exists() or not (MT / "models" / "musetalkV15" / "unet.pth").exists():
        raise RuntimeError("MuseTalk not installed: bash \"${CLAUDE_PLUGIN_ROOT}/scripts/install_musetalk.sh\"")
    out, vo = Path(out).resolve(), Path(vo).resolve()  # MuseTalk runs from its own folder: absolute paths only
    work = out.parent / "presenter_work"
    work.mkdir(parents=True, exist_ok=True)
    wav = work / "vo.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", vo, "-ac", "1", "-ar", "16000", wav])
    cfg = work / "task.yaml"
    cfg.write_text(f'task_0:\n  video_path: "{(d / prof["base_clip"]).as_posix()}"\n  audio_path: "{wav.as_posix()}"\n  result_name: "avatar_raw.mp4"\n', encoding="utf-8")
    ffdir = str(Path(shutil.which("ffmpeg")).parent)
    cmd = [str(MPY), "-m", "scripts.inference", "--inference_config", str(cfg), "--result_dir", str(work / "res"),
           "--unet_model_path", "models/musetalkV15/unet.pth", "--unet_config", "models/musetalkV15/musetalk.json",
           "--version", "v15", "--use_float16", "--batch_size", str(config().get("presenter", {}).get("batch", 4)),
           "--ffmpeg_path", ffdir, "--fps", "25", "--saved_coord", "--use_saved_coord"]
    # face landmarks of the idle clip are per-avatar, not per-reel: cache them (CPU pass ~8 min on a laptop)
    coords, wcoords = d / "base_coords.pkl", work / (Path(prof["base_clip"]).stem + ".pkl")
    if coords.exists():
        shutil.copy(coords, wcoords)
    t0 = time.time()
    # landmark/face detection on CPU (one pass over the 6 s base clip): the pose model's CUDA kernels crash on some
    # laptop GPUs ("illegal instruction"); the lip-sync UNet itself stays on the GPU
    menv = {**os.environ, "MUSETALK_PREPROC_DEVICE": config().get("presenter", {}).get("preproc_device", "cpu")}
    # stream the log live; kill if it stops growing (a wedged GPU/CPU stage otherwise hangs forever)
    lp = work / "musetalk.log"
    stall = config().get("presenter", {}).get("stall_seconds", 600)
    with open(lp, "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen(cmd, cwd=MT, stdout=lf, stderr=subprocess.STDOUT, env=menv)
        last, size = time.time(), 0
        while p.poll() is None:
            time.sleep(5)
            s = lp.stat().st_size
            if s != size:
                last, size = time.time(), s
            elif time.time() - last > stall:
                subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True) if os.name == "nt" else p.kill()
                raise RuntimeError(f"musetalk stalled: no log output for {stall}s (see {lp})")
    if wcoords.exists() and not coords.exists():
        shutil.copy(wcoords, coords)
    res = next((work / "res").rglob("avatar_raw.mp4"), None)
    if p.returncode != 0 or not res:
        raise RuntimeError(f"musetalk failed (see {lp}): {lp.read_text(encoding='utf-8', errors='replace')[-400:]}")
    # 30 fps, the take's exact audio, faststart
    run(["ffmpeg", "-y", "-v", "error", "-i", res, "-i", vo, "-map", "0:v", "-map", "1:a", "-r", "30", "-c:v", "libx264", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    print(f"musetalk: {duration(out):.1f}s video in {time.time() - t0:.0f}s", file=sys.stderr)


PROVIDERS = {"heygen": heygen, "musetalk": musetalk}


def windows(prod, pad=0.25):
    """Reel-time spans of `presenter` scenes, each with its offset inside the cut audio. [] -> lip-sync the full VO
    (split-avatar layout shows the presenter all the way through)."""
    sb = load_json(prod / "storyboard.json")
    if sb["meta"].get("layout") == "split-avatar" or not (prod / "words.json").exists():
        return []
    words = load_json(prod / "words.json")
    ids, first = [s["id"] for s in sb["scenes"]], {}
    for w in words:
        first.setdefault(w["scene"], w["s"])
    out, off = [], 0.0
    for i, s in enumerate(sb["scenes"]):
        if s["type"] != "presenter":
            continue
        a = 0.0 if i == 0 else max(0.0, first[s["id"]] - pad)
        b = (first[ids[i + 1]] if i + 1 < len(ids) else words[-1]["e"]) + pad
        out.append({"scene": s["id"], "start": round(a, 3), "end": round(b, 3), "offset": round(off, 3)})
        off += b - a
    return out


def make(prod, provider=None, avatar=None):
    prod = Path(prod).resolve()
    pc = config().get("presenter", {})
    name = avatar or pc.get("avatar", "presenter-m1")
    d = AV / name
    if not (d / "profile.json").exists():
        raise SystemExit(f"avatar {name} not set up: rf presenter setup --image <portrait> --name {name}")
    prof = load_json(d / "profile.json")
    vo = prod / "public" / "vo.mp3"
    out = prod / "public" / "avatar.mp4"
    wins = windows(prod)
    if wins:  # lip-sync only the presenter scenes (5x less GPU time / HeyGen minutes); build maps scene -> offset
        work = out.parent / "presenter_work"
        work.mkdir(parents=True, exist_ok=True)
        cut = work / "vo_windows.wav"
        fc = "".join(f"[0:a]atrim={w['start']:.3f}:{w['end']:.3f},asetpts=PTS-STARTPTS[a{i}];" for i, w in enumerate(wins))
        fc += "".join(f"[a{i}]" for i in range(len(wins))) + f"concat=n={len(wins)}:v=0:a=1[o]"
        run(["ffmpeg", "-y", "-v", "error", "-i", vo, "-filter_complex", fc, "-map", "[o]", "-ar", "44100", cut])
        vo = cut
        log(prod, f"presenter: {len(wins)} windows · {sum(w['end'] - w['start'] for w in wins):.1f}s of speech to lip-sync")
    order = [provider] if provider else [pc.get("provider", "heygen")] + [p for p in pc.get("fallback", ["musetalk"]) if p != pc.get("provider", "heygen")]
    errs = []
    for p in order:
        try:
            PROVIDERS[p](prof, d, vo, out)
            sb = load_json(prod / "storyboard.json")
            sb["avatar"] = {"src": "avatar.mp4", "provider": p, "name": name, **({"windows": wins} if wins else {})}
            save_json(prod / "storyboard.json", sb)
            return log(prod, f"presenter: {p} · {name} · {duration(out):.1f}s -> public/avatar.mp4 (disclose: AI-generated presenter)")
        except Exception as e:
            errs.append(f"{p}: {str(e)[:200]}")
            log(prod, f"presenter: {p} unavailable/failed -> next ({str(e)[:160]})")
    raise SystemExit("presenter: all providers failed: " + " | ".join(errs))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        ap = argparse.ArgumentParser()
        ap.add_argument("setup"); ap.add_argument("--image", required=True); ap.add_argument("--name", default="presenter-m1")
        ap.add_argument("--voice"); ap.add_argument("--crop", help="x,y,w,h crop of the source image (remove watermarks/borders)")
        a = ap.parse_args()
        return setup(a.image, a.name, a.voice, a.crop)
    ap = argparse.ArgumentParser()
    ap.add_argument("prod"); ap.add_argument("--provider", choices=list(PROVIDERS)); ap.add_argument("--avatar")
    a = ap.parse_args()
    make(a.prod, a.provider, a.avatar)


if __name__ == "__main__":
    main()
