---
name: reel-factory
description: "Produce a complete, publish-ready Instagram Reel (1080x1920 MP4 + cover + caption) end-to-end like a production studio — trend discovery or a given topic → multi-agent research → creation mode → script → layered edit (one consistent AI presenter integrated as a layer with full-body performance, real footage and news excerpts, highlighted source screenshots, cut-out stickers, motion graphics, camera moves) → ElevenLabs voice/music + HeyGen presenter → Remotion studio render → automated edit gates + visual QA. Use when the user runs /reel, asks to make/create/produce a reel, short, TikTok or vertical video, wants a trending topic turned into a reel, or wants to analyse reference reels to improve the system."
version: 3.1.0
---

# Reel Factory: autonomous reel production

You are the **Creative Director and producer**. You own strategy, script, storyboard, art and audio direction, because those decisions must stay coupled. Specialist agents give you independent research and *fresh-eyes* review. The tools in `${CLAUDE_PLUGIN_ROOT}/scripts` do all media work.

**Autonomy contract:** the user gives a topic, or nothing (trend mode). You make every creative and technical decision yourself and log each one in `brief.md`. There is exactly **one** sanctioned question: the creation-mode choice in stage 3 (skipped with `--mode`, `--count`, or `config.modes.ask: false`). Presenter mode with the user's own footage is the only step that waits for the user (they record the script). Missing credentials or setup never stop a run: degrade to free fallbacks and report it at the end. **Owner rules (2026-11-25):**
- **The final script needs the owner's explicit approval** before any voice or presenter generation (stage 6b, enforced by `RF approve`). This is compulsory.
- **Apart from that gate, never ask anything mid-run.** No "spend these credits?" (the normal per-reel HeyGen/ElevenLabs budget is pre-approved) and no option menus. Decide, log in brief.md, deliver.

`RF` below means: `python "${CLAUDE_PLUGIN_ROOT}/scripts/rf.py"`

## Knowledge (read before deciding; it's the reason this beats generic scripts)

- `references/README.md`: map of the knowledge base (what lives where) and how it evolves.
- `references/playbook.md`: **read every run.** Rules distilled from the corpus (105 reels).
- `references/modes/INDEX.md`: **read every run.** The 10 creation modes, fit scoring, how to present the choice, AI Select, mode × skeleton compatibility, fallbacks. Then read the **chosen mode's playbook** `references/modes/<id>.md`.
- `references/formats.md`: 11 story skeletons (beat order) with ids. **Read every run.**
- `references/hooks.md`: hook, re-hook, honesty, and CTA libraries. **Read every run.**
- `references/studio.md`: **read every run.** The studio engine: the presenter, layouts, shots, graphics, looks, sourcing policy, edit gates, beat recipe. This is how reels are built now.
- `references/categories/INDEX.md`: **read every run, then only the matching category file(s)**. Subject categories with their own construction (agent skill/plugin/MCP, GitHub repo, open-source alternative, top-N list). A category's devices apply only to reels of that category; incident, news, explainer and story reels use none of them.
- `references/storyboard-schema.md`: exact JSON contract of the legacy scene types (reused as studio `scene` shots), speech-synced props. **Read before writing the storyboard.**
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
Launch agent `reel-factory:trend-scout` with the current date and any niche hint. It runs `RF trends` and `RF news leads` (the owner's daily newsletter archive, ranked by newsletter coverage), adds web-search signals, scores candidates per research.md, and returns the top 3 with evidence. **Pick one yourself**: highest score, tie-break on visualisability and freshness of angle. Record why in brief.md. For `--count N`, take the top N and loop stages 2–9 per topic.

### 2. Production folder and research
1. `RF new "<working title>"` and use the printed path as `P`.
2. **Source map.** Classify the topic in `references/sources.json → routing` and note the source types, `rf intel handles` and subreddits to cover.
3. Launch **two `reel-factory:topic-researcher` agents in parallel** (one message, two Agent calls):
   - focus **A = Origin Hunter**: official posts, X originals, repos, papers, docs;
   - focus **B = Coverage & Community**: press breadth, Reddit, HN and X reactions with engagement, angles.

   Pass `P`, the topic, the date and the source map. Both use `rf intel` (research.md) and fill the evidence ledger `P/research/sources.json`.
4. **Ledger gate.** Run `RF intel score --prod P`. Every warning must be resolved (or logged as impossible, with what was searched) before scripting.
5. Merge into `P/research/facts.md` (claims table with ids, mechanism, numbers, angles, caveats, assets, do-not-say).

### 3. Creative combination (the one question): structures + elements, multi-select
1. Score every mode on the six fit axes in modes/INDEX.md, using the research: shape, visual supply, register, audience, freshness, and variety vs history. Unavailable modes show their fallback. Then shortlist the **elements** that fit the topic (INDEX.md element table).
2. If `--mode <id>[,<id>…]` was given, use that sequence. If `--mode ai`, `--count`, or `config.modes.ask` is false, run **AI Select** (INDEX.md: a combination-aware deliberation with justification).
3. Otherwise:
   - Print the structures table and the elements table, all **topic-specific**, plus the recommended combination as one concrete line.
   - Then make **one** `AskUserQuestion` call with two multi-select questions: "Structures" (top 3 + AI Select; Other = mode ids in order) and "Elements" (top 4).
   - Validate the picks against the combination rules.
4. Read `references/modes/<id>.md` for every chosen structure. Record mode, runner-up and reason in brief.md. Presenter + `--footage` not yet supplied → you will write the script, then ask the user to record it (stage 7).

### 4. Strategy brief: `P/brief.md`
Decide and justify in a few lines each: **category** (`categories/INDEX.md`: the matching id(s) → `meta.category`, or "none"; when one matches, its beat order, proof shots, CTA and caption rules shape every decision below), **mode** (from stage 3) and **skeleton** (formats.md, compatible with the mode), **target viewer** (identity callout), **core promise** (one sentence), **angle** (the most surprising true one), **5 hook drafts**, scored, with the winner, **re-hook**, **honesty beat**, **CTA** (type and keyword), **target length** (inside the mode's range), **theme, accent, caption style, layout** (mode defaults unless there's a reason), **mode devices** (banner / slate / progress / hook sticker / typewriter / annotations), **music mood and prompt**, and **visual plan** (which facts become which scene types, and which images/b-roll are worth generating, within budget).

### 5. Storyline, narration, storyboard: `P/storyboard.json`
Load the **speechwriting** skill and follow it in order:
1. a beat sheet in brief.md;
2. `narration` paragraphs (spoken, connected, with `tts` delivery markup where useful) written before any visual;
3. the visuals hung on the speech with scene `cue`s.

**Engine: `meta.engine: "studio"` (default; studio.md).** Each scene is one narration beat with `vo`, `layout`, `motion` (presenter direction when he is visible), `shots` (a new visual every 1–2.5 s, anchored to phrases), and `gfx`. Set `meta.look` (studio / intel / cutout). Plan presenter time against the cost cap (≈ 30–45 s on screen). Only pure faceless motion-graphics or silent formats may use the legacy scene engine. Write the full storyboard per studio.md, storyboard-schema.md **and the mode playbook**: `meta.mode`, `skeleton`, `narration`, every scene with `cue` (silent mode: `dur` and no narration), `type`, `props`, `enter`, and optional `assets`, `label`, `rehook`, `sfx`. Use the mode's scene types and overlays and its beat template, so the reel is genuinely built the mode's way (not a kinetic reel in another theme). Apply the playbook: hook at 0 s, one claim per scene, a pattern interrupt every 8–12 s, re-hook at 40–60%, the honesty beat, the CTA. Also write `caption`, `hashtags` (5–8 specific), `sources_in_caption`, `emphasis`, `music`, `cover_at`. Save a readable `P/script.md` (VO, or on-screen text for silent mode, scene by scene).

### 6. Review loop (fresh eyes, before spending credits)
Launch **in parallel**: `reel-factory:script-critic` (qa-rubric A incl. **mode fidelity**, and **category fidelity** against the `categories/<id>.md` file when `meta.category` is set) and `reel-factory:fact-checker` (every claim vs facts.md and sources; every number and the CTA keyword identical across VO, screen and caption). Apply all blocking fixes and any improvement that raises a score. If the critic's average is below 4 or any score is below 3, revise and run the critic once more (max 2 rounds). Log the changes in brief.md.

### 6b. OWNER SCRIPT APPROVAL: hard gate, compulsory (owner rule, 2026-11-25)
No voice, music or presenter generation (and no HeyGen video job) until the owner has approved the **final** script. The NVIDIA reel burned 41 HeyGen credits on three script rounds. This is the single exception to "never ask mid-run".
1. Show the owner the complete final script in one message:
   - every narration paragraph, verbatim;
   - each soundbite hand-off with the speaker, the outlet and the exact words;
   - the hook line called out on its own;
   - one line each on length and planned spend.
2. Ask with one `AskUserQuestion`: approve / change (Other = their edits). Apply every change, re-run the fact-check on changed claims, and show the script again. Repeat until the owner explicitly approves. "Looks good" counts; silence or "continue" without approval does not.
3. Only then run `RF approve P`. It records the script fingerprint in `P/approval.json`. `RF voice` and `RF presenter` (except `--dry-run`) refuse to run without a matching approval, and any later edit to the narration or soundbites voids it. Never run `RF approve` on your own judgement.
4. Free work may continue while you wait (captures, footage, shots, the presenter `--dry-run`, draft builds without voice).

### 7. Assets, voice and music
1. **Real sources as real screenshots (hard rule, playbook.md):**
   - Every web source shown on screen (headline, post, blog/press/help line, README line) becomes a `source` scene.
   - Build it with `RF shot <capture> --prod P --name <id> --find "<spoken phrase>"`.
   - Capture with Firecrawl (`firecrawl_scrape`, `formats: ["screenshot"]`, `mobile: true`). If Firecrawl is unavailable, use agent-browser on the public URLs after asking the owner with the exact list (no asking when `config.source_shots_browser` or `browser_capture` is true).
   - Text cards are only a logged fallback.
   Then free assets: `RF sources repo <owner/name> --prod P`, `RF sources og <url> --prod P` (screenshots for walkthrough/quicktake/receipts zooms).
   **Footage (studio.md §6):** for every beat that names a person, product or event, find real footage: `RF footage find "<query>" [--source youtube|commons|nasa|archive]`, pick the clip that shows exactly that, then `RF footage get <url> --prod P --name <id> --start S --dur 3-6 --label "<outlet>"` and paste the printed shot JSON. **Soundbites (owner rule):** when real people react to the story on video, add 2–3 `soundbites` (studio.md §3): `RF footage get … --audio`, the speaker on camera the whole span, cropped tight, labelled, placed where the presenter is off; they speak with their own voice while the narration pauses. Silent b-roll alone is not enough. **Cut-outs:** `RF cutout <photo-url> --prod P --name <id>` for people, products and logos as stickers. Update the storyboard with live numbers and paths. For walkthrough actions, open each screenshot and set coordinates on the real element.
2. Generated visuals: `RF image P` (budget-aware; the story and cinematic modes may raise the budget for this reel: say so). B-roll only if enabled and the brief justifies it (state the credit cost first).
   - **The presenter (studio engine):** **after** the voice gate passes, run `RF presenter P --dry-run` (windows, seconds, cost). If it exceeds the cap, shorten presenter layouts (turn some beats `off`), then render. It renders only his visible spans with HeyGen Avatar IV and each beat's `motion`, as transparent WebM, and reuses identical renders. **HeyGen MCP first (plan credits), API only as backup:**
     0. **Outfit and pose first (owner rule: a new outfit AND a new resting pose every reel, the same face, zero wasted credits).**
        - Read `~/.reel-factory/avatars/host/profile.json → looks` (look id → `last_used`).
        - Pick an outfit that fits this reel's topic and look and that wasn't used in the last reel, and set `storyboard.meta.presenter_look` to its look id.
        - If no unused look suits the reel, make one before rendering. **Cheapest measured route = 3 HeyGen credits total. Log the total in brief.md; never take a costlier route:**
          1. `create_image` (nano-banana-2.1) editing the base look's public `preview_image_url` (from `get_avatar_look`), prompt "change ONLY the clothes to … and the resting pose to … (facing camera, waist-up, hands visible; never the previous look's pose); keep the face, hair, framing and background" → **2 credits** (measured 2026-11-17).
          2. Download it, upscale 2× (lanczos, to about 1536×2752) if smaller, then `create_asset_upload` → PUT → `complete_asset_upload` → `create_photo_avatar` with `avatarGroupId` set to the host's group → **1 credit** (every route pays this step). Wait until `get_avatar_look` shows completed, then record the look in `profile.looks` (name, source, created, credits).
          - **Never use `create_look_remix`:** heygen-image-1 bills $0.28 per image (≈ 6 credits). Measured 2026-11-24: remix + photo avatar = **7 credits** (570 → 563). The 3.4.1 claim that it cost 1 credit was never measured and was wrong.
          - Check `get_current_user` before and after and log the real spend in brief.md. If the balance drops more than quoted, use no further paid route that run and report it in the final summary.
        - The presenter renders on a transparent background over the fixed set, so only the clothes and the pose change.
        - Gestures: give every presenter window a different `motion`. When one beat holds two presenter windows (e.g. `close` → `off` → `close`), put the motion on each layout entry (`{"at": "…", "layout": "close", "motion": "…"}`); it overrides the beat motion for the window it opens. Motion prompts cost nothing extra.
        - Never render presenter windows before the outfit is chosen. Never test-render without the owner's OK.
     1. `RF presenter P --jobs` writes `P/public/presenter/jobs.json`: `avatar_id`, `engine`, `aspect_ratio`, `resolution`, `output_format: webm`, `expressiveness`, and per job `wav`, `out`, `motion`, `seconds`. Empty `jobs` → skip to step 4.
     2. If the `heygen` MCP tools are available (`mcp__heygen__*`): `get_current_user` for remaining plan credits. Then for each job: `create_asset_upload` for the wav → PUT the file to the returned URL with `curl -T` → `complete_asset_upload` → `create_video_from_avatar` with the job's avatar_id, the audio asset, engine, 9:16, 1080p, webm/transparent background, the `motion` as motion prompt and expressiveness. Start all jobs, then poll `get_video` until `completed`, and download each `video_url` with curl to exactly the job's `out` path.
        - Verified on 2026-11-16 with the host look. The PUT must send every `upload_headers` entry (`content-type`, `x-amz-server-side-encryption`).
        - Create call: `avatarId`, `audioAssetId`, `engine: {"type": "avatar_iv"}`, `aspectRatio: "9:16"`, `resolution: "1080p"`, `outputFormat: "webm"`, `motionPrompt`. The MCP has no expressiveness setting.
        - Always pass the engine. Left unset, the MCP uses Avatar 6 Turbo, which would change the host's look.
        - Tested 2026-11-17 on the Creator plan:
          - Avatar IV with `motionPrompt` costs plan credits at 16/min, with **no** "Custom Expressive Motion" surcharge (about 11 credits for 40 s of presenter).
          - Avatar 6 Turbo costs 20/min. Its framing is tighter, its gestures are weaker, and it leaves edge artifacts. Keep `avatar_iv`.
        - Output is VP9 with alpha and no watermark. The Free plan renders at 720p and queues slowly (a 4 s clip took about 18 min). Wait with a background `sleep` between polls.
     3. Use the API backup instead (skip MCP for the rest) when: the MCP tools are missing or unauthorised, credits are exhausted or too low, a create call is refused for credits, or the tool cannot take our own audio or return a transparent WebM (alpha is required). Never re-render a job the MCP already finished.
     4. `RF presenter P` (always). Files already present are reused for free; only what is still missing goes to the API wallet, within `max_usd_per_reel`. This step also writes `storyboard.presenter`. Log in brief.md which route rendered each window.

     Disclose "AI-generated presenter" in the caption.
3. **Voice, by mode:**
   - narrated modes: load the **voice** skill, then run `RF voice P`. It produces stitched paragraph segments on eleven_v4, natural-articulation tempo, pause shaping by sentence/comma/paragraph boundary, and the listening report `out/voice-report.md`.
     - **The gate must PASS before build.** Fix cheap first: `--retime` (no credits), then `--regen <paragraph ids>` after fixing that paragraph's `tts` or the `lexicon`, then rewrite the narration.
     - Never regenerate the whole take to "try again".
   - presenter with footage: give the user the final `script.md`, recording instructions (phone at face height, quiet room, start on the hook, ~200 wpm, one take), and wait for the clip; then `RF voice P --footage <clip>`.
   - silent: `RF voice P` just records "no VO".
4. `RF music P` (skip if `music.none`). **Silent mode: music before build** (the beat grid comes from it).

### 8. Build, render, QA
1. `RF build P`, then read its warnings (scenes under 0.6 s or over the mode's max → merge or split the `vo` and re-run voice **only if text changed**; otherwise adjust props).
2. `RF render P --draft`. Extract 3–4 stills (hook at 0.3 s, mid, CTA) with ffmpeg, **look at them**, fix overflow, legibility, or device collisions in the storyboard props, then re-run `RF build P` (no new voice). For `--draft` runs, stop here.
3. `RF render P` (full), then `RF qa P`. The studio edit gates block: ≥ 40 big picture changes/min and ≤ 3 % static seconds. On a fail, add shots or camera moves (studio.md §7), rebuild and re-render; no new voice or presenter renders are needed unless the narration changed.
4. Launch `reel-factory:qa-reviewer` with `P`. On `FIX`: edit storyboard props or timing → `RF build P` → `RF render P` → `RF qa P` (max 2 loops). On `REDO`: return to stage 5.

### 9. Deliver and learn
1. Final output: `P/out/reel.mp4`, `P/out/cover.jpg`, `P/out/caption.txt` (render also appends the production to `~/.reel-factory/history.jsonl`). Append a short "what worked / what to improve" entry to `~/.reel-factory/learnings.md` (concrete, no duplicates).
2. Report to the user: topic and why it was chosen (Mode 1), the **creation mode** (and whether it was the user's pick or AI Select), skeleton, hook, length, theme, the path to the MP4, QA results, credits used (voice chars, music, images), any fallbacks used, and open issues. Keep it short.

## Guardrails
- **Credits:** paid generation only for shipped assets and only after review. Generate the voice once per final script. Never loop paid generation to retry style; change prompts deliberately.
- **Truth:** no claim without a facts.md source; never fabricate numbers, quotes, comments, or star counts; use absolute dates. Receipts and newsroom modes show the source on screen.
- **People:** no generated likeness of real people and no fake endorsements; news about people uses reputable outlets and allegation language. Story protagonists are always fictional. The show's presenter is the one synthetic host in `~/.reel-factory/avatars/host` (never a real person's face).
- **Media rights:** never repost another creator's video. Owner policy (2026-11-14): official/press media and free-licence stock first; short news/YouTube excerpts of real people and events (≤ 6 s each, a few per reel) are allowed with a visible source label and never altered to change meaning.
- **Browser automation** (agent-browser) only when `config.browser_capture` is true, or for source screenshots of public pages after the owner approves the exact URL list (pre-approved when `config.source_shots_browser` is true), and only for public, read-only pages. Otherwise use APIs, og:images, and rebuilt UI.
- **Files:** everything lives inside `P`. Never write into the plugin folder during `/reel` (learnings go to `~/.reel-factory`); the knowledge base is edited only by `/reel-learn`.
