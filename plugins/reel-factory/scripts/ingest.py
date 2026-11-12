"""Ingest a new batch of reference reels into the library: dedup first, then analyse only what is new.

usage: rf ingest <folder or video> [...] [--batch NAME] [--source-root DIR] [--dry-run]

1. Fingerprint every input video (per-frame 9x8 dHash at 2 fps, centre crop too -> survives re-encodes,
   720p downscales, trims and screen-record bars). Fingerprints are cached as <library>/<slug>/fp.npz.
2. Duplicates: exact md5, or coarse overlap >= 0.90 verified by a 17x16 fine hash >= 0.60, against (a) every library reel and (b) earlier files
   in the same batch. Duplicates are NOT re-analysed (saves GPU time and avoids double-counting patterns).
3. New reels -> analyze() into ~/.reel-factory/library/<slug>/ (metrics, transcript, sheet) + batch tag.
4. Writes <library>/_batches/<batch>.json: new / duplicate-of / skipped, so /reel-learn knows what to review.

Library reels analysed before fingerprints existed get one backfilled from their recorded source path
(metrics.json "file", resolved against --source-root or cwd) when that file still exists.
"""
import argparse, hashlib, subprocess, sys, time
from pathlib import Path
import numpy as np
from common import HOME, load_json, save_json

LIB = HOME / "library"
EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
DUP = 0.90       # coarse candidate threshold
FINE_DUP = 0.60  # fine-hash verification (calibrated batch-02: true dups 0.82-1.00, tweet-frame false positive 0.00)


# coarse 9x8 dHash finds candidates fast; a 17x16 "fine" hash verifies them, because shared layouts
# (black tweet-frame reposts, same creator template) make coarse hashes collide across different reels.
SIZES = {"full": (1.0, 9, 8), "crop": (0.7, 9, 8), "fine": (0.7, 17, 16)}
THR = {"full": 10, "crop": 10, "fine": 48}


def fingerprint(p: Path, keys=("full", "crop", "fine")):
    out = {}
    for name in keys:
        crop, w, h = SIZES[name]
        vf = f"fps=2,crop=iw*{crop}:ih*{crop},scale={w}:{h}:flags=area,format=gray"
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", vf, "-f", "rawvideo", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
        bits = (a[:, :, 1:] > a[:, :, :-1]).reshape(len(a), (w - 1) * h)
        keep = a.reshape(len(a), -1).std(axis=1) > 6  # flat/black frames match everything
        out[name] = np.packbits(bits[keep], axis=1)
    return out


def overlap(A, B, thr=10):
    """fraction of A's frames with a near match (hamming <= thr) in B"""
    if len(A) == 0 or len(B) == 0:
        return 0.0
    x = np.unpackbits(A[:, None, :] ^ B[None, :, :], axis=2).sum(axis=2)
    return float((x.min(axis=1) <= thr).mean())


def similarity(fa, fb, keys=("full", "crop")):
    return max(max(overlap(fa[k], fb[k], THR[k]), overlap(fb[k], fa[k], THR[k])) for k in keys)


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def library_index(source_root: Path):
    """[(slug, fp, md5)] for every library reel we can fingerprint"""
    idx = []
    for d in sorted(x for x in LIB.iterdir() if x.is_dir() and not x.name.startswith("_")):
        fpf = d / "fp.npz"
        if not fpf.exists():
            m = d / "metrics.json"
            src = Path(load_json(m)["file"]) if m.exists() else None
            if src and not src.is_absolute():
                src = source_root / src
            if not (src and src.exists()):
                continue
            fp = fingerprint(src)
            np.savez_compressed(fpf, md5=md5(src), **fp)
            print(f"  backfilled fingerprint {d.name}", flush=True)
        z = np.load(fpf)
        idx.append((d.name, {k: z[k] for k in z.files if k != "md5"}, str(z["md5"])))
    return idx


def fine_for(slug_, source_root):
    """compute + cache the fine hash for a library reel fingerprinted before it existed"""
    d = LIB / slug_
    src = Path(load_json(d / "metrics.json")["file"])
    src = src if src.is_absolute() else source_root / src
    if not src.exists():
        return {"fine": np.zeros((0, 32), np.uint8)}
    fine = fingerprint(src, ("fine",))
    z = dict(np.load(d / "fp.npz"))
    z.update(fine)
    np.savez_compressed(d / "fp.npz", **z)
    return fine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--batch", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--source-root", default=".")
    ap.add_argument("--dry-run", action="store_true", help="dedup report only, no analysis")
    a = ap.parse_args()
    files = []
    for i in map(Path, a.inputs):
        files += sorted(f for f in (i.rglob("*") if i.is_dir() else [i]) if f.suffix.lower() in EXT and "_duplicates" not in f.parts)
    LIB.mkdir(parents=True, exist_ok=True)
    print(f"library: indexing fingerprints…", flush=True)
    idx = library_index(Path(a.source_root).resolve())
    print(f"library: {len(idx)} fingerprinted reels · batch: {len(files)} files", flush=True)

    idx_map = {sl: fp for sl, fp, _ in idx}
    from analyze import analyze, slug  # heavy imports (whisper) only after dedup
    bf = LIB / "_batches" / f"{a.batch}.json"
    report = load_json(bf) if bf.exists() else {"batch": a.batch, "date": time.strftime("%Y-%m-%d"), "new": [], "duplicates": []}
    done = {e["file"] for e in report["new"] + report["duplicates"]}  # re-run on a grown folder: only new files
    seen = []  # (path, fp, md5) of this batch's unique files
    for f in files:
        if str(f) in done:
            continue
        fp, h = fingerprint(f), md5(f)
        best = max(((s, 1.01 if m == h else similarity(fp, lf)) for s, lf, m in idx), key=lambda x: x[1], default=(None, 0))
        inb = max(((str(p), 1.01 if m == h else similarity(fp, pf)) for p, pf, m in seen), key=lambda x: x[1], default=(None, 0))
        hit = max(best, inb, key=lambda x: x[1])
        if DUP <= hit[1] <= 1.0:  # perceptual candidate -> verify with the fine hash
            other = dict(idx_map.get(hit[0]) or next(pf for p, pf, _ in seen if str(p) == hit[0]))
            if "fine" not in other:
                other.update(fine_for(hit[0], Path(a.source_root).resolve()))
            fine = similarity(fp, other, ("fine",))
            print(f"     verify {f.name[:50]} vs {hit[0][:40]}: coarse {hit[1]:.2f} fine {fine:.2f}", flush=True)
            if fine < FINE_DUP:
                hit = (hit[0], fine)  # shared layout, different reel
        if hit[1] >= DUP:
            report["duplicates"].append({"file": str(f), "duplicate_of": hit[0], "score": round(min(hit[1], 1.0), 3), "exact": hit[1] > 1.0})
            print(f"DUP  {hit[1]:.2f} {f.name[:70]}  ==  {hit[0][:60]}", flush=True)
            continue
        seen.append((f, fp, h))
        entry = {"file": str(f), "slug": slug(f), "closest": best[0], "closest_score": round(best[1], 3)}
        report["new"].append(entry)
        print(f"NEW  {f.name[:70]}  (closest library {best[1]:.2f})", flush=True)
        if not a.dry_run:
            o = analyze(f, LIB)
            np.savez_compressed(o / "fp.npz", md5=h, **fp)
            m = load_json(o / "metrics.json")
            m["batch"] = a.batch
            save_json(o / "metrics.json", m)
    if not a.dry_run:
        save_json(bf, report)
    print(f"\n{len(report['new'])} new · {len(report['duplicates'])} duplicates" + ("" if a.dry_run else f" -> {LIB / '_batches' / (a.batch + '.json')}"))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        z = np.packbits(np.zeros((3, 64), bool), axis=1)
        o = np.packbits(np.ones((3, 64), bool), axis=1)
        assert overlap(z, z) == 1.0 and overlap(z, z[:0]) == 0.0 and overlap(z, o) == 0.0
        print("ok")
    else:
        main()
