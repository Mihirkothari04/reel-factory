---
description: Analyse a new batch of reference reels and evolve reel-factory — dedup, per-reel analysis, compare with known modes/skeletons/techniques, add only what is genuinely new (new mode, variation, or technique), implement it, version it
argument-hint: "<folder or video files> [--batch NAME]"
---

Run the **reel-factory R&D loop** on: `$ARGUMENTS`

`RF` = `python "${CLAUDE_PLUGIN_ROOT}/scripts/rf.py"`. Analysis uses free local tools only (ffmpeg, local Whisper); never paid APIs.

## 1. Locate the knowledge base
`RF kb where` → `KB` = the printed **source** dir (`KB/skills/reel-factory/references/` is the knowledge base). Read `references/README.md` (map + evolution protocol), `modes/INDEX.md`, `modes/modes.json`, `formats.md`, `techniques.md`, `corpus.md`. All edits go to `KB`, never to the installed cache.

## 2. Ingest (dedup before spending any time)
`RF ingest <paths…> --batch <NAME or batch-NN> --source-root <cwd>` (run it in the background for big folders). It fingerprints every file, drops duplicates against the library and within the batch (coarse hash, then fine-hash verification), analyses only the new reels into `~/.reel-factory/library/`, and writes `~/.reel-factory/library/_batches/<NAME>.json`. If the user adds files to the folder mid-run, re-run the same command: it only processes unseen files. Spot-check any duplicate whose score is < 1.0 and whose files look unrelated (shared layouts can fool hashes): view a frame strip of both.

## 3. Analyse every new reel
- ≤ 6 new reels: do it yourself.
- More: split the new slugs into chunks of ~6 and launch **`reel-factory:reel-analyst` agents in parallel** (one message, several Agent calls), each with its slugs, the batch name, `KB`, and an output path `<cwd>/analysis/notes/<batch>-<n>.md` (or `~/.reel-factory/library/_batches/<batch>-<n>.md` outside a project). Review their tables; open the sheets of any reel flagged as a new mode or skeleton yourself before accepting it.

## 4. Decide (per the evolution protocol in `references/README.md`)
For each finding: **new mode** (a distinct construction pipeline, recurring or clearly reproducible) · **new skeleton** · **new technique** · **strengthens a known technique** (seen +1) · **better numbers** · **nothing new**. Never add a duplicate; a new look or theme is never a mode.

## 5. Implement
- Knowledge: update `corpus.md` (rows + counts), append notes to `corpus-notes.md`, `techniques.md` (new rows / seen counts / status), `hooks.md`, `formats.md`, mode playbooks, `art-direction.md`, `qa-rubric.md` as needed.
- New mode: add it to `modes/modes.json` (all fields), write `modes/<id>.md` (identity, construction, beat template, pacing/audio, workflow, pitfalls, evidence), add it to `modes/INDEX.md` (table, compatibility, fallbacks).
- Renderable technique seen with 2+ creators: add engine support in `KB/engine/src` (new scene in `scenes/modes.tsx` + REGISTRY in `Reel.tsx` + `types.ts`, or a prop/overlay), document it in `storyboard-schema.md`, then verify: `RF setup` (syncs the engine) → `npx tsc --noEmit` in `~/.reel-factory/engine` → render a still with `npx remotion still` from a test props file and **look at it**.
- Script behaviour (timing, sync, QA): edit `KB/scripts/*`, keep each script's `--selftest` passing.

## 6. Version and report
Append a dated entry to `references/CHANGELOG.md` (batch, counts, what was added and why), then `RF kb bump minor` (new mode/scene/script) or `RF kb bump patch` (guidance only). Report: files → new vs duplicates, per-reel mode/skeleton table, what changed in the system (modes, skeletons, techniques, engine), anything recorded but not yet implemented, and the new version. Production lessons from our own reels stay in `~/.reel-factory/learnings.md`.
