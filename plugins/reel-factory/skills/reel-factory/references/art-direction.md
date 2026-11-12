# Art direction, audio direction, and visual sourcing

## Themes (engine `meta.theme`)

Each theme is one neutral, one accent, and a two-face pairing (sans + italic-serif emphasis), the system the top creators use. Override only the accent (`meta.accent`) for brand colour. Never mix themes inside a reel.

| Theme | Look | Faces | Best for |
|---|---|---|---|
| `paper` | warm off-white `#F3EFE6`, ink, coral accent | Geist + Instrument Serif italic | explainers, design/creative, stories, frameworks |
| `night` | near-black `#0E0E10`, warm white, amber accent | Inter Tight + Fraunces italic | launches, investigations, AI news with weight |
| `swiss` | off-white, black heavy grotesk, blue accent | Archivo Black/Archivo + Source Serif italic | listicles, resource roundups, rankings |
| `signal` | warm grey, deep red, condensed caps | Barlow Condensed + Source Serif italic | breaking news, big-tech, policy, "drops" |
| `terminal` | green-black, mint accent | Inter Tight + JetBrains Mono | dev tools, CLIs, security, agents |
| `noir` | warm near-black `#0D0C0B`, cream ink, orange `#FF5A1F`, condensed caps | Barlow Condensed + Instrument Serif italic | cinematic mode, AI video/3D tools, launch hype |
| `frost` | cool grey `#EEF1F5`, near-black ink, cobalt accent | Inter Tight + Newsreader italic | tutorials, catalogs, explainers that should not read as "AI-made" warm cream |
| `ink` | blue-black `#0B0F14`, cool white, sky accent, condensed caps | Barlow Condensed + Newsreader italic | security, launches, cinematic and receipts reels |

Each creation mode has preferred themes (`modes/modes.json` → `defaults.themes`); the mode playbook wins over the topic-mood table when they disagree.

**Palette fatigue:** warm cream + orange/coral (`paper`, `noir`, coral accents) is the look audiences now associate with AI-generated content. Prefer `frost`, `ink`, `swiss`, `terminal` or a brand accent unless the topic calls for warmth.

**Accent discipline:** one accent per reel. Use it for the emphasis word, the active item, and the CTA keyword. Everything else is ink or muted. Avoid purple-blue "AI gradients", neon glows, glassmorphism, and gradient text; the corpus' own anti-slop reels mock them, and they read as cheap.

## Caption styles (`meta.captionStyle`)

| Style | Look | Pairs with |
|---|---|---|
| `pill` | dark rounded box, white bold, accent keyword | any theme; safest on busy visuals |
| `highlight` | ink text, keyword in accent box | light themes (`paper`, `swiss`, `signal`) |
| `serif` | sans words, keyword swapped to italic serif accent | `paper`, `night` (editorial creators) |
| `caps` | 1–2 huge uppercase words at a time | high-energy dev or security reels |
| `none` | no subtitles (kinetic titles carry the text) | music-only reels, or when every scene is kinetic text |

## Layout

- `faceless` (default): designed scenes fill the frame. Top-tier faceless creators prove this works.
- `split-avatar`: the presenter clip sits in the bottom 46% with scenes on top (the corpus' most common layout). The clip is either the user's own footage (`rf voice P --footage clip.mp4`, free) or an AI avatar (`config.avatar.enabled`; ElevenLabs Flows `creatify-aurora`: image + VO → talking head; credit-heavy).

**Persistent overlays** (mode devices, `storyboard-schema.md`): `meta.banner` (newsroom BREAKING lower-third), `meta.slate` (cinematic film-slate HUD), `meta.progress` (bar or ToC chips for story ladders, steps and checklists), `meta.hookTitle` (sticker; in quicktake it stays the whole reel).

Safe zones (the engine enforces them): key content sits 200–1290 px vertically, captions around 1400 px, and nothing important goes in the bottom 380 px (Instagram UI) or right 120 px (action rail).

## Visual sourcing priority (cheapest and most truthful first)

1. **Rebuilt UI from real strings**: the repo card from the GitHub API, a terminal with the real install command, a chat with a real prompt, a `quote` of the real README or tweet sentence. Free, legible, accurate.
2. **og:images** of the official page or repo (`rf sources og|repo`). Free.
3. **Diagrams**: `flow`, `hub`, `bars`, `versus`, `grid` drawn by the engine. Free.
4. **Generated images** (ElevenLabs Flows `gpt-image-2`/`gemini`/`seedream`): metaphors, illustrated characters, atmospheric hook frames. Budget is about 4 per reel. Prompt style: name the theme palette, "flat editorial illustration" or "clean 3D render", **no text, no real people, no real logos**. Keep one consistent style per reel.
5. **Generated video b-roll** (Seedance/Veo, off by default): one 4–6 s cinematic hook or establishing shot, only when motion matters.
6. **Browser capture** (agent-browser screenshots or recordings of public pages): **off by default**. Browser automation can touch live sites, so it is opt-in. Use it only when `config.browser_capture` is `true`, only for public unauthenticated pages, and with no form input.

## Locked illustration styles (one per reel, reused in every prompt)

- **Story characters** (story mode): "flat vector illustration, warm off-white #F3EFE6 background, thick even dark outlines, muted palette with a single orange accent, simple rounded shapes, no text, no logos" + the same character line in every prompt ("a small rounded robot named Nova with a blue cap").
- **Concept icon cards** (catalog/checklists, the batch-02 legal-checklist pattern): "isometric 3D icon of <concept object>, soft studio light, white background, single <accent> accent, clean glossy materials, centered, no text".
- **Metaphor hero frames** (kinetic/cinematic): "<the analogy drawn literally: an elephant planning next to a goldfish reviewing>, clean studio 3D render, <theme bg> background".
Reject and regenerate (once) any image that breaks the style; never mix styles in one reel.

## Annotation grammar (walkthrough, receipts, quicktake)

Point at exactly what the VO names: big yellow `arrow` actions (from top, bobbing) for single UI elements, `box` for regions, `zoom` (1.5–2×) when text is small, `highlight` sweeps on source sentences. One annotation per sentence; remove the previous one (`until`) before the next lands.

## Image prompt template

`"<subject doing the concept>, <composition: centered subject, generous negative space top and bottom>, <style: flat editorial illustration | clean studio 3D render | isometric diagram>, palette <theme bg> background with <accent> accents, soft even lighting, high detail"` + aspect `4:5` for in-window images, `9:16` for `frame: "full"`.

## Audio direction

- **Voice:** ElevenLabs voice from config (default "Liam – energetic social media creator"), speed about 1.05–1.12, `eleven_v3`. The free fallback is edge-tts "Andrew Multilingual". The tone is a confident friend explaining, not a narrator. Write emphasis into the words, not into stage directions.
- **Music prompt** by mood (always instrumental):
  - dev, security, tension: "dark minimal techno pulse, 110–118 bpm, sub bass, clean hi-hats"
  - launches, optimism: "bright modern electronic, 105–115 bpm, plucky synths, light claps"
  - design, creative: "lo-fi house, warm keys, soft vinyl texture, 95–100 bpm"
  - news, investigation: "tense cinematic pulse, low strings ostinato, ticking percussion"
  - story explainers: "playful minimal pizzicato and marimba, light percussion, 100 bpm"
- **SFX:** automatic from scene entrances (see storyboard-schema.md). Add a `riser` into the re-hook (`rehook: true`), a `tick` on counters if a stat lands mid-sentence, and an `impact` on stamps. Keep it subtle: the voice always wins.
