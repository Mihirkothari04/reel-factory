# Studio engine: how a reel is constructed (v3, default)

The reference reels are layered, not sequenced. A presenter performs continuously. The edit changes how much of the frame he gets, while footage, screenshots, cut-outs and motion graphics change every 0.5–1.5 s on top of or around him. Batch-03 measured 48–129 big picture changes per minute and 0–6 % static seconds. Our 2.0 output measured 10 changes per minute and 9.4 % static. `storyboard.meta.engine: "studio"` builds reels this way. The legacy scene engine stays only for pure motion-graphics formats that never use a presenter.

## 1. The cast: one presenter, always the same man

- `~/.reel-factory/avatars/host/` is the show's single presenter: an original synthetic man, not based on any real person. It holds:
  - the HeyGen look (`heygen_avatar_id`);
  - the identity description;
  - the default motion;
  - the set plate `set.jpg`;
  - the voice (`voice_id` = config voice).

  Never swap him per reel; consistency is the brand.
- He is rendered by HeyGen Avatar IV (`presenter.engine`) from **our** ElevenLabs take, only for the spans where a layout shows him. The output is a transparent WebM, so he can sit on his set, in a split band or as a corner cut-out.
- Cost: **$0.0425/s** of presenter on screen (measured 2026-11-14). The cap is `presenter.max_usd_per_reel` (default $2 ≈ 47 s). `RF presenter P --dry-run` prints windows and cost before paying. Re-runs reuse identical renders and never pay twice.
- Performance direction: each beat's `motion` (≤ 1–2 sentences) tells him how to deliver that line. Examples:
  - "leans in, lowers voice, sceptical half-smile";
  - "counts three points on his fingers";
  - "points up at the graphic above him";
  - "shrugs, open palms".

  Match the emotion of the line, vary it beat to beat, and never make it theatrical.
- Disclose in the caption ("AI-generated presenter"). Meta also asks for the "AI info" label on photoreal AI video.

## 2. Layouts (presenter framings)

| layout | frame | use it for |
|---|---|---|
| `full` | presenter waist-up on his set, full frame | hook line, opinion, re-hook, verdict, CTA (the human moments) |
| `close` | punch-in on his face (1.34×) | the single most important sentence, a reaction, a twist |
| `split` | content top 1000 px, presenter band below | explaining while showing proof: the workhorse layout |
| `card` | presenter full, a white card with the content floats over his chest | a headline/post he is "holding up" |
| `corner` / `corner-left` | presenter cut-out in the bottom corner over full-screen content | fast montages and walkthroughs where he reacts or points |
| `off` | full-screen content, voice continues | footage, documents, dense graphics |

Rules:
- Change layout every 2–6 s.
- Never use the same layout for more than 3 beats in a row.
- The hook opens with a presenter layout (`split` or `full`) unless the format is faceless.
- `close` at most twice per reel.
- Presenter on screen 30–60 % of the reel. Count it against the cost cap; `off` is free.

## 3. Shots (content track)

`shots[]` per beat, each starting `at` a phrase of that beat's narration. Shots run until the next shot (also across beats), so the content box is never empty. Every beat needs at least one shot, except `full`/`close`-only beats. **Aim for a new shot every 1–2.5 s of narration.**

| kind | fields | notes |
|---|---|---|
| `image` | `src` or `shot` (rf shot JSON), `highlight: ["exact phrase"]`, `markStyle` (marker/box/underline/strike), `fit` (width/cover/contain/blurfill), `cam`, `label` | documents and posts fill the box **width**. By default the camera opens on the masthead and pans/zooms to each highlight as it is spoken, and the marker sweeps word by word. `strike` crosses out text as a rhetorical device. |
| `video` | `src` (from `RF footage get`), `trim`, `fit` (cover for vertical, `blurfill` for 16:9), `label` | real footage of the person/product/event being named. Always label news/YouTube excerpts (`"label": "Source: CNBC"`). |
| `scene` | `type` + `props` of any legacy scene component (stat, list, flow, versus, grid, walkthrough, terminal, chat, repo, carousel, sheet, punch, title …) | rendered inside the content box, scaled to it |
| `color` | `bg` | a hard colour beat behind a gfx slam |

`enter`: `cut` (default; most changes should be hard cuts on a word), `whip`, `zoom`, `blur`, `slide`, `flash`. Use `whip`/`zoom` for section changes, `flash` for impacts. Transition SFX are added automatically.

## 4. Graphics (gfx track, over everything)

| kind | fields | use |
|---|---|---|
| `sticker` | `src` (from `RF cutout`), `x`, `y`, `w`, `rot`, `text` (name chip) | people, products, logos cut out as stickers |
| `label` | `text`, `x`, `y` | mono micro-labels: "sec filing · form 8-k", "source: WIRED", "day 1 → 2 weeks" |
| `slam` | `text`, `sub`, `y`, `h` (font px), `color` | 1–3 display words that land on a stressed word ("CHINESE SPY", "FREE") |
| `counter` | `value`, `fromValue`, `prefix`, `suffix`, `decimals`, `text` | numbers that count up as they are said |
| `scene` | `type`, `props`, `x`, `y`, `w`, `h` | a boxed legacy component floating over footage |

`at` = start phrase, `dur` (default 1.8 s) or `until` (phrase). Keep `y` clear of the caption line for that layout (split ≈ 925, full ≈ 1430, corner ≈ 1150, off ≈ 1480).

## 5. Looks (format bibles)

`meta.look` picks one complete identity: palette, caption style, marker colour, grain and vignette. Pick one per reel and keep it.
- `studio`: cool light content, single-word italic-serif captions, presenter on his teal set. The default for news and explainers with the presenter.
- `intel`: dark layered motion graphics, bold captions with a lime keyword, mono labels, heavy grain. For investigations, scandals and timelines; works faceless or with a corner presenter.
- `cutout`: bold colour fields that change per shot, corner presenter with gestures, bold captions. For tool launches, tutorials and lists.

## 6. Footage and media sourcing (owner policy 2026-11-14)

The order to try:
1. Official/press media: company keynote and launch videos, press-kit photos, the person's own posts.
2. Real product screen recordings and screenshots: `RF shot`, or agent-browser `record` on public pages.
3. Free-licence stock: `RF footage find --source commons|nasa|archive`.
4. **News/YouTube excerpts of real people and events**: `RF footage find --source youtube` then `RF footage get <url> --start S --dur 3-6`. Short excerpts only (≤ 6 s each), always with a source label, never altered to change meaning.

Every visual must show **what the narration says at that moment**: the named person, the named product, the quoted line. "Related" stock is the last resort.

## 7. Edit gates (blocking in `RF qa`)

- ≥ 40 big picture changes/min;
- ≤ 3 % static seconds;
- presenter share 20–75 % (warning);
- the WER, loudness and voice gates as before.

If the edit fails: add shots (split long beats into 2–3 visual events), add camera moves to images, swap a static `full` beat for `split` with proof.

## 8. Beat recipe (typical 45–60 s reel)

| time | layout | content |
|---|---|---|
| 0–3 s | `split` or `full` | strongest visual of the claim on top (the post/footage); **the hook line from him** |
| 3–15 s | `off`/`split` alternating | the proof: highlighted document, footage of the person, cut-out stickers, counters |
| re-hook (40–60 %) | `close` or `full` | "But here's what nobody's talking about…" |
| 15–40 s | `split`/`corner`/`card` | the mechanism or story with a shot every 1–2 s |
| last 6–8 s | `full` | verdict plus CTA, a comment-keyword gfx |
