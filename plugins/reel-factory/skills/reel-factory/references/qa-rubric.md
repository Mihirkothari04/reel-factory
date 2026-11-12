# QA rubric (script-critic and qa-reviewer)

## A. Storyboard review (before any paid asset is generated)

Score each 1–5. **Ship threshold: no score below 3, and an average of at least 4.** Give the fix for every score under 5.

| Criterion | 5 looks like |
|---|---|
| Hook (0–3 s) | Payoff or tension in the first sentence; specific (number, name, outcome); visual matches; no preamble |
| Promise and payoff | The reel delivers exactly what the hook promised, with the payoff visible on screen |
| Structure | Uses a known format skeleton correctly; escalation; re-hook at 40–60%; clean ending |
| Pacing | 4–12 words per scene; no scene over 6 s; pattern interrupt every 8–12 s; total in the target length |
| Clarity | A smart 16-year-old understands it on first watch; jargon translated; one analogy |
| Specificity | Concrete numbers, names, and examples in most sentences; nothing generic |
| Visual variety | No more than 2 consecutive scenes of the same type; demo/proof visuals, not just logos |
| On-screen text | Complements (doesn't duplicate) the VO; ≤7 words per headline; one emphasis per line |
| Credibility | Every claim maps to facts.md; honesty beat present; sources on screen where useful. Every on-screen web source is a real `source` screenshot; a `headline`/`quote` text card for a web source without a logged fallback reason caps this at 2 |
| CTA | Fits the format; shows the action; keyword is short and topical |
| Voice-readiness | Sentences are speakable, no tongue-twisters, numbers written how they should be said |
| **Mode fidelity** | The storyboard is genuinely built the way the chosen mode's playbook (`modes/<id>.md`) describes: its stage, devices, pacing and audio, not a kinetic reel with a different theme |

**Mode-specific checks** (score them inside "Mode fidelity"):
- `presenter`: board text shorter than kinetic; the face has its emphasis and CTA moments; footage or avatar actually available (else a kinetic fallback was declared).
- `story`: a fictional protagonist; every concept motivated by a felt failure; escalating stakes; a callback twist; one locked illustration style; progress stack wired.
- `newsroom`: banner set; every claim has an outlet on screen; allegation language for people; "crazy" escalation and "catch" balance both present.
- `receipts`: every quote is verbatim from facts.md; highlighted phrases are actually spoken; a verdict closes the reel.
- `catalog`: preview up front; counter/progress; restraint beat; a `sheet` end frame held ≥ 2.5 s; hook matches the items.
- `walkthrough`: every step happens on screen (cursor/type/click/arrow/zoom with `say` cues); before→after or result-first hook; recap of why.
- `cinematic`: every generated shot depicts a claim; slate set; 0.9–2.6 s cadence; topic not a sober one.
- `silent`: no `vo`, every scene has `dur`; ≤ 5 words per beat; the result in the first second; 12–25 s; music generated before build.
- `quicktake`: hook sticker for the whole reel; every zoom lands on a phrase being spoken; one non-obvious insight; 20–35 s.

Also flag: anything that breaks real-people or ethics rules (playbook.md), and scenes whose props don't match storyboard-schema.md.

## B. Render review (after `rf qa`)

Automated (from `out/qa/report.md`; thresholds per mode from `modes.json` → `qa`, e.g. story allows 7.5 s scenes and 135 s, silent skips the voice checks): loudness, VO start, pace, duration, scene lengths, black/frozen frames, clipping, WER (intelligibility), music presence. **Blocking failures must be fixed.**

Visual (read `out/qa/sheet.jpg`; for doubts render stills with `ffmpeg -ss T -i out/reel.mp4 -frames:v 1 x.png`):
1. **The hook frame at 0.0–0.5 s** is already informative and legible at phone size (not blank, not mid-animation garbage).
2. **Text fits**: no overflow, cut-off words, or overlap between captions and scene content, the hook sticker, or the handle.
3. **Legibility**: headline ≥ 80 px, supporting text ≥ 40 px, contrast fine on the theme.
4. **Safe zones**: nothing important in the bottom 380 px or right 120 px.
5. **Consistency**: one theme and accent; generated images match each other and the palette.
6. **Sync**: visuals change when the VO changes topic (spot-check 3 scene boundaries against words.json).
7. **Mode devices render**: banner/slate/progress/hook sticker visible where intended and not colliding with scene content; walkthrough cursor/arrow lands on the element the VO names.
8. **Source shots**:
   - The screenshot is the real page, not retyped text.
   - The crop is legible at phone size and banners are removed.
   - The highlight sits exactly on the spoken words and sweeps when they are said.
9. **Ending**: the CTA is readable for at least 1.5 s, and the comment mock or final frame isn't cut off.

Verdict: `SHIP`, `FIX` (with an exact list of edits to storyboard.json, each tied to a scene id and prop), or `REDO` (structural; go back to the storyboard). Allow at most 2 fix loops, then ship the best version and record the open issues.
