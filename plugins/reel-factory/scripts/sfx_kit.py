"""Procedurally synthesise a small, subtle SFX kit (free, offline, deterministic).

Usage: python tools/sfx_kit.py <out_dir>
Writes whoosh.wav, pop.wav, click.wav, tick.wav, type.wav, riser.wav, ding.wav, impact.wav, swipe.wav.
Matches the corpus finding: SFX are functional and quiet (transitions, card pops, typing, counters, CTA ding).
"""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

SR = 48000
rng = np.random.default_rng(7)


def env(n, a, d, curve=3.0):
    """attack/decay envelope, a+d in samples"""
    e = np.zeros(n)
    a = max(1, a)
    e[:a] = np.linspace(0, 1, a)
    rest = n - a
    e[a:] = (1 - np.linspace(0, 1, rest)) ** curve
    return e


def lowpass(x, cutoff):
    """one-pole lowpass; cutoff may be an array (time-varying)"""
    cutoff = np.broadcast_to(cutoff, x.shape)
    y = np.zeros_like(x)
    acc = 0.0
    for i, (v, c) in enumerate(zip(x, cutoff)):
        k = 1 - np.exp(-2 * np.pi * c / SR)
        acc += k * (v - acc)
        y[i] = acc
    return y


def norm(x, peak_db):
    x = x / (np.abs(x).max() + 1e-9)
    return x * 10 ** (peak_db / 20)


def stereo(x, width=0.0):
    return np.stack([x, np.roll(x, int(width * 40))], axis=1)


def whoosh(dur=0.45):
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    sweep = np.geomspace(300, 6000, n // 2)
    sweep = np.concatenate([sweep, sweep[::-1]])[:n]
    x = lowpass(noise, sweep) - lowpass(noise, sweep * 0.25)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return stereo(norm(x * e, -8), 1)


def swipe(dur=0.22):
    n = int(SR * dur)
    x = lowpass(rng.standard_normal(n), np.geomspace(5000, 900, n))
    return stereo(norm(x * env(n, int(0.01 * SR), n, 2.5), -10))


def pop(dur=0.12):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = np.geomspace(900, 260, n)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 40, n, 4)
    return stereo(norm(x, -9))


def click(dur=0.03):
    n = int(SR * dur)
    x = lowpass(rng.standard_normal(n), 4500) * env(n, 5, n, 6)
    return stereo(norm(x, -12))


def tick(dur=0.05):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 2400 * t) * env(n, 10, n, 8)
    return stereo(norm(x, -16))


def typing(dur=1.2, rate=14):
    n = int(SR * dur)
    out = np.zeros(n)
    t = 0.0
    while t < dur - 0.05:
        k = click()[:, 0] * rng.uniform(0.5, 1.0)
        i = int(t * SR)
        out[i:i + len(k)] += k[: n - i]
        t += rng.uniform(0.6, 1.4) / rate
    return stereo(norm(out, -14))


def riser(dur=1.2):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = np.geomspace(180, 1400, n)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    noise = lowpass(rng.standard_normal(n), np.geomspace(500, 9000, n)) * 0.6
    e = np.linspace(0, 1, n) ** 2.2
    e[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    return stereo(norm((tone + noise) * e, -10), 1)


def ding(dur=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * 1318.5 * h * t) * np.exp(-t * (3 + 2 * h)) for h, a in [(1, 1), (2.01, 0.4), (3.02, 0.2), (4.2, 0.1)])
    return stereo(norm(x * env(n, 30, n, 1), -12))


def impact(dur=0.7):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = np.geomspace(110, 38, n)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    hit = lowpass(rng.standard_normal(n), 2500) * np.exp(-t * 30) * 0.5
    return stereo(norm(body + hit, -7))


KIT = dict(whoosh=whoosh, swipe=swipe, pop=pop, click=click, tick=tick, type=typing, riser=riser, ding=ding, impact=impact)


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in KIT.items():
        x = fn()
        assert np.isfinite(x).all() and np.abs(x).max() <= 1.0, name
        sf.write(out / f"{name}.wav", x.astype(np.float32), SR)
        print(f"{name:7} {len(x) / SR:.2f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "engine/public/sfx")
