# reel-factory knowledge base

The plugin is never finished. Every batch of reference reels goes through `/reel-learn`, and whatever is genuinely new lands in one of the files below. Edit the **source** copy (`rf kb where`), never the installed cache, then `rf kb bump` so the next session loads it.

## Map: what lives where

| Domain | File | Holds |
|---|---|---|
| Creation modes | `modes/INDEX.md`, `modes/<id>.md`, `modes/modes.json` | the ways a reel is *constructed*; selection rubric; per-mode playbooks; machine defaults and QA overrides |
| Storytelling frameworks | `formats.md` | story skeletons (beat order) with ids |
| Hooks, retention, CTAs | `hooks.md` | hook formulas with counts, re-hooks, honesty beats, CTA patterns |
| Strategy and production rules | `playbook.md` | the corpus-derived rules every reel follows |
| Visual presentation and animation | `art-direction.md` | themes, captions, layouts, overlays, style locks, annotation grammar, sourcing priority |
| Audio, voice and sound design | `playbook.md` (§audio), `art-direction.md` (§audio), `tools.md` | levels, pace, bed, SFX, providers |
| Editing standards | `playbook.md`, `qa-rubric.md` | cadence, transitions, QA thresholds |
| Tools and technology | `tools.md` | commands, capability matrix, costs, fallbacks |
| Discrete techniques | `techniques.md` | every technique: id, evidence count, modes, **where implemented** (engine/script/guide/avoid) |
| Evidence | `corpus.md`, `corpus-notes.md`, `corpus-analysis.md` | every analysed reel by mode; per-reel notes; batch-01 synthesis |
| Research | `research.md` | trend scoring, research protocol, facts format |
| Change history | `CHANGELOG.md` | what each batch/version added, and why |
| Production lessons | `~/.reel-factory/learnings.md` (runtime, not in the plugin) | lessons from our own productions; read every run |

## Evolution protocol (what `/reel-learn` must decide for every new reel)

```
new reel ──► same construction as an existing mode? ──no──► does it recur (≥2 creators) or is it clearly
   │                                                         reproducible with a distinct pipeline?
   yes                                                         ├─ yes → NEW MODE (modes.json + playbook + INDEX + corpus)
   ▼                                                           └─ no  → record in corpus.md as an outlier; revisit next batch
new beat order? ──yes──► NEW SKELETON in formats.md (+ compatibility row in INDEX.md)
   │ no
   ▼
new technique? ──yes──► in techniques.md already? ──yes──► seen +1 (promote guide → engine at seen ≥ 2 if renderable)
   │ no                        │ no
   │                           └──► NEW TECHNIQUE row; implement now if cheap (engine prop/scene/overlay or script),
   │                                otherwise status "guide" with exact instructions
   ▼
better numbers? ──yes──► update thresholds (playbook/qa) only when the new evidence moves the median, not on one reel
   │ no
   ▼
nothing new → corpus.md row only ("confirms <mode>/<skeleton>")
```

Rules:
- **No duplicates.** Search `techniques.md`, `hooks.md` and the mode playbooks before writing; strengthen an entry instead of adding a twin.
- **A mode is a pipeline, not a look.** A new theme or caption style is never a mode; it goes into art-direction.md.
- **Evidence or it didn't happen.** Every addition cites the reel(s) (creator + topic, batch).
- **Implement what you document.** If a technique is renderable and seen with 2+ creators, add the engine support (scene/prop/overlay), typecheck (`npx tsc --noEmit` in `~/.reel-factory/engine` after `rf setup`), and render a still to verify it.
- **Version every change.** Append to `CHANGELOG.md`, then `rf kb bump minor` (new mode/scene) or `patch` (guidance only).
