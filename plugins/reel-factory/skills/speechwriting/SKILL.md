---
name: speechwriting
description: "Write reel narration that sounds like a real creator talking — storyline first, then flowing spoken paragraphs with connectors, varied sentence lengths, natural pause points and emphasis, then delivery markup for TTS and visual cue mapping. Use for every reel-factory script (the reel-factory skill calls it at the script stage), when rewriting a choppy or robotic voice-over, or when a script-critic/voice report flags flow, pacing or pause problems."
version: 2.0.0
---

# Speechwriting for reels

A reel's narration is **one continuous spoken performance**, not a list of captions. Write the speech first, then hang the visuals on it. Never write one line per scene.

The evidence comes from word-timestamp transcripts of the reference corpus (89 English reels), measured against our early productions. Our early scripts averaged 7–9 words per sentence with no connectors, and that is exactly why they sounded robotic.

| measure | corpus (median, IQR) |
|---|---|
| words per sentence | **15** (12–18) |
| sentences of 16+ words | **48 %** |
| sentences of 6 words or fewer | 11 % |
| pause at a sentence end | 0.24 s (0.16–0.30) |
| pause at a comma | 0.22 s |
| gap between words inside a phrase | 0 s (words run together) |
| speaking rate (pauses included) | 215 wpm (195–237) |
| speaking rate (pauses excluded) | 238 wpm |
| visual cuts per sentence | 1.08 (cuts land mid-sentence) |
| sentence openers | "So" 9 %, "And" 9 %, "You" 5 %, "This" 5 %, "Now" 4 %, "It's" 4 %, "Then" 3 %, "But" 3 %, "If" 3 % |

## The process (do the steps in order)

### 1. Storyline (beat sheet) before any sentence
Write 5–8 beats in `brief.md`. Each beat is one line saying what the viewer must *feel* or *know* after it:
- hook stake;
- name and define;
- how it works;
- turn or re-hook;
- proof;
- catch;
- payoff for the viewer;
- action.

Check the arc: does every beat raise or answer a question the previous beat opened? If two beats say the same thing, merge them.

### 2. Speak the paragraphs
One paragraph per beat, usually 1–3 sentences. Write the way the creator would *say* it to a friend who is a bit behind on tech.

- **Hook paragraph.**
  - The first sentence is **complete and carries the stake**, and is often long. Example: "Someone just built a free AI video studio that runs entirely on your laptop, and you don't need a three-thousand-dollar GPU to use it."
  - Never open with a fragment.
  - The second sentence names and defines it. Example: "This is WAN2GP, an open-source video generator built for people who can't afford cloud subscriptions."
- **Connect every sentence to the one before it.** Use the connector system:
  - adding: "And…", "Plus…", "On top of that…";
  - consequence: "So…", "Which means…", "That's why…";
  - turn: "But…", "But here's the catch.", "Here's the thing though…";
  - sequence: "First…", "Then…", "Now…", "Next…", "And finally…";
  - signposting: "Here's how it works.", "OK, but this is the fun part.";
  - viewer bridge: "So if you've ever ___, you don't have to anymore.", "If you run a ___, this matters because…".

  Use them roughly every second sentence and vary them; don't start three sentences in a row with the same word.
- **Rhythm.** Mix long payload sentences (16–24 words) with short punches (3–7 words) placed **after** a long one. Example: "…it generates the whole clip on your own machine. No cloud. No subscription." Target a median of 13–17 words with a third or more at 16+. Avoid a run of more than three short sentences, which reads as robotic, and avoid any sentence over about 28 words, which runs out of breath.
- **Lists live inside sentences** as comma series ("text to video, image to video, restoration, music and sound effects"), not one item per line, unless the format is a listicle with "Number one…" signposts.
- **Spoken texture.** Use contractions always (it's, you're, don't). Allow one or two natural fillers per reel ("basically", "literally", "honestly", "OK"). Use second person. Use concrete nouns and numbers written the way they're said ("three thousand dollars", "one point two billion").
- **Re-hook at 40–60 %.** A short signpost sentence ("But here's what actually makes this insane.") followed immediately by the payload.
- **Honesty beat.** One sentence, plainly said ("It's still in beta, so expect a few rough edges.").
- **CTA as speech.** Example: "Comment SETUP and I'll send you the whole guide." Not a fragment.

### 3. Mark pauses and emphasis with punctuation (the voice reads punctuation)
- A period gives a sentence pause of about 0.25 s, and a comma a short breath. Put commas where a speaker breathes, not where grammar demands them.
- An ellipsis (`...`) gives a held beat before a reveal. Use at most two per reel.
- An em dash (`—`) is a quick aside or turn.
- New paragraph = new beat. The voice pipeline adds about 0.4 s between paragraphs.
- Never break a thought across paragraphs. The pipeline never pauses mid-paragraph unless punctuation says so.

### 4. Delivery markup (`tts` field, optional, sparing)
The `tts` copy of a paragraph has the **same words**, plus:
- **audio tags** before the words they colour: `[excited]`, `[curious]`, `[serious]`, `[confident]`, `[surprised]`, `[sarcastic]`, `[laughs]`, `[whispers]`, `[short pause]`. At most one per paragraph, and none on most paragraphs;
- **CAPS** on the one word per sentence a speaker would hit ("It's FREE");
- **ellipses** for a held beat.

Never add or remove words: captions are built from `text`, and the voice pipeline aligns the two.

### 5. Visual cues (after the speech is final)
Each scene has a `cue`, the exact phrase of the narration where its visual starts (2–5 words). Cuts may and should land **inside** sentences, on the noun or number being said (the corpus has 1.08 cuts per sentence). The first scene needs no cue. Each cue must appear in order in the narration.

## Format profiles (the narration methodology changes with the reel's structure)

| structure | voice | sentences | connectors and devices | pace |
|---|---|---|---|---|
| kinetic explainer | confident friend explaining | 13–17 median, many long | "Here's how it works.", "So…", one analogy | 205–235 wpm |
| presenter (avatar or own face) | conversational, first person, opinions ("I tested…", "honestly") | longest (~19), loose, asides | "And guys…", "So all fun aside…", direct address | 225–250 wpm, short pauses |
| newsroom / trending news | urgent, crisp, factual, attributed ("according to…") | 12–16, tight | "Just now…", "Now here's where it gets crazy.", "But here's the catch." | 210–240 wpm |
| receipts | skeptical journalist, reads the source aloud | quoted lines plus a verdict | "Their own fine print says…", "Does that hold up?" | 190–220 wpm |
| walkthrough / tutorial | instructor, imperative, calm | 14–17, "Step one…" signposts | "First… then… now…", recap of why | 215–235 wpm |
| catalog / listicle | energetic host | short item sentences plus a long reason each | "Number three is the one I use daily." | 220–245 wpm |
| story (problem ladder) | narrator with a character | varied, scene-setting, past tense | "So she added…", callback twist | 175–210 wpm, longer pauses |
| cinematic hype | big, declarative | short punches over music plus 2–3 long ones | ellipses, a single CAPS word | 190–220 wpm |
| quick take | fast reaction | 8–12, few sentences | "Here's what matters." | 170–220 wpm |

When structures are combined (for example a presenter hook into a walkthrough body), switch the profile at the paragraph boundary where the structure changes, and say a bridge sentence ("Let me show you exactly how.").

## Self-check before handing over
Read the whole narration aloud in your head at speed:
- Does each sentence follow from the last?
- Is there a word that would make a speaker stumble?
- Is any thought cut in two?
- Run the numbers: the sentence-length median is 13–17, there are 0–3 sentences of 6 words or fewer, and the connectors vary.
- Count the words: about 3.4 words per second of target length (55 s ≈ 185 words).

Then save `narration` in `storyboard.json` and a readable `script.md`.
