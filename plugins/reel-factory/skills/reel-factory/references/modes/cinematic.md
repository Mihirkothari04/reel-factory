# Mode: Cinematic Hype (`cinematic`)

**Identity:** spectacle first. Generated hero shots, a film-slate HUD, huge condensed caps, cuts every 1–2 s on a loud bed. For when the output *is* the hook: AI video/image/3D tools, sci-fi-framed tech, launch hype. (Creator 18; Creator 22' Wan2GP cold open; MotionSites' card swarm; Creator 59' MiroFish Matrix city.)

## Construction
- **Theme:** `noir` (warm near-black, cream ink, orange accent, Barlow Condensed uppercase); captions `caps` (1–2 huge words).
- **Slate HUD:** `meta.slate = {"title": "WAN2GP · REEL / 2026"}` draws corner brackets, a running timecode and `SCENE 03/12`.
- **Visuals:** `video` scenes from `assets` (kind video, 4–6 s; needs `video_gen.enabled`; state the credit cost before generating), otherwise `image` with `frame: "full"` + `kenburns` from 2–4 generated stills; plus `stat` count-ups, `punch` stamps, `title` with a `[box]` keyword.
- **Prompts:** cinematic language (lens, light, motion): "slow dolly through a dark server hall, volumetric haze, orange rim light, 35 mm, shallow depth of field". No real people, logos or text in generated media.
- **Audio:** loud bed (musicVolume 0.42, duckTo 0.17; prompt "cinematic hybrid trailer pulse, 128 bpm, sub hits, risers, no vocals"), a riser into the re-hook, impacts on stamps. VO stays fast (210–235 wpm).
- **Pacing:** 0.9–2.6 s per scene (QA enforces).

## Beat template (spotlight, 30–45 s)
Cold open on the most spectacular shot (0–1.5 s, no setup) + the hook line → what it is (slate + name) → 3 rapid capability shots → "but here's what makes this insane" → the accessibility or price kicker → CTA.

## Pitfalls
- B-roll that illustrates nothing. Every generated shot must depict a claim.
- Sober topics (breaches, money loss) read as hype here: use newsroom or receipts.
