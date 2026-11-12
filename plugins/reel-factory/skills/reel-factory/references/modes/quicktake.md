# Mode: Quick Take, the source frame (`quicktake`)

**Identity:** same-day reaction. A persistent headline sticker over the source itself (the official launch video, the README, the post), zoomed to what matters, plus one sharp insight and a verdict, in 20–35 s. The fastest mode to produce. (Recordly: cut-out presenter over a README that zooms to each section as it's read; Creator 39/Creator 42 source frames; Creator 53's blog pick.)

## Construction
- **Hook sticker for the whole reel:** `meta.hookTitle = {"text": "This repo makes ANY screen recording look *edited*", "untilScene": "<last scene id>"}`.
- **Source on stage:** `walkthrough` with `src` = the README/page screenshot (`RF sources repo`, `RF sources og`) and `zoom`/`arrow` actions keyed to `say` words, so the camera moves to each section as it is mentioned; the official video as `video` (`fit: "contain"`) credited in the caption; `quote` for the post.
- **The insight:** one thing the press release doesn't say (who it's really for, the catch), or a price comparison shown as a real receipt (the competitor's pricing page screenshot, never a made-up number).
- **Voice:** brisk, 210–230 wpm. When speed matters most it can be silent (music + sticker): set `mode: "silent"` and keep the sticker.
- **CTA:** a keyword ("comment REPO").

## Beat template (20–35 s)
Hook (sticker + the source's hero) → what it is (zoom to the description) → 2 capabilities (zoom to features) → the insight or price receipt → verdict → CTA.

## This mode vs. the floor
The automated README-scroll channels (Creator 44, Creator 28, Semantica, Next AI Draw.io) are this mode done badly: blind scrolling, tiny text, README-speak, no music. Every zoom must land on a phrase the VO is saying, and the VO speaks plain language, not README copy.

## Pitfalls
- Reposting someone else's full video. Use official press/launch media only, credit it, and add the insight. Never repost a creator's reel.
