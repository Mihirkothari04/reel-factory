# storyboard.json: the single source of truth

The Creative Director writes `<prod>/storyboard.json`. Every tool reads it: `voice` speaks `scenes[].vo`, `image` generates `scenes[].assets`, `build` times scenes from the voice-over and produces `props.json`, and `render` draws it with the Remotion engine.

```jsonc
{
  "meta": {
    "title": "Strix: free AI pentester",          // working title (also the output name)
    "mode": "kinetic",                             // creation mode id (modes/INDEX.md): kinetic | presenter | story | newsroom | receipts | catalog | walkthrough | cinematic | silent | quicktake
    "theme": "night",                              // paper | night | swiss | signal | terminal | noir | frost | ink   (art-direction.md)
    "accent": "#F2A93B",                           // optional: override the theme accent (one accent only)
    "captionStyle": "pill",                        // pill | highlight | serif | caps | none
    "layout": "faceless",                          // faceless | split-avatar (needs avatar clip)
    "handle": "@yourhandle",                       // optional: top-right handle after the hook
    "hookTitle": { "text": "This free tool *hacks* your app", "untilScene": "s3" },  // optional sticker for scenes s1..s3
    "banner": { "kicker": "BREAKING", "text": "Cloudflare ships a *browser* for AI agents" },  // optional, newsroom: persistent lower-third
    "slate": { "title": "WAN2GP · REEL / 2026" },  // optional, cinematic: film-slate HUD (corner brackets, timecode, scene n/N)
    "progress": { "items": ["Model", "Prompt", "RAG"], "scenes": ["s3", "s6", "s9"], "style": "bar" }  // optional tracker; bar | chips (ToC)
  },
  "skeleton": "spotlight",                         // formats.md id: spotlight | listicle | tutorial | news | claim-test | problem-ladder | framework | tier-list | comparison | action-reaction | stack-roadmap
  "language": "en",
  "voice": { "voice_id": null, "speed": 1.08 },    // optional per-reel overrides of config.voice
  "music": { "prompt": "dark minimal techno pulse, 112 bpm, tense but clean", "mood": "tense tech", "query": "dark electronic" },  // or {"none": true}
  "musicVolume": 0.30, "duckTo": 0.11,             // optional mix overrides (0..1)
  "emphasis": ["free", "hacker", "45,000"],         // caption words shown in the accent colour (≈1 per 2 seconds)
  "scenes": [
    {
      "id": "s1",
      "vo": "Someone just open-sourced an AI that hacks your app before a real hacker does.",
      "type": "title",
      "enter": "cut",                              // push (default) | slide | pop | blur | cut
      "label": null,                               // optional HUD chapter label, e.g. "02 / 05"
      "rehook": false,                             // true = riser SFX leads into this scene
      "sfx": null,                                 // null = automatic; [] = silence; [{"t":0.2,"name":"tick","vol":0.4}]
      "props": { "lines": ["Someone just built", "an AI [hacker]"] },
      "assets": []                                 // [{"kind":"image","prompt":"…","out":"img/s1.png","aspect":"4:5"}]
    }
  ],
  "caption": "Instagram caption (hook line + 2–4 value lines + CTA)",
  "hashtags": ["ai", "opensource", "cybersecurity"],
  "sources_in_caption": ["github.com/usestrix/strix"],
  "cover_at": 1.2                                  // seconds: frame used for cover.jpg
}
```

## Hard rules

- **Silent mode exception:** with `meta.mode: "silent"` scenes have **no `vo`**; each has `"dur": <seconds>` (0.8–3) and boundaries snap to the music's beats. Run `rf music` before `rf build`.

- **Every scene must have `vo`.** Scene duration equals its spoken length. Aim for 4–12 words (≈1.3–3.5 s) per scene. Longest allowed is about 6 s, and splitting is better.
- Scene 1's `vo` **is the hook**: payoff in the first sentence, no greeting, no "in this video".
- Write `vo` the way it should be *spoken*: numbers as people say them ("forty-five thousand" or "45,000", either works), no markdown, no emoji, and no URLs (put those on screen).
- On-screen text **complements** the voice-over and must not transcribe it. Use 2–7 words of headline per scene. Captions already carry the full speech.
- Asset paths are relative to `<prod>/public/` (for example `img/s3.png`). Remote `https://` URLs also work.
- Use one `theme` per reel. Change `enter` types to vary rhythm, but don't change themes mid-reel.

## Rich-text markup (any text prop)

`*phrase*` renders the italic serif in the accent colour (the signature emphasis). `[phrase]` renders a Figma-style selection box (accent fill with corner handles). `_phrase_` renders muted. Use at most **one** emphasis per line.

## Scene types and props

| type | use it for | props |
|---|---|---|
| `title` | hook headline, section headers, kinetic statements | `lines: string[]` (1–3 lines, ≤4 words each ideal), `kicker?` (mono line above), `sub?`, `size?` (default 104), `align?: "center"\|"left"` |
| `punch` | pattern interrupt, 1–3 big words; stamps ("HUGE", "VULNERABLE") | `text`, `style?: "big"\|"stamp"`, `sub?`, `size?` (default 150) |
| `stat` | one big number with count-up | `value: number`, `from?`, `prefix?`, `suffix?` (e.g. "%", "★", "x"), `decimals?`, `label`, `sub?`, `source?` |
| `list` | progressive checklist / numbered list (screenshot-worthy) | `title?`, `items: string[]` (≤6 ideal), `check?: bool`, `revealAt?: number[]` (sec from scene start) |
| `quote` | tweet / blog / README line with highlighter sweep | `text`, `highlight: string[]` (exact substrings), `author?`, `handle?`, `source?`, `size?` |
| `repo` | GitHub repo card with star odometer | `owner`, `name`, `description`, `stars: number`, `language?`, `license?`, `topics?: string[]`, `highlight?`, `image?` (og image path) |
| `terminal` | install commands, agent runs, logs | `title?`, `lines: [{t:"cmd"\|"out"\|"ok"\|"err"\|"dim", text}]`, `caption?` |
| `code` | a source or config file with highlighted line(s); secrets redacted | `file` (tab title), `lines: string[]` (≤14), `highlight?: number[]` (1-based), `redact?: string[]` (substrings to mask as ••••), `caption?` |
| `chat` | prompt → AI answer demos | `app?`, `messages: [{role:"user"\|"ai", text}]` |
| `image` | screenshot / generated image (Ken Burns), with optional highlight box | `src`, `frame?: "window"\|"none"\|"full"`, `url?` (title-bar text), `kenburns?: "in"\|"out"\|"up"`, `box?: {x,y,w,h}` (0..1), `caption?`, `maxH?`, `fallback?` (title text if asset missing) |
| `video` | generated b-roll / screen recording, full bleed | `src`, `fit?: "cover"\|"contain"`, `trim?` (s), `caption?` |
| `item` | one entry of a listicle with i/N counter | `index`, `total`, `name`, `desc`, `stars?`, `tag?`, `url?`, `image?` |
| `bars` | before/after, A vs B, benchmark | `title?`, `bars: [{label, value, highlight?}]`, `unit?`, `decimals?`, `note?` (source) |
| `flow` | pipeline / steps / how it works | `title?`, `nodes: string[]` (3–6) |
| `hub` | one thing connects to many | `center`, `spokes: string[]` (3–7) |
| `versus` | old way vs new way, myth vs reality | `left: {title, points[]}`, `right: {title, points[]}`, `leftTag?` (default OLD), `rightTag?` (default NEW) |
| `grid` | "works with…", N tools at a glance | `title?`, `items: [{label}]`, `highlight?: number[]`, `cols?` |
| `cta` | closing call to action (shows the action) | `kind: "comment"\|"follow"\|"save"`, `keyword?`, `line?`, `headline?`, `sent?` |
| `walkthrough` | one app window; cursor types, clicks, arrows and zooms through steps (walkthrough, quicktake zoom-to-source, receipts zoom-to-line) | `url?`, `src?` (screenshot in public/) or `rows?: string[]` (rebuilt app text), `aspect?` (w/h, default 0.75), `actions: [{type:"move"\|"click"\|"type"\|"zoom"\|"box"\|"arrow", x, y, w?, h?, text? (type), scale? (zoom), from? (arrow: top\|left\|right\|bottom), until?, say? (VO word that triggers it) \| at? (s)}]`, `caption?` |
| `headline` | article/blog/press card with outlet, date and highlighter synced to VO | `outlet`, `date?`, `headline`, `highlight?: string[]`, `dek?`, `image?`, `author?`, `size?` |
| `carousel` | many items flying past, focused card sharp, i/N counter | `items: [{name, desc?, tag?, meta?}]` (3–6 per scene), `total?`, `offset?` (index of the first item in the full list), `revealAt?` (auto from VO) |
| `sheet` | dense cheat-sheet end frame (screenshot bait) | `title`, `items: string[] \| [{name, tag?}]`, `cols?` (auto 2 past 8), `note?` (e.g. "checked 12 Nov 2026"), `stamp?` (e.g. "Screenshot this") |

**Speech-synced props** (filled by `rf build` from the VO, unless set): `list.revealAt`, `flow.revealAt`, `carousel.revealAt`, `quote.highlightAt`, `headline.highlightAt`, walkthrough `actions[].at` (from `say`). **Title extras:** `typewriter: true` types the lines letter by letter with an underscore cursor.

## Scene-type cadence

- Never put the same `type` in more than **2 consecutive** scenes. Alternate dense scenes (repo, terminal, list) with light ones (title, punch, stat).
- Put a `punch` or `stat` roughly every 8–12 s as a pattern interrupt.
- Mark the re-hook scene at 40–60% of the runtime (`rehook: true`).
- End on `cta`, or on a verdict `title` for news and story formats.

## Assets (`scenes[].assets`)

```json
{"kind": "image", "prompt": "isometric illustration of a small robot inspecting a glowing server rack, warm paper palette, flat shading", "out": "img/s4.png", "aspect": "4:5"}
{"kind": "video", "prompt": "slow dolly through a dark server room, rim light, shallow depth of field", "out": "vid/s2.mp4", "seconds": 5}
```

Reference the same path in the scene props (`"src": "img/s4.png"`). The image budget is in config (`images.max_per_reel`, default 4). Video generation is off unless `video_gen.enabled`. If an asset fails, `build` turns the scene into a `title` using `props.fallback` or `props.caption`, so always set one.
