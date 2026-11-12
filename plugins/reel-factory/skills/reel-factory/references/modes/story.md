# Mode: Illustrated Story (`story`)

**Identity:** teach N connected concepts by letting a fictional protagonist fail N times. Each failure motivates one fix; the stakes escalate; the ending calls back to the first failure. The best storytelling in the corpus (Creator 25, "The 8 Layers of AI Engineering", 128 s, saved and shared for its narrative).

## Construction
- **Protagonist:** a named product, bot or startup ("Nova"), **never** a real person. Give it a goal in sentence one.
- **Illustrations:** one locked style prefix for the whole reel, e.g. "flat vector illustration, warm off-white #F3EFE6 background, thick even outlines, muted palette with one orange accent, no text, no logos", plus the same character description in every prompt. Generate 6–10 with `RF image` (raise `images.max_per_reel` for this reel only, and say so). No budget → diagram "illustrations" (`flow`, `versus`, `list`, `hub`) with the same ladder.
- **Chapters:** a `label` on every scene: `// 03 — rag` (mono, top-left).
- **Progress stack:** `meta.progress = {"items": ["Model", "Prompt", "RAG", …], "scenes": ["s4", "s7", …]}`: one segment fills as each fix lands. End with a `list` (`check: true`) showing the whole stack ✓.
- **Captions:** `serif`; key nouns in `emphasis`.
- **Audio:** calm, clear VO at 180–200 wpm; quiet bed (musicVolume 0.18, duckTo 0.06, about −35 dB); a stamp SFX on each failure (`punch` style stamp: "AGAIN", "FAIL").

## Beat template (problem-ladder, 60–120 s)
| beat | content |
|---|---|
| setup (0–5 s) | "Meet Nova. Nova has one job: …" |
| failure 1 → fix 1 | a visible consequence (red stamp), then the concept as the fix (illustration + one-line plain definition) |
| repeat 4–8× | each failure bigger (one customer → 2,000 users → a $3,940/day bill) |
| all fixed | the full stack ✓ |
| twist | someone skips one layer "on a Friday" → failure 1 returns (callback) |
| end | punchline; soft CTA or none |

## Pitfalls
- A concept without a felt failure becomes a lecture. If you can't name the failure, cut the concept.
- Style drift between illustrations: reuse the exact prefix; regenerate an off-style image once at most.
- Under 45 s there is no room for a ladder: use `kinetic` with the framework skeleton.
