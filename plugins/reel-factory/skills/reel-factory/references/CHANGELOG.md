# Knowledge-base changelog

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
