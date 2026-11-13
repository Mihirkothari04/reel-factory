# Knowledge-base changelog

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
