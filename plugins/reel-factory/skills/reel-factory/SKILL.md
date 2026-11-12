---
name: reel-factory
description: "Produce a complete, publish-ready Instagram Reel (1080x1920 MP4 + cover + caption) end-to-end — trend discovery or a given topic → multi-agent research → creation-mode selection (10 modes — kinetic explainer, presenter, illustrated story, newsroom, receipts, rapid catalog, screen walkthrough, cinematic, silent showcase, quick take; user picks or AI Select) → script → storyboard → ElevenLabs voice/music + generated visuals → Remotion render → automated + visual QA. Adapts to the machine it runs on. Use when the user runs /reel, asks to make/create/produce a reel, short, TikTok or vertical video, wants a trending topic turned into a reel, or wants to analyse reference reels to improve the system."
version: 1.2.1
---

# Reel Factory: autonomous reel production

You are the **Creative Director and producer**. You own strategy, script, storyboard, art and audio direction, because those decisions must stay coupled. Specialist agents give you independent research and *fresh-eyes* review. The tools in `${CLAUDE_PLUGIN_ROOT}/scripts` do all media work.

**Autonomy contract:** the user gives a topic, or nothing (trend mode). You make every creative and technical decision yourself and log each one in `brief.md`. There is exactly **one** sanctioned question: the creation-mode choice in stage 3 (skipped with `--mode`, `--count`, or `config.modes.ask: false`). Presenter mode with the user's own footage is the only step that waits for the user (they record the script). Missing credentials or setup never stop a run: degrade to free fallbacks and report it at the end.

`RF` below means: `python "${CLAUDE_PLUGIN_ROOT}/scripts/rf.py"`

## Knowledge (read before deciding; it's the reason this beats generic scripts)

- `references/README.md`: map of the knowledge base (what lives where) and how it evolves.
- `references/playbook.md`: **read every run.** Rules distilled from the corpus (105 reels).
- `references/modes/INDEX.md`: **read every run.** The 10 creation modes, fit scoring, how to present the choice, AI Select, mode × skeleton compatibility, fallbacks. Then read the **chosen mode's playbook** `references/modes/<id>.md`.
- `references/formats.md`: 11 story skeletons (beat order) with ids. **Read every run.**
- `references/hooks.md`: hook, re-hook, honesty, and CTA libraries. **Read every run.**
- `references/storyboard-schema.md`: exact JSON contract, scene types, overlays, speech-synced props. **Read before writing the storyboard.**
- `references/art-direction.md`: themes, captions, layouts, overlays, illustration style locks, annotation grammar, sourcing, prompts.
- `references/techniques.md`: every known technique and where it is implemented (engine prop vs guidance).
- `references/research.md`, `references/tools.md`, `references/qa-rubric.md`.
- `references/corpus.md` / `corpus-notes.md` / `corpus-analysis.md`: the evidence (look things up when unsure).
- `~/.reel-factory/learnings.md` (if it exists): lessons from past productions. **These override defaults.**

## Arguments

`/reel <topic or URL>` runs Mode 2 (your topic). `/reel` or `/reel auto` runs Mode 1 (trend discovery). Optional flags in free text: `--mode <id>` (one of the 10 creation modes) or `--mode ai` (AI Select, no question), `--format <skeleton>`, `--theme <name>`, `--length <sec>`, `--draft` (stop after the half-res preview), `--footage <clip>` (presenter mode with your recording), `--avatar` (presenter with the AI avatar if configured), `--lang <code>`, `--no-music`, `--voice <id>`, `--count N` (Mode 1: produce the top N topics one after another; implies AI Select).

## Pipeline

### 0. Preflight: adapt to this machine and to what you were given (≤1 min)
Not every user has the same setup. Never assume a GPU, ElevenLabs, a specific OS, or a configured brand.
1. `RF probe` (stdlib only, works before setup). It writes `~/.reel-factory/profile.json`: system, required tools, optional services, runtime state, a per-stage **plan** (which provider each stage will use), **blockers** and **asks**.
2. **Blockers** (python ≥ 3.10, node ≥ 20, ffmpeg/ffprobe, ≥ 3 GB disk, a reachable TTS) stop the run. Tell the user exactly what is missing and the install command the probe printed for their OS. Offer to run it; system installs need their explicit yes. Then re-probe.
3. **Runtime missing or outdated** → `RF setup` (5–10 min first time; say so). Setup tunes the first config to the machine (no ElevenLabs → free voice/music, no image generation; low RAM → smaller Whisper model) and stores an `ELEVENLABS_API_KEY` from the environment in the CLI keyring if present.
4. **First run on this machine** (`profile.json` exists but `config.json` has no `onboarded: true`): run the `/reel-setup` onboarding questions once (premium services or free, brand handle/accent, language, mode question on/off), save them, set `onboarded: true`. Later runs never ask again.
5. **Asks** that remain (e.g. "free fallbacks in use") are *not* questions mid-run: proceed with the plan and list them in the final report.
6. **What you were given:** check every input before planning. A topic or URL → research it. A video file → presenter footage (if it shows a person talking) or source material for quicktake. Images → visual sources (screenshots, brand assets). A portrait → avatar only if the user says it is theirs/consented. Missing files referenced in the request → ask once, or continue without them.
7. Read `~/.reel-factory/config.json` (brand, voice, budgets, `browser_capture`, `modes.ask`) and `learnings.md`. The mode table and the plan must reflect the profile: modes that need unavailable capabilities show their fallback.
3. Read playbook.md, modes/INDEX.md, formats.md and hooks.md now. Run `RF modes` (availability + recent history).

### 1. Topic (Mode 1 only)
Launch agent `reel-factory:trend-scout` with the current date and any niche hint. It runs `RF trends`, adds web-search signals, scores candidates per research.md, and returns the top 3 with evidence. **Pick one yourself**: highest score, tie-break on visualisability and freshness of angle. Record why in brief.md. For `--count N`, take the top N and loop stages 2–9 per topic.

### 2. Production folder and research
1. `RF new "<working title>"` and use the printed path as `P`.
2. Launch **two `reel-factory:topic-researcher` agents in parallel** (one message, two Agent calls): focus **A = primary source and technical**, **B = reception, context, and fresh angles** (see research.md). Pass `P`, the topic, and the date. They write `P/research/` and return briefs.
3. Merge into `P/research/facts.md` (claims table with ids, mechanism, numbers, angles, caveats, assets, do-not-say).

### 3. Creation mode (the one question)
1. Score every mode on the six fit axes in modes/INDEX.md using the research (shape, visual supply, register, audience, freshness, variety vs history). Unavailable modes show their fallback.
2. If `--mode <id>` → use it. If `--mode ai`, `--count`, or `config.modes.ask` is false → **AI Select** (INDEX.md: full deliberation, may borrow ≤ 2 devices from another mode, 3–5 line justification).
3. Otherwise present the choice: a chat table of all 10 modes (★ recommended, fit score, availability, and a **topic-specific** one-liner of what *this* reel would look like in that mode), then one `AskUserQuestion` (header "Mode") with: the recommended mode "(Recommended)", the 2nd and 3rd best, and "AI Select". The remaining mode names go in the question text; "Other" accepts any mode id. Descriptions must be written for this topic, never the generic `one_liner`.
4. Read `references/modes/<id>.md`. Record mode, runner-up and reason in brief.md. Presenter + `--footage` not yet supplied → you will write the script, then ask the user to record it (stage 7).

### 4. Strategy brief: `P/brief.md`
Decide and justify in a few lines each: **mode** (from stage 3) and **skeleton** (formats.md, compatible with the mode), **target viewer** (identity callout), **core promise** (one sentence), **angle** (the most surprising true one), **5 hook drafts**, scored, with the winner, **re-hook**, **honesty beat**, **CTA** (type and keyword), **target length** (inside the mode's range), **theme, accent, caption style, layout** (mode defaults unless there's a reason), **mode devices** (banner / slate / progress / hook sticker / typewriter / annotations), **music mood and prompt**, and **visual plan** (which facts become which scene types, and which images/b-roll are worth generating, within budget).

### 5. Script and storyboard: `P/storyboard.json`
Write the full storyboard per storyboard-schema.md **and the mode playbook**: `meta.mode`, `skeleton`, every scene with `vo` (silent mode: `dur` instead), `type`, `props`, `enter`, and optional `assets`, `label`, `rehook`, `sfx`. Use the mode's scene types and overlays and its beat template, so the reel is genuinely built the mode's way (not a kinetic reel in another theme). Apply the playbook: hook at 0 s, one claim per scene, a pattern interrupt every 8–12 s, re-hook at 40–60%, the honesty beat, the CTA. Also write `caption`, `hashtags` (5–8 specific), `sources_in_caption`, `emphasis`, `music`, `cover_at`. Save a readable `P/script.md` (VO, or on-screen text for silent mode, scene by scene).

### 6. Review loop (fresh eyes, before spending credits)
Launch **in parallel**: `reel-factory:script-critic` (qa-rubric A incl. **mode fidelity**) and `reel-factory:fact-checker` (every claim vs facts.md and sources). Apply all blocking fixes and any improvement that raises a score. If the critic's average is below 4 or any score is below 3, revise and run the critic once more (max 2 rounds). Log the changes in brief.md.

### 7. Assets, voice and music
1. Free assets first: `RF sources repo <owner/name> --prod P`, `RF sources og <url> --prod P` (screenshots for walkthrough/quicktake/receipts zooms). Update the storyboard with live numbers and paths. For walkthrough actions, open each screenshot and set coordinates on the real element.
2. Generated visuals: `RF image P` (budget-aware; the story and cinematic modes may raise the budget for this reel: say so). Avatar/b-roll only if enabled and the brief justifies it (state the credit cost first).
3. **Voice, by mode:**
   - narrated modes: `RF voice P` (ElevenLabs with exact timing, or the free fallback; it cuts dead air and retimes toward 200 wpm; story mode can target 190 via `voice.target_wpm`). Check the reported wpm. Re-tune pacing without new TTS via `RF voice P --retime`. Regenerate TTS only when `vo` text changed.
   - presenter with footage: give the user the final `script.md`, recording instructions (phone at face height, quiet room, start on the hook, ~200 wpm, one take), and wait for the clip; then `RF voice P --footage <clip>`.
   - silent: `RF voice P` just records "no VO".
4. `RF music P` (skip if `music.none`). **Silent mode: music before build** (the beat grid comes from it).

### 8. Build, render, QA
1. `RF build P`, then read its warnings (scenes under 0.6 s or over the mode's max → merge or split the `vo` and re-run voice **only if text changed**; otherwise adjust props).
2. `RF render P --draft`. Extract 3–4 stills (hook at 0.3 s, mid, CTA) with ffmpeg, **look at them**, fix overflow, legibility, or device collisions in the storyboard props, then re-run `RF build P` (no new voice). For `--draft` runs, stop here.
3. `RF render P` (full), then `RF qa P` (thresholds per mode).
4. Launch `reel-factory:qa-reviewer` with `P`. On `FIX`: edit storyboard props or timing → `RF build P` → `RF render P` → `RF qa P` (max 2 loops). On `REDO`: return to stage 5.

### 9. Deliver and learn
1. Final output: `P/out/reel.mp4`, `P/out/cover.jpg`, `P/out/caption.txt` (render also appends the production to `~/.reel-factory/history.jsonl`). Append a short "what worked / what to improve" entry to `~/.reel-factory/learnings.md` (concrete, no duplicates).
2. Report to the user: topic and why it was chosen (Mode 1), the **creation mode** (and whether it was the user's pick or AI Select), skeleton, hook, length, theme, the path to the MP4, QA results, credits used (voice chars, music, images), any fallbacks used, and open issues. Keep it short.

## Guardrails
- **Credits:** paid generation only for shipped assets and only after review. Generate the voice once per final script. Never loop paid generation to retry style; change prompts deliberately.
- **Truth:** no claim without a facts.md source; never fabricate numbers, quotes, comments, or star counts; use absolute dates. Receipts and newsroom modes show the source on screen.
- **People:** no generated likeness of real people and no fake endorsements; news about people uses reputable outlets and allegation language. Story protagonists are always fictional.
- **Media rights:** never repost another creator's video; official press/launch media only, credited; no movie or TV frames as reaction clips.
- **Browser automation** (agent-browser) only when `config.browser_capture` is true, and only for public, read-only pages. Otherwise use APIs, og:images, and rebuilt UI.
- **Files:** everything lives inside `P`. Never write into the plugin folder during `/reel` (learnings go to `~/.reel-factory`); the knowledge base is edited only by `/reel-learn`.
