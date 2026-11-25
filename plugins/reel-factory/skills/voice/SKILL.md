---
name: voice
description: "Generate, tune and quality-check reel voice-overs with ElevenLabs (v4 default) — paragraph segments with previous/next-text stitching, delivery markup, pronunciation lexicon, boundary-aware pause shaping toward corpus targets, and a blocking listening report. Use for every reel-factory voice-over (the reel-factory skill calls it at the voice stage), when a take sounds robotic, rushed, choppy or mispronounced, or when choosing a voice/model/settings."
version: 2.0.0
---

# Voice generation for reels

Tool: `python "${CLAUDE_PLUGIN_ROOT}/scripts/rf.py" voice <prod> [...]`. Input is `storyboard.json` → `narration` (written with the speechwriting skill).

**Gate (owner hard rule, 2026-11-25):** `rf voice` refuses to run until the owner has approved the final script and `rf approve P` has recorded it. Editing the narration or soundbites afterwards voids the approval, so show the owner the change and get approval again.

## What the pipeline does (and why)
1. **Segments.** Whole paragraphs are grouped into segments of about 900 characters or less, and a thought is never split. Generating sentence by sentence produces pitch and energy jumps at every join. Generating one 60 s block risks drift on long takes. Paragraph segments with stitching are the balance.
2. **Stitching.** Each request carries `previous_text` and `next_text` (about 600 characters around it), so intonation continues across joins (ElevenLabs request stitching).
3. **Model and settings.**
   - The default is `eleven_v4` with `stability` 0.5 and `similarity_boost` 0.75. v4 has no speed or style slider: pace and emotion come from the **text** (punctuation, ellipses, CAPS, audio tags).
   - `eleven_v3` remains available (`voice.model_id`) and accepts `style`.
   - Lower stability (0.35–0.45) gives more expressive but less predictable delivery; higher (0.6–0.7) is steadier for long explainers.
4. **Delivery markup** comes from `narration[].tts`: audio tags such as `[excited]`, `[curious]`, `[serious]` or `[short pause]`, CAPS emphasis, and ellipses. Captions always use the clean `text`.
5. **Pronunciation.** `voice.lexicon` (in the config) and `storyboard.lexicon` map a word to a respelling, or on v4 to IPA in slashes. Example: `{"Persona": "PER-suh-nuh", "GGUF": "gee-guff"}`. Add every brand or product name the report lists as misheard.
6. **Alignment.** ElevenLabs character timestamps are mapped onto the display words; tags are skipped and tokens matched. Edge-tts, the free fallback, is aligned with local Whisper.
7. **Joins.** Each segment is trimmed of edge silence and segments are joined with a paragraph pause (`voice.paragraph_pause`, 0.40 s).
8. **Pause shaping by boundary.** This replaces the old blanket cut, which crushed every silence to 0.12 s. Every inter-word gap is set to its boundary's corpus range:

   | boundary | target |
   |---|---|
   | sentence or ellipsis | 0.18–0.32 s |
   | comma or dash | 0.10–0.22 s |
   | paragraph | 0.34–0.50 s |
   | mid-phrase | ≤ 0.08 s |

   Long mid-phrase gaps (model glitches) are removed if the audio there is quiet. Sentence and paragraph ends with no air get silence inserted. Words are never cut.
9. **Tempo.** There is no blanket speed-up. A tempo nudge of at most ×1.05 (`voice.max_tempo`) is applied only if the take exceeds `meta.max_seconds`. If a script is too long, cut words with the speechwriter instead.
10. **Listening report and gate.** The report goes to `out/voice-report.md` and `.json`. It measures:
    - wpm against the mode range;
    - articulation rate;
    - sentence length;
    - sentence, comma and paragraph pause medians;
    - mid-phrase gap p90;
    - loudness jumps at segment joins;
    - WER of local Whisper against the script, with a "misheard" list.

    The gate is **FAIL** on: sentence pauses outside 0.14–0.40 s, mid-gap p90 over 0.15 s, wpm outside the mode range, a join jump over 6 dB, or WER over 8 %. `rf qa` blocks on a failing voice report.

## Fix loop (cheap first)
- **Pause, flow or glitch issue:** `rf voice P --retime` re-shapes the saved raw take. No credits.
- **One paragraph sounds wrong** (mispronounced, wrong emotion, a glitch): fix its `tts` markup or the lexicon, then run `rf voice P --regen p4` to regenerate only that paragraph. The others are reused.
- **The whole take is flat or rushed:** fix the *writing* (speechwriting skill), not the settings. Then regenerate.
- **Never loop paid generation blindly.** Change one thing, regenerate once, read the report.

## Choosing a voice
Use one voice per channel for consistency (config `voice.voice_id`). Pick it from the ElevenLabs library for a natural, conversational, mid-pitch creator voice whose samples contain fast explanatory speech. Pace and tag response follow the voice's training audio. Re-test the voice whenever the model changes.

## Costs
ElevenLabs bills the characters of `text`, and delivery tags count. Whether stitching context is billed is not documented, so check the `x-character-count` response header or the credit balance before and after. A 55 s reel is about 1,100 characters per take, and a single-paragraph regeneration is about 150–250. State the cost before batch jobs.
