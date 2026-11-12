# reel-factory

Autonomous Instagram Reel production for Claude Code. Give it a topic, or nothing, and it researches, picks a creation mode, writes, designs, voices, scores, renders, and QA-checks a publish-ready 1080×1920 reel. Its creative rules come from a frame-by-frame study of 105 AI and tech reels, and it keeps learning from every new batch you give it.

```
/reel                       → trend discovery: picks today's best AI/tech topic from live data, then produces it
/reel <topic or URL>        → produces a reel about your topic
/reel <topic> --mode ai     → skip the mode question; the Creative Director decides (AI Select)
/reel-trends [niche]        → just show the top trending topics with evidence
/reel-learn <folder>        → analyse new reference reels, dedup, and evolve modes/techniques/engine
/reel-setup [set key value] → install/repair runtime, view/change preferences
```

Output goes to `./reel-productions/<date>-<slug>/out/` in the folder you run it from: `reel.mp4`, `cover.jpg`, and `caption.txt`, plus the research, brief, script, and storyboard behind them.

## Creation modes

After research, `/reel` shows all ten modes with a one-line description of what *your* topic would look like in each, marks the recommended one, and asks once (or choose **AI Select**). Modes differ in construction, not colour: stage, presenter, visual source, voice, pacing, audio, and tools.

| Mode | Built as |
|---|---|
| Kinetic Explainer | faceless motion graphics, one composition per sentence |
| Presenter + Board | your own recorded clip (or an AI avatar) under a motion-graphics board |
| Illustrated Story | a fictional character fails and learns, chapter by chapter, with a growing progress stack |
| Newsroom Brief | BREAKING banner, real headlines highlighted as read, escalation and catch |
| Receipts | primary sources highlighted line by line → honest verdict |
| Rapid Catalog | preview grid, i/N carousel, cheat-sheet end frame |
| Screen Walkthrough | one app window: cursor types, clicks, arrows and zooms through the steps |
| Cinematic Hype | generated hero shots, film-slate HUD, 1–2 s cuts |
| Silent Showcase | no voice, text beats cut on the music's beat, loops |
| Quick Take | headline sticker over the source itself, same-day, 20–35 s |

Details: `skills/reel-factory/references/modes/`.

## Pipeline (multi-agent)

| Stage | Who | What |
|---|---|---|
| Topic discovery | `trend-scout` agent + `rf trends` | GitHub (new and trending), Hacker News, Hugging Face, Lobsters, and web search; convergence scoring |
| Research | 2× `topic-researcher` in parallel | A: primary sources and mechanism. B: reception, competitors, fresh angles |
| Mode selection | Creative Director (+ you, once) | fit scoring on six axes, topic-specific options, AI Select |
| Strategy, script, storyboard | Creative Director (main session) | skeleton (11), 5 scored hooks, re-hook, honesty beat, CTA, mode devices, visual plan |
| Review | `script-critic` + `fact-checker` in parallel | rubric scoring incl. mode fidelity, claim verification, before any credits are spent |
| Assets | `rf sources`, `rf image` | rebuilt UI and real screenshots first; generated images within budget |
| Voice | `rf voice` | ElevenLabs with exact timing (edge-tts free fallback); `--footage` for your own clip; none in silent mode |
| Music and SFX | `rf music`, procedural SFX kit | instrumental bed, auto-ducked; beat grid for silent mode |
| Edit and render | Remotion engine | 22 scene types, 6 themes, banner/slate/progress overlays, speech-synced highlights and actions, −14 LUFS master |
| QA | `rf qa` + `qa-reviewer` | per-mode thresholds, black/frozen frames, Whisper intelligibility, visual review of stills |
| Learning | `/reel-learn` + `reel-analyst` agents | ingest with dedup → per-reel analysis → new mode / skeleton / technique → implement → version |

## Install

```bash
claude plugin marketplace add Mihirkothari04/reel-factory
claude plugin install reel-factory@reel-factory --scope user
```

Then run `/reel-setup` in a new Claude Code session. It probes the machine (OS, GPU, RAM, Node, ffmpeg, ElevenLabs), tells you exactly what to install if something required is missing, installs the runtime, and asks a few one-time preferences. To evolve your own version with `/reel-learn`, clone the repo and add it as a local marketplace (see the repository README).

## Requirements

Windows, macOS, or Linux with Python 3.10+, Node 20+, and ffmpeg on PATH. Optional: an NVIDIA GPU (faster Whisper), the `elevenlabs` CLI logged in (`elevenlabs auth login`), and `uv`. The first run of `/reel-setup` (or the first `/reel`) creates the runtime at `~/.reel-factory/` (venv, Remotion deps, SFX kit, `config.json`, `learnings.md`, the analysed-reel library, production history). Plugin updates never touch it.

## Preferences (`/reel-setup set <key> <value>`)

`brand.handle` · `brand.accent` · `voice.voice_id` / `voice.speed` · `images.max_per_reel` · `video_gen.enabled` · `avatar.enabled` + `avatar.image` · `modes.ask` (false = always AI Select) · `output_dir` · `browser_capture` (off by default; agent-browser is only used when enabled) · `source_shots_browser` (true = read-only screenshots of public pages for on-screen sources without a prompt).
