# Toolchain, commands, costs and fallbacks

All tools run through one launcher (any `python` works; it re-enters the runtime venv):

```bash
RF="python ${CLAUDE_PLUGIN_ROOT}/scripts/rf.py"
$RF probe [--json]               # system probe (no venv needed): capabilities, per-stage plan, blockers, asks → ~/.reel-factory/profile.json
$RF doctor                       # health + ElevenLabs credits
$RF setup                        # (re)install runtime at ~/.reel-factory (idempotent)
$RF config [set key value]       # preferences (voice, brand, budgets, output_dir, browser_capture, source_shots_browser)
$RF new "<title>" [--root DIR]   # → prints production dir (default <cwd>/reel-productions/<date>-<slug>)
$RF modes [--json]               # creation-mode catalog with live availability + recent production history
$RF trends --days 7 --out F      # free trend scan (GitHub, HN, HF, Lobsters)
$RF sources repo owner/name --prod P   # GitHub facts + README excerpt + og image → public/img/
$RF sources og <url> --prod P [--name x]
$RF sources hn "<query>" [--days 14]
$RF shot <img|url> --prod P --name x --find "exact phrase" [--find …] [--erase x,y,w,h] [--crop x,y,w,h | --aspect 1.0]
                                 # real-page screenshot → cleaned crop + local-OCR highlight boxes → public/img/shot-x.{png,json} (`source` scene)
$RF image P [--dry-run]          # generate scenes[].assets (budgeted)
$RF voice P [--provider edge]    # VO + exact word timing → public/vo.mp3, words.json (silent mode: writes empty words)
$RF voice P --footage clip.mp4   # presenter mode with the user's own recording: its audio = VO, aligned, never cut
$RF music P [--provider openverse|none]   # silent mode: run BEFORE build (beat grid)
$RF build P                      # storyboard + words → props.json (timing, sfx, fallbacks)
$RF render P [--draft]           # Remotion render → out/reel.mp4 (-14 LUFS), cover.jpg, caption.txt
$RF qa P                         # automated checks + out/qa/sheet.jpg (exit 1 on blocking fail)
$RF analyze <out_dir> <videos…>  # analyse reference reels
$RF ingest <folder|videos…> --batch NAME [--source-root DIR] [--dry-run]
                                 # /reel-learn step 1: fingerprint → dedup vs library + within batch (coarse dHash,
                                 # verified by fine 17x16 hash) → analyse only new reels → library/_batches/NAME.json
$RF kb where|bump [minor|patch]  # knowledge-base source location; bump version + refresh the installed plugin
```

## Capability matrix

| Stage | Primary | Fallback | Cost |
|---|---|---|---|
| Trend signals | `rf trends` (GitHub/HN/HF/Lobsters APIs) | web search only | free |
| Research | WebSearch/WebFetch, `rf sources` | Firecrawl MCP if connected (billed per call; use only for pages WebFetch can't read) | free / low |
| Script & storyboard | Claude (this session) + critic agents | n/a | n/a |
| Voice | ElevenLabs TTS with char timestamps (`eleven_v3`) | edge-tts neural voice + local Whisper alignment | ~1 char credit per char (~800–1,200 per reel) / free |
| Word timing | ElevenLabs alignment | faster-whisper (CUDA when an NVIDIA GPU is present, else CPU int8; model from `config.whisper.model`) | free |
| Music | ElevenLabs Music `music_v2` (exact length, instrumental) | Openverse CC0/CC-BY search (credit written to the caption) | credits / free |
| SFX | procedural local kit (whoosh, pop, swipe, click, tick, type, riser, ding, impact) | ElevenLabs SFX for special one-offs | free |
| Images | ElevenLabs Flows image (`gpt-image-2`, `gemini-3.1-flash-image`, `bytedance-seedream-5-lite`) | engine diagrams, og:images | credits (budget 4/reel) |
| B-roll video | ElevenLabs Flows video (`bytedance-seedance-v2-fast`, `veo-3.1-fast`) | none (off by default) | high, opt-in |
| Avatar | ElevenLabs Flows `creatify-aurora` (portrait + VO → lip-sync) | faceless layout | high, opt-in |
| Motion graphics & edit | Remotion engine (22 scene types, 6 themes, overlays: banner/slate/progress, captions, ducking, SFX) | n/a | free |
| Presenter | user's own footage (`--footage`) | AI avatar (`creatify-aurora`) → else kinetic | free / high |
| Beat sync (silent) | numpy onset/tempo on music.mp3 (`build.beat_grid`) | even timing | free |
| Mastering | ffmpeg loudnorm -14 LUFS / -1.5 dBTP, H.264 CRF18, AAC 192k | n/a | free |
| QA | `rf qa` (ffmpeg + Whisper) + qa-reviewer agent viewing the contact sheet | n/a | free |

## Budget policy

- **Free first for everything intermediate** (research, alignment, analysis, drafts, QA). Paid generation is only for assets that ship in the final reel.
- Generate the voice **once** per approved script. Edits to visuals or timing never re-run TTS. Re-run voice only if the `vo` text changed.
- Run `rf image` only after the critic and fact-check pass, so you never pay for assets of a script that will change.
- Check credits with `rf doctor` before voice and music. If credits are under about 3,000, use edge-tts and Openverse automatically (the tools already do this).

## Render notes

- The render needs the internet once per new font (Google Fonts) and takes about 1–2 min for a 50 s reel on this machine.
- `--draft` renders at half resolution for fast visual checks.
- The engine source is synced from the plugin to `~/.reel-factory/engine` on every render; node_modules persist there.
