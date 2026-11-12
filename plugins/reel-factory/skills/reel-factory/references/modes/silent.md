# Mode: Silent Showcase (`silent`)

**Identity:** no voice. A stunning result in the first second, three to six short text beats cut on the music's beat, 12–25 s so it loops. Only works when the visual payoff is spectacular. (Creator 15' "model + 1 prompt = this site"; Creator 40's flashcard websites; Creator 42's silent demo.)

## Construction
- **No VO:** with `meta.mode: "silent"`, `rf voice` writes empty words and `rf build` times scenes from each scene's `dur` (seconds), snapping boundaries to the beat grid of `music.mp3` (saved as `public/beats.json`). Scenes have **no `vo`**; give `dur` instead (0.8–3 s; the hook and result scenes longest).
- **Order of tools:** `RF music P` **before** `RF build P` (the beat grid needs the music). Prompt a clear pulse: "punchy minimal electronic, 120 bpm, clear kick on every beat, no vocals". Loud mix (musicVolume 0.85).
- **Text carries everything:** `title` lines ≤ 5 words, one idea per beat ("Sonnet + 1 prompt", "= this site", "Prompt from scrolltide.co", "Paste in Claude", "Site ready ✅"). Put `typewriter: true` on the formula line.
- **Visuals:** the result first: full-frame `image`/`video` or in a window (generated, captured with permission, or official media); `carousel`/`item` flashcards for lists; a `cta` card with the keyword at the end (hold 2.5 s).
- **Captions:** none.
- **Loop:** the last frame should cut cleanly back to the first (end on the result or the keyword card).

## Storyboard sketch
```json
{"meta": {"mode": "silent", "theme": "night", "title": "…"}, "music": {"prompt": "…120 bpm…"},
 "scenes": [{"id": "s1", "dur": 2.0, "type": "image", "props": {"src": "img/result.png", "frame": "full"}},
            {"id": "s2", "dur": 1.5, "type": "title", "props": {"lines": ["Sonnet + 1 prompt"], "typewriter": true}}]}
```

## Pitfalls
- Anything that needs explanation. If a beat needs a "because", pick another mode.
- A weak visual: if the result isn't striking at phone size, this mode fails.
