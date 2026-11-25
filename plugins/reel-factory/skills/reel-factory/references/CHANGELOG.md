# Knowledge-base changelog

## 3.6.5 (2026-11-25): compulsory owner approval of the final script

- Owner rule after the NVIDIA reel needed three script rounds (41 HeyGen credits): **the final script must be explicitly approved by the owner before any voice or presenter generation.**
- New SKILL stage 6b. Show the full final script (narration verbatim, soundbite hand-offs, the hook called out, length and spend), ask once, apply changes and show it again until approved, then run `rf approve P`.
- New `rf approve` (scripts/approve.py) writes P/approval.json with a fingerprint of the narration text/tts and the soundbites. `common.require_approval` makes `rf voice` (except `--report`) and `rf presenter` (except `--dry-run`) refuse without a matching approval. Any later script edit voids it.
- This is the one exception to "never ask mid-run". /reel command and voice skill updated.

## 3.6.4 (2026-11-25): news hooks lead with the newest development

- The owner rejected the NVIDIA v3 opening "Jensen Huang quit Nvidia after…": he was already back, so the first words reported outdated news and viewers skip. hooks.md (opening lock STOP + a "News reversal / update" row), speechwriting and the script-critic hard checks now require the LATEST development in the first ~5 words, with older events after it as the amplifier ("Nvidia just brought Jensen Huang back as CEO, only eleven days after he quit…").
- `rf render` chunked fallback is leaner: 60-frame chunks, 1 worker, a 600 MB OffthreadVideo cache and 6 tries each. At about 60 MB free RAM the 240-frame / 2-worker chunks failed 4 times on the first chunk; the lean settings rendered.

## 3.6.3 (2026-11-25): speech that a newcomer understands + no mid-run questions

- The owner rejected the NVIDIA reel v1. The hook's promise line ("Here's how a CEO gets his job back in 11 days") read as a tutorial. It passed through NVIDIA's euphemisms ("target of a foreign intelligence effort", "unfaithful"). It left the key person (the alleged spy) unnamed. It dropped the petition / employees / Musk / Kalanick / Trump beat that both reference reels had. The last soundbite clipped its final word.
- speechwriting SKILL: reference beats are mandatory (cut length elsewhere); plain words instead of source euphemisms, attribution kept; the promise line points at the story or twist, never a how-to.
- script-critic: new blocking hard checks (newcomer clarity, reference beats, hook promise, names, soundbite ends).
- studio.soundbite_plan / rf build: warn when a soundbite cut lands inside or within 0.25 s of the last word's end.
- reel-factory SKILL: never ask the owner anything mid-run (normal per-reel HeyGen/ElevenLabs budget pre-approved); over-quote spend is reported at the end instead of asked.

## 3.6.2 (2026-11-25): low-RAM renders + soundbite-aware QA

- Root cause of the NVIDIA reel's "No frame found" render failures was memory, not a worker race: with ~0.1–0.6 GB free (other apps), OffthreadVideo's frame cache evicts frames before use (Remotion docs). Concurrency 1 and an explicit `--offthreadvideo-cache-size-in-bytes` both still failed; the full render passed in 296 s once RAM was freed. `rf render` drops the 3.6.1 concurrency retry and instead falls back to a chunked render (bundle once, 240-frame muted chunks with 4 tries each, audio pass once, lossless join). If chunks still fail, free RAM (close apps) — that is the real fix.
- `rf qa` WER: long-form Whisper drifts at a change of speaker and drops whole soundbites (24.8 % false FAIL; each clip transcribed perfectly alone). QA now re-hears every soundbite span on its own and replaces that span's words (→ 4.8 %).

## 3.6.1 (2026-11-25): render resilience

- Full studio renders hit Remotion's compositor race ("No frame found at position…") on different clips/frames at concurrency 3 (NVIDIA reel, 26 shots + 4 soundbites + 7 presenter streams). `rf render` now retries once at `--concurrency=1` when the log shows that error.
- `rf build` warns when a video shot's on-screen span (+ trim) is longer than its clip — drafts tolerate it, the full render fails. Fix with a longer `rf footage get --dur` or an earlier cut.

## 3.6.0 (2026-11-24): soundbites (real people speaking with their own voice)

- Owner: "use actual video clips… there was no voice and focus in the video clips." The references let real people speak on camera; our footage was muted b-roll under narration.
- New storyboard `soundbites` (studio.md §3): the narration pauses after a phrase, the clip plays full-frame with its own sound and captions. `rf footage get --audio` keeps the sound. `studio.soundbite_plan / apply_soundbites / soundbite_audio` warp the compiled timeline at build time only and write `public/vo_sb.mp3`; `vo.mp3` and presenter renders are untouched (0 new HeyGen credits). Optional `text` fixes ASR wording in captions. `rf qa` includes soundbite speech in the WER reference. Selftest in studio.py.
- First used on the Riemann reel: Brian Greene (World Science Festival), Jon Keating (Numberphile), Tony Padilla (FRANCE 24).

## 3.5.3 (2026-11-24): consistency check ignores calendar years

- `common.consistency_issues` compared years as quantities ("screen says 1,859 but the caption says 2,026" on the Riemann reel). Whole numbers 1000–2100 now count as years and are skipped; selftest added.
- HeyGen MCP note: the create call's default engine is now Avatar 6 Turbo. Always pass `engine: {"type": "avatar_iv"}` (measured 16 credits/min, rounded up per video: 9 windows / 40.7 s = 12 credits).

## 3.5.2 (2026-11-24): outfit route re-measured; 3.4.1 was wrong

- 3.4.1 priced `create_look_remix` at 1 credit without measuring it. HeyGen bills heygen-image-1 at $0.28 per image (≈ 6 credits); the Riemann reel's outfit cost remix + photo avatar = **7 credits** (570 → 563).
- SKILL.md step 0 now uses the measured cheapest route: `create_image` edit of the base look (2) + `create_photo_avatar` (1) = **3 credits**. `create_look_remix` is banned. Check the balance before and after every paid HeyGen step, and stop and tell the owner when it drops more than quoted.

## 3.5.1 (2026-11-23): use the routine's decoded links

- When the routine's `stories.json` link carries `decoded` (a destination decoded offline in the cloud), `rf news` uses it and skips network resolution.

## 3.5.0 (2026-11-23): newsletter intel (`rf news`)

- New `scripts/news.py`, run as `rf news`. It ingests the owner's daily Gmail-newsletter routine ZIP (`*_AI-Tech-Newsletters.zip` in ~/Downloads):
  - extracts it safely (zip-slip guard);
  - dedups emails by Gmail message ID across days;
  - parses stories from the routine's `stories.json`, or from the digest .md as a fallback;
  - resolves substack/beehiiv tracking redirects to real URLs (HTTP plus meta-refresh, with a cache);
  - downloads images the cloud run could not fetch;
  - links the same story across days into threads.
- Commands:
  - `rf news leads`: threads ranked by distinct-newsletter coverage, for momentum.
  - `rf news grep`: searches stories and raw email bodies, for research.
  - `rf news selftest`.
- Store: `config.json → news.dir`. Wired into trend-scout (step 1b), topic-researcher (A0, B3), research.md and SKILL.md stage 1. Newsletter text is a lead only and is never ledgered as a source or shown on screen.

## 3.4.1 (2026-11-18): outfit route corrected to the cheapest

- 3.4.0 made the HeyGen `create_image` edit the default outfit route (3 credits). That was wrong: a free reference photo + `create_look_remix` (1) + `create_photo_avatar` (1) = **2 credits** is the default now. `create_image` needs the owner's OK, and a failed cheap step means asking before any costlier route. (Owner: zero wasted credits; the design-skills reel spent 1 credit more than needed.)

## 3.4.0 (2026-11-18): new pose with every outfit; a different gesture for every window

From the first `agent-skill` + `top-n` production (Claude design skills).
- **Outfit step (SKILL.md stage 7, step 0).** The verified route is HeyGen `create_image` (nano-banana-2.1) editing the base look's preview URL, then a 2× upscale, then `create_photo_avatar` in the host group: 3 credits in all. Owner rule: the same edit also changes the **resting pose**, so each reel has a new outfit and a new pose at no extra cost. ElevenLabs Flows images need the Pro plan; a free-licence reference with `create_look_remix` remains the fallback.
- **Per-layout `motion`** (`studio.py`, `presenter.py`, studio.md). A beat whose layout list opens two presenter windows used to send the same gesture prompt twice. A layout entry can now carry `"motion"`, which replaces the beat motion for the window it opens. Reels without layout-level motion are unaffected: same cache keys, `jobs: []`.

## 3.3.0 (2026-11-17): batch-04 → subject categories (dev-tool reels), consistency check

**Corpus:** "AI Dev Tools Reels" Parts 01–02 (100 files) → 42 new + 58 already in the library. All 100 `.md` files (captions, links, on-screen text) were mined, including the known reels. 9 parallel analysts; notes in `analysis/notes/batch-04-*.md`.

**Added: a category layer** (`references/categories/`), read only when a reel's subject matches:
- `agent-skill` (skills / plugins / MCP servers for a task), `github-repo`, `oss-alternative` (villain-first beat order), `top-n` (list COMMIT devices, item grammar, recap).
- `INDEX.md` explains *why* dev-tool reels are built differently from incident/news reels (the viewer shops for a tool vs. wants to understand an event). Category devices are never applied to other reel types.
- SKILL.md: category chosen in the brief (`meta.category`); script-critic checks category fidelity only when it is set. README: a "scope before you write" rule for future `/reel-learn` runs.
- The general files (playbook, hooks, formats, modes, techniques) are unchanged by this batch.

**Engine (optional studio gfx, no effect unless used):** `sticker.strike` (red slash across a rival logo), `label.icon` (logo pill), kind `callout` (tag + leader line to `tx,ty`). Typechecked; still rendered and inspected.

**Scripts:**
- `common.consistency_issues`: numbers (≥ 100, rounding ≤ 7 % allowed, clock times ignored) and the CTA keyword must agree across VO, screen and caption. `rf build` logs a warning; `rf qa` reports a non-blocking check. 7 of the 100 reference reels contradict themselves; our 3 shipped reels pass.
- `rf ingest`: library reels from older batches were stored with paths relative to the project root, so fine-hash verification couldn't find them and returned 0.00. 9 known reels were then mislabelled as new. Sources now resolve against `--source-root` or the cwd; if one is still missing, the coarse verdict stands with a warning.

## 3.2.0 (2026-11-17): presenter wardrobe, number-aware WER

- **Presenter outfits** (owner rule: a new outfit every reel, the same face, zero wasted credits):
  - `storyboard.meta.presenter_look` picks a look in the host's avatar group, and `presenter.py` renders with it.
  - `profile.json → looks` records `last_used`, so outfits rotate.
  - The render cache key includes the look only when it differs from the default, so existing renders stay reusable.
  - SKILL.md step 0 makes the outfit the first step before any presenter render: a reference image via `RF image`, then `create_look_remix` (1 credit), then `create_photo_avatar` in the host group.
- **WER scoring** (voice gate and `rf qa`): spelled numbers, hyphens, slashes and thousands separators are normalised on both sides, so "forty-five" equals "45" and "9/11" equals "9 -11". A number-heavy take went from a false 9.3% FAIL to 1.6% PASS with the same audio.
- **Lesson:** HeyGen plan credits round up per video. 7 windows totalling 39.6 s cost 12 credits, not 10.6, so fewer, longer presenter windows are cheaper.

## 3.1.9 (2026-11-17): no more stalled captures

- `rf shot <url>` used to hang forever. The first agent-browser call spawns its daemon, which inherited the output pipe, so `subprocess.run(capture_output, timeout)` never returned. Output now goes to a temp file, the call waits only on the CLI process, and the process is killed on timeout. A URL capture now takes about 12 s.
- The topic-researcher has a hard no-stall rule: every external command runs under `timeout`, anything past 3 minutes is killed and replaced with a fallback, and the research file is written early.
- MCP presenter notes (3.1.8): Avatar IV with `motionPrompt` is charged with no expressive-motion surcharge. Avatar 6 Turbo was tested and rejected.

## 3.1.6 (2026-11-16): source labels clear Instagram's UI

- Studio shot labels: 210 px from the top in split boxes (clear of the "Reels" header) and 540 px from the bottom on full-height shots. That keeps them clear of the username/caption block and above the off-layout caption line (≈1480). Before, they sat 40 px from the edge, under Instagram's overlays.

## 3.1.5 (2026-11-16): fixes from the Microsoft 365 outage production

- `rf presenter`: the `max_usd_per_reel` cap now counts only the windows still to be rendered by the API. Windows already on disk (HeyGen MCP plan renders, earlier takes) cost $0, so a reel can mix MCP and API renders. The dry-run reports `over_cap` instead of exiting.
- `rf voice --regen`: unknown paragraph ids now stop with an error. Before, `--regen p2,p3` regenerated nothing and left stale audio under new captions (WER 18%). Ids are space-separated: `--regen p2 p3`.
- Lesson: the HeyGen Free plan's monthly Avatar IV allowance is tiny. One 4 s test used it up, and later free jobs fail with `AVATAR_IV_VIDEO_GENERATION_DURATION_LIMIT_REACHED`.

## 3.1.4 (2026-11-16): the opening lock, generalised

- hooks.md "The opening lock": every narrated reel opens with three moves, STOP → AMPLIFY → COMMIT.
- A table covers each reel type (tool, authority launch, list, challenge, tutorial, money, threat, hidden pain, concept, claim, discovery, news ×3, product-for-you), with verbatim examples from the 80 corpus hooks and the batch-03 openings.
- Wired into speechwriting, qa-rubric and script-critic.
- topic-researcher scouts footage and cut-out leads (3.1.2).

## 3.1.0 (2026-11-16): HeyGen MCP first, API as backup

- Presenter renders now go through the HeyGen MCP server (`heygen`, OAuth, HeyGen plan credits). `RF presenter P --jobs` writes `public/presenter/jobs.json` (audio slice, output path, motion direction, avatar, engine); Claude renders each job with the MCP tools and saves it to that path.
- `RF presenter P` then reuses those files at no cost and sends only what is still missing to the API wallet (`HEYGEN_API_KEY`). That happens when plan credits run out or the MCP is unavailable. The `max_usd_per_reel` cap still applies.
- The API key is no longer needed when every render is already on disk.

## 3.0.0 (2026-11-14): studio engine, layered edit, one consistent AI presenter

Built from batch-03 (7 new reference reels) measured against our 2.0 output.
- References: 48–129 big picture changes per minute, 0–6 % static seconds.
- Ours: 10 changes per minute, 9.4 % static seconds.

The reference presenters are AI digital clones performing continuously under the edit. Ours was a mouth-only face in separate cut-away scenes. Root cause: the engine played one full-frame scene at a time.

**Engine**
- New `Studio` composition with layered tracks: presenter (alpha), layout, content shots, graphics, captions, grade, audio.
- 7 presenter framings, animated between: off / full / close / split / card / corner / corner-left.
- A virtual camera on images and screenshots: opens on the masthead, pans and zooms to each highlight as it is spoken; marker / box / underline / strike.
- Footage with cover or blurred fill. Shot transitions: cut, whip, zoom, blur, slide, flash.
- Graphics: cut-out stickers, mono labels, display slams, counters, boxed scene components.
- Studio captions: single-word italic serif, bold, box.
- Looks (format bibles): studio, intel, cutout. Film grain and vignette.
- `rf build` compiles the storyboard's word-anchored edit decisions (`layout`, `motion`, `shots`, `gfx` per narration beat) into the timeline (`scripts/studio.py`). The legacy scene engine is unchanged for old storyboards.

**Presenter**
- One persistent synthetic host (`~/.reel-factory/avatars/host`).
  - Rendered by HeyGen Avatar IV from our own voice track, only for the spans where a layout shows him.
  - Each beat carries its own `motion` direction.
  - Output: transparent WebM over his own set plate.
- Measured cost $0.0425/s. Cap per reel `presenter.max_usd_per_reel` (default $2). `--dry-run` shows windows and cost; identical renders are reused, never paid twice.
- Voice: an Indian-English reel voice to match him.

**Media departments**
- `rf footage find|get`: YouTube, Wikimedia Commons, NASA and Internet Archive search; short excerpts with source labels.
- `rf cutout`: local background removal for sticker cut-outs.
- Owner media policy recorded.

**QA**
- Blocking edit gates measured on the render: ≥ 40 big picture changes per minute, ≤ 3 % static seconds. Presenter share is a warning.
- Presenter pace gate widened to 175–250 wpm (references 167–255).

**Knowledge**
- New `references/studio.md`: cast, layouts, shots, graphics, looks, sourcing, gates, beat recipe.
- SKILL.md now builds every presenter reel on the studio engine.

## 2.0.0 (2026-11-13): natural narration, source intelligence, creative combinations, AI presenter

Built from a measured diagnosis against 89 English corpus reels. Our scripts had a sentence median of 7–9 words (corpus 15), sentence-end pauses of 0.03 s (corpus 0.24 s), no connectors, and research that defaulted to a single trade site.

**Narration**
- New **speechwriting** skill: storyline, then spoken paragraphs, then visual cues.
  - Corpus rules: sentence mix, the connector system, the hook + define pair, viewer bridge, delivery markup.
  - Per-format voice profiles.
- **Storyboard v2:** `narration` paragraphs plus scene `cue`s, so cuts land mid-sentence like the corpus (1.08 per sentence). Legacy `scenes[].vo` is still accepted.
- New **voice** skill and `rf voice` v2:
  - `eleven_v4` default (A/B tested against v3);
  - paragraph segments with `previous_text`/`next_text` stitching;
  - `tts` delivery markup and a pronunciation `lexicon`;
  - natural-articulation tempo (no blanket speed-up);
  - **pause shaping on real silence, by boundary**: sentence 0.18–0.32 s, comma 0.10–0.22 s, paragraph 0.34–0.50 s, mid-phrase glitches removed;
  - `--regen <paragraph>` and `--retime`;
  - a **listening report and gate** (`out/voice-report.md`) that `rf qa` blocks on.

**Research**
- New **`rf intel`** with official and free access paths:
  - Google News across publishers;
  - publisher and company newsroom feeds (22 verified);
  - X posts via the official oEmbed and embed data (text, date, verified, likes, replies);
  - Reddit (OAuth with scores when a key is set, otherwise RSS);
  - GitHub (new repos by stars/day; repo stars, velocity, releases, contributors, commits);
  - HN, arXiv, Hugging Face Papers;
  - full-text `read` via trafilatura.
- **`sources.json` registry:** publisher tiers and on-screen eligibility (TechCrunch is lead only), official, founder and researcher X handles, subreddits by topic, and topic → source-type routing.
- **Evidence ledger** (`research/sources.json`) and **`rf intel score`**, which ranks sources by credibility, originality, engagement, recency and corroboration. Its gates: originals for key claims, no publisher above 30 %, a community signal, and no lead-only source on screen.
- Research agents redefined as **Origin Hunter** and **Coverage & Community**. The trend-scout uses attention signals and the fact-checker verifies against originals.
- **`rf shot` capture ladder:** given a page URL it captures itself, using X's official embed for posts, then a headless phone viewport, then a headed isolated session. It has hard timeouts.

**Creative combinations**
- Structures (the 10 modes, sequenceable as segments) plus **elements** (presenter, source shots, cursor demo, cinematic b-roll, banner, progress, …) with combination rules.
- Two multi-select questions; combination-aware AI Select. `meta.segments` and `meta.elements`.

**AI presenter**
- New `rf presenter`:
  - one consistent avatar identity under `~/.reel-factory/avatars/` (portrait, idle base clip, bound voice);
  - lip-sync of the final voice-over via **HeyGen API v3** (paid, default) or local **MuseTalk 1.5** (free fallback; installer `scripts/install_musetalk.sh`).
- New `presenter` scene type: full-frame and cut in sync.
- Lip-sync covers only the presenter scenes' spans (~4x less GPU time and HeyGen minutes). Per-avatar face-landmark cache. Live MuseTalk log with a stall watchdog (`presenter.stall_seconds`).

**Known plan limits** (detected): ElevenLabs Flows image and video need the Pro plan, so `rf image` falls back to engine visuals on Creator.

## 1.3.0 (2026-11-12): real sources are shown as real screenshots (hard rule)

- **Rule** (`playbook.md` › Credibility): headlines, social posts, blog/press/help lines and README lines appear as the **actual page**, highlighted where the voice-over reads it. Retyped text cards are only a logged fallback.
  - Editing is limited to *around* the content: crop, erase banners and ads, add overlays.
  - The outlet's words, layout and numbers are never altered.
  - The rule is enforced in the agents: researcher, fact-checker, script-critic, qa-reviewer. It is also in qa-rubric A (Credibility) and B9, the newsroom/receipts/quicktake playbooks, research.md, art-direction.md and SKILL.md stage 7.
- **`rf shot`** turns a capture into a source shot. It:
  - erases banners (`--erase`) and auto-crops around the phrases, keeping the masthead;
  - finds the exact phrases with free local OCR (RapidOCR, now in the runtime venv), splitting lines into words from pixel gaps and handling glued OCR words;
  - writes `shot-<name>.{png,json}`.
  - `--selftest` covers it.
- **New `source` scene:** the real page in a styled window, with a slow push toward the phrase (auto-capped so the words stay in frame).
  - It has a highlighter sweep synced to the VO: a multiply marker on light pages, an underline marker on dark pages (chosen automatically).
  - It has an optional outlet/date chip.
  - `rf build` merges the shot JSON, syncs `highlightAt` from the VO, and falls back to a title card if the capture is missing.
- **Capture path:**
  1. Firecrawl `firecrawl_scrape` (`formats: ["screenshot"]`, `mobile: true`).
  2. Otherwise agent-browser on public pages at a phone viewport. It asks the owner first, unless the new config key `source_shots_browser` is true.
  3. Otherwise the logged text-card fallback.
  - Sites behind Cloudflare may also block headed capture; that is a valid logged fallback.

## 1.2.1 (2026-11-12): bug fixes from production #2 (walkthrough)

- **Walkthrough window fits the stage and the screenshot.** `rf build` reads the `src` image's aspect when none is set. The engine caps the content box to the stage height, after the title bar and caption, and shrinks the width rather than cropping. Before this, screenshots lost about 7.5% on each side and the bottom ~14% was hidden.
- **The cursor follows the zoom.** It is drawn in zoomed coordinates, so it stays on the element it clicked.
- **Speech-sync cues:** consecutive actions with the same `say` word share one cue (for example move + zoom). Zooms are pulled to at least 1 s before the cut so the ease finishes and holds. `build.py --selftest` covers both.
- **The first frame is never empty.** Walkthrough and image scenes skip their entrance fade when they start the reel (the hook frame).
- **`image.box` rides the Ken Burns layer,** so the highlight stays on its element while the image moves.
- **`rf sources og` decodes HTML entities** (`&amp;`) in og:image URLs; these used to fail with HTTP 400.
- **Docs:** `versus` marks the left column ✗ and the right ✓ (put "isn't" on the left); the walkthrough coordinates note.

## 1.2.0 (2026-11-12): public release, machine-adaptive setup

- `rf probe` (stdlib only, runs before setup): OS, GPU, RAM, disk, required tools with OS-specific install hints, ElevenLabs login/credits/API key, network reachability, runtime state → per-stage plan, blockers, asks (`~/.reel-factory/profile.json`).
- `rf setup` refuses to run with blockers, stores `ELEVENLABS_API_KEY` in the CLI keyring, and writes a first config tuned to the machine (free providers without ElevenLabs; smaller Whisper model on low-RAM CPUs); `whisper.model` is configurable.
- Skill stage 0 is probe-first and inspects every input it was given; `/reel-setup` is a one-time onboarding (services, brand, language, mode question).
- Mode availability respects the probe (no generated media without an ElevenLabs login).
- `rf kb where` explains how to evolve a remote-installed copy (clone + local marketplace).
- Themes `frost` (cool light) and `ink` (blue-black, condensed caps); guidance against the warm-cream + orange "AI look".
- Plugin icon; MIT license; public README with rendered mode demos.

## 1.1.0 (2026-11-12): creation modes + batch-02

**Corpus:** batch-02 (`Reels/Saved 2 - 30-69-days-ago`, grew 14 → 21 → 30 → 66 files during the run) → **17 new reels, 49 duplicates**. Total corpus 105 unique reels.

**Added**
- **10 creation modes** derived from both batches, by construction rather than subject: kinetic, presenter, story, newsroom, receipts, catalog, walkthrough, cinematic, silent, quicktake (`modes/`). Each with a playbook, defaults, QA overrides, requirements and fallbacks. Interactive mode selection with topic-specific descriptions, a recommendation, and **AI Select** (SKILL.md stage 3).
- **2 skeletons:** action-reaction, stack-roadmap (`formats.md`); all skeletons now carry ids.
- **Engine:** scenes `walkthrough` (cursor, typing, clicks, arrows, zoom), `headline` (outlet card with synced highlighter), `carousel` (DOF cards + i/N), `sheet` (cheat sheet + stamp); overlays `banner` (news lower-third), `slate` (film-slate HUD), `progress` (bar or ToC chips); `title.typewriter`; per-phrase `quote.highlightAt`; theme `noir`.
- **Scripts:** `rf ingest` (fingerprint dedup against the library + within the batch, fine-hash verification, analyse only new reels, batch report; re-runnable on a growing folder); `rf modes` (catalog + availability + history); `rf kb` (source location, version bump, plugin refresh); `voice --footage` (own-footage presenter); silent mode (no VO, beat-grid timing); speech sync for carousels, highlights and walkthrough actions; mode-aware `build` defaults and `qa` thresholds; production history (`~/.reel-factory/history.jsonl`).
- **Knowledge:** `techniques.md` (technique registry with implementation status), `corpus.md` (all 105 reels by mode), this changelog, the KB map and evolution protocol (`README.md`); batch-02 hooks, art-direction style locks and annotation grammar; mode-fidelity criteria in `qa-rubric.md`; `reel-analyst` agent for parallel batch analysis.

**Batch-02 findings that changed the system**
- No new mode was needed: the 17 new reels fit presenter (11), walkthrough (1), quicktake (4 incl. 2 floor), silent (1). They strengthened walkthrough (cursor/zoom grammar, yellow arrows) and quicktake (zoom-to-source).
- New techniques: T-zoom-to-source, T-arrow-annotation, T-toc-chips, T-typewriter-title, T-concept-icon-card, T-end-open-loop, T-killed-profession hook, T-context-bridge, T-friction-removal, T-price-receipt; anti-pattern A-title-mismatch.
- Dedup false positive (black tweet-frame layouts) fixed with fine-hash verification, calibrated on this batch.

## 1.0.0 (2026-11-11): initial release
Batch-01 (88 unique reels of 115 files): playbook, 9 skeletons, hooks, art direction, Remotion engine (18 scenes, 5 themes), multi-agent pipeline, first production.
