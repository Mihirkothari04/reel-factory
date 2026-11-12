# Reverse-engineering 88 Instagram Reels (AI and tech niche)

**Corpus:** 115 files in `Reels/`, 27 duplicates moved to `Reels/_duplicates/` (see `MANIFEST.json`), leaving **88 unique reels**. The 1080p file added at the repo root (`VID_20261103_233055_875.mp4`) is byte-identical to the duplicate of "The 8 Layers of AI Engineering"; it was re-analysed at full resolution.
**Method:** every reel went through `tools/extract_reel.py`: ffprobe; ffmpeg scene-cut detection (threshold 0.3); EBU R128 loudness; music-bed level measured in non-speech gaps; faster-whisper `small` word-timestamp transcript on the local GPU; and a 20-frame contact sheet weighted toward the first 3 s. I then read each reel's sheet and transcript and wrote a note on it (`PER_REEL_NOTES.md`, raw data in `analysis/reels/<id>/`).

---

## 1. Hard numbers (all 88 reels)

| Metric | Median | Middle 50% | Reading |
|---|---|---|---|
| Duration | **51 s** | 35–60 s | 72 of 88 fall between 20 and 65 s. Two run past 2 min, and both are story or tier-list formats. |
| Voice-over start | **0.0 s** | 0.0–0.0 s | **Every narrated reel speaks on frame 1.** None opens with silence or an intro. |
| Speaking rate | **204 wpm** | 177–232 wpm | Much faster than conversation (~150). Density drives rewatches. |
| Speech coverage | 87% | 81–92% | Almost no pauses. Silence is cut out. |
| Integrated loudness | **-14.1 LUFS** | -14.2 to -14.1 | Instagram's normalisation target. Everyone masters to -14. |
| Music bed (non-speech gaps) | **-25 dBFS** | -34 to -21 | **84%** have a bed. It sits about 10 dB under the voice (~-15). |
| Hard cut interval | 4.9 s | 2.7–13 s | Misleading on its own: the motion-graphics reels change content every **1–3 s** inside one "shot". |
| No-voice (music + text) reels | 3 of 88 | – | They work only when the visual payoff is spectacular. |

**Production standard derived:** 9:16 at 1080×1920 (the "Saved" copies are 540×960 re-encodes), 30 fps, -14 LUFS, the voice-over starts at 0 s, 190–235 wpm, a visual change at least every 2.5 s, word-synced captions, and a music bed 10–12 dB under the voice.

---

## 2. Content strategy

**Topic selection.** About 80% of the corpus is *"a thing that just shipped"*: a GitHub repo, a Claude/Codex skill or plugin, a model launch, or a company announcement. Topics cluster around whatever has momentum that week, and **several creators covered the same item within days**:
- Cloudflare security-audit skill: Creator 30 *and* Creator 37
- The AI-security-for-vibe-coders cluster: Strix, PentAGI, Agent Honeypot, Anthropic OSS Scanner, SkillSpector, DeepSec
- The anti-AI-slop design cluster: Hallmark, MotionSites, Anti-slop, Creator 33's "eyebrow labels", taste-skill

*Takeaway: when several creators cover the same item, that is the strongest trend signal. Topic discovery should look for convergence across sources, not single mentions.*

**Topic archetypes (by frequency):**
1. **Free or open-source tool spotlight.** About 40% of reels. "Free" appears in the hook of most of them.
2. **Curated list** ("N repos/skills/sites"), usually 3, 5, 7, 30, or 45 items.
3. **Brand news** ("Google/Anthropic/xAI/NVIDIA/China just…"), framed through the rivalry between big players.
4. **Workflow tutorial** (step 1…5, or tool A + tool B = result).
5. **Concept explainer or framework** ("only 5 problems", "8 layers", "scroll engineering").
6. **Opinion, ranking, or critique** (tier list by money, "smells like AI", model comparison verdict).
7. **Money and side-hustle angle** (earn in dollars, save $1,000/month).

**Audience targeting:** an identity callout in the first sentence ("vibe coders", "if you've got a Windows laptop", "video editors", "if you use Claude Code"), plus "for whom" lines near the end ("if you're a parent…", "for solo devs and product teams").

**Value framing:** free, open-source, runs locally, private, saves money ($ anchors), saves time, "without coding". Specific numbers are everywhere: stars (★40k), counts (700 designs, 18 skill areas), money ($1,000+/mo, two cents), speed (3 s vs 11.9 s), and percentages (-61% tokens).

---

## 3. The hook (0–3 s)

All 88 reels put the topic's payoff in the **first sentence**. Visual and verbal hooks land together.

**Verbal hook formulas found (with counts):**

| Formula | Example | ~n |
|---|---|---|
| Discovery: "Someone just built / open-sourced X that Y" | "Someone just built a trap for rogue AI agents" | 15 |
| Brand + recency: "X just released/dropped/launched…" | "Google's Android team just released free skills…" | 16 |
| Number list + promise | "7 GitHub repos worth installing for Claude" | 20 |
| Pain callout / you-problem | "You're probably never going to watch those reels you saved" | 7 |
| Contrarian imperative | "Never use /compact again", "Stop paying for these AI tools" | 6 |
| Threat / fear | "Your Claude skills might have malicious code hidden inside them" | 6 |
| Result-first proof | "…came back 0% AI generated" / "website like this" | 6 |
| Authority figure | "The man who taught the world machine learning just…" | 4 |
| Drama / irony / scandal | "…Fable 5 refused to run it, an open model did it better" | 4 |
| Challenge / quiz | "45 places to launch. I bet you know fewer than 10" | 2 |
| Coined term | "There's a new kind of engineering: scroll engineering" | 1 |
| Vivid metaphor | "peanut-sized OCR model", "like the Matrix", "Palantir alternative" | 5 |

**Visual hook patterns:** the payoff on screen at 0–1 s (the actual website, the 0% detector, a 3D render); a kinetic headline that builds word by word with one keyword emphasised (selection box, colour, or italic serif); a famous face or logo in the first 0.5 s (Elon, Sundar, Xi, the NVIDIA logo); a red "BREAKING NEWS" or tabloid banner; a censor bar over a famous face (withhold, then reveal); a meme or movie clip as a pattern interrupt; a table of contents previewing all N items (open loop).

**Persistent hook title:** about 25% keep a sticker-style title on screen for the first section or the whole reel (e.g. "😱 Don't Use Claude Without These 2 Things"), so viewers who arrive late or watch muted still get the topic.

---

## 4. Storytelling structures (9 reusable skeletons)

1. **Tool spotlight** (most common): hook → name + credibility (brand, stars, "built by…") → mechanism in 2–4 visualised steps → **re-hook** ("but here's the smart part / the trick / this next one is huge") → proof or stat → honest caveat → CTA.
2. **Listicle N**: hook with N → table-of-contents preview → items with an *i/N* counter, each with a name, a one-line benefit, and a demo visual → restraint advice ("don't install all 30, pick one row") → CTA with a withheld bonus ("I'll DM all 20, including the ones for sound…").
3. **Step tutorial**: before→after hook → "Step 1…5" spoken signposts → recap of *why* it works → CTA.
4. **News explainer** (a big-tech CEO, Grok Bot): "Breaking:" hook → chronology → "here's where it gets crazy" escalation → "but here's the catch" balance → so-what stakes. Often ends without a CTA.
5. **Claim → test → verdict** (Desert Ant Labs): claim → "does it hold up?" → third-party test → fine print → honest verdict pill. Builds trust.
6. **Problem-ladder story** (8 Layers of AI Engineering, the best in the corpus): a named protagonist ("Nova") fails → fix (concept 1) → new failure → fix (concept 2) … → callback twist at the end. Teaches N concepts, each motivated by a failure the viewer feels.
7. **Framework reduction**: "There are only N problems/layers" → numbered buckets → summary grid (screenshot-worthy) → "Which first? Comment a number" (seeds the next video).
8. **Ranking / tier list**: scores per tier, best revealed last. Built to provoke debate.
9. **Comparison + personal verdict**: X vs competitors → reasons → caveat → "my pick" → question CTA ("which would you use?").

**Re-hook phrases used mid-reel** (each placed about 40–60% in): "But here's the smart part", "Now here's where it gets crazy", "this next one is huge", "But that's not even the most interesting part", "OK but this is the fun part", "And here's the trick", "But here's the catch".

---

## 5. Visual presentation

**Layout families:**

| Family | Share | Description |
|---|---|---|
| Split presenter | ~40% | Top 40–60% motion graphics or screen, bottom presenter. The face reappears full-frame for emphasis and the CTA (push-in close-up). |
| Faceless motion graphics | ~15% | Designed scenes only (Creator 30, Creator 63, Creator 32, 8 Layers, 45 Places). **Fully automatable, and among the most polished.** |
| Full-frame talking head + floating overlays | ~15% | Cards and stickers over the face (Creator 55, Creator 26). |
| UGC / handheld | ~12% | Phone filming the laptop, real hands, room tone. Authenticity over polish. |
| Automated README scroll + TTS | ~7% | Trending-OSS and Creator 44 channels. **The quality floor to beat.** |
| Repost / tweet frame | ~3% | Horizontal video inside a black frame with a headline. |
| AI avatar presenter | ~1–2 | Creator 58 (seated avatar plus screen recordings). Shows the avatar only has to be good enough. |

**What fills the visual track (ranked by frequency):**
1. **Rebuilt product UI**: dark or light app windows, terminals with typing, chat mocks, dashboards. These are *redrawn* to be crisp at phone size rather than raw screenshots. The top creators do this.
2. GitHub repo cards with **odometer star counters** (0 → 40,000★).
3. Website or README screenshots in a browser frame, with **highlighted key sentences** (marker, black-highlight, or red circle and arrow annotations).
4. Big numerals and stat cards (count-ups, before/after bars, percentages).
5. Diagrams: hub-and-spoke, pipelines, layer pyramids, branching trees, orbit diagrams.
6. Logos and app-icon grids.
7. Kinetic typography as the main visual.
8. Meme or movie reaction clips (pattern interrupt).
9. Stock or cinematic B-roll, AI-generated sample clips, 3D renders.
10. Flat illustration and mascots (pixel-art Claude-crab sprites appear across five or more unrelated creators, which marks them as the niche's visual vernacular).

**Typography system (near-universal):** a sans for the body, plus an **italic serif for the emphasised word** (Creator 37, Creator 30, Creator 12, Creator 22, Creator 18), sometimes inside a **Figma-style selection box** (blue fill with corner handles). Condensed grotesk caps for headlines in more energetic reels. Monospace for technical labels and HUD metadata.

**Colour:** one dominant accent per brand (blue, coral, teal, red, orange, amber, mint) on a neutral (off-white/cream, near-black, warm grey, lavender). Purple-blue AI gradients are almost absent from the top tier, and the anti-AI-slop reels openly mock them.

**Composition rules:** the safe zone keeps the top ~8% and bottom ~20% free of key content (Instagram UI). Captions sit at the "seam" between graphics and face, or in the lower third, never under the like/comment rail. Corner HUD metadata ("// 05 — fake", "SCENE 02/09", "TC 00:00:07") adds production feel.

---

## 6. Audio and voice

- **Voice:** fast, confident, conversational, second person ("you"); first person for credibility ("I've built a ton of mods", "I tried this"). Hinglish and Hindi creators use "bhai" intimacy. The automated channels use flat TTS, which noticeably lowers perceived quality.
- **Delivery:** pauses cut, breaths removed, ~200 wpm, energy front-loaded.
- **Music:** a bed under the voice in 84%. Lo-fi, tech-house, or minimal electronic, never competing with the voice. Instrumental only, no vocals. Builds sit under the hook. News reels use tense pulses.
- **SFX:** subtle and functional: a whoosh on transitions, a pop or click on card appearances, typing ticks on terminals, a tick on counters, a riser into the re-hook, a ding on the CTA. Two corpus reels are about *adding* pro SFX to AI edits, so this layer is a known differentiator.
- **Music-only reels** (3): the text carries everything and the visual payoff is spectacular.

---

## 7. Editing techniques

- **Captions:** word- or chunk-synced (1–4 words), bold sans, one keyword emphasised by colour, pill, highlight box, or font swap. Placed at the seam or lower-middle. Some creators replace subtitles with kinetic headline text.
- **Transitions:** hard cuts dominate. Motion-graphics reels use push/slide with motion blur, whip pans, scale-in pops with overshoot (spring easing), blur-to-sharp focus pulls, and card carousels with depth blur.
- **Camera moves on static content:** slow push-ins (Ken Burns) on screenshots, scroll-reveals of READMEs (good when it zooms to the highlighted line, bad when it blind-scrolls the whole page), and a push-in on the face for the CTA.
- **Emphasis effects:** highlight sweeps on text, red circles and arrows, stamps ("KILLED", "HUGE", "AGAIN"), count-ups, strike-throughs (paid prices crossed out).
- **Progress devices:** i/N counters, progress dots, cumulative checklists or stack diagrams, a "you know __/45" score box, chapter labels.

---

## 8. Information delivery

- **One claim → one visual.** Each sentence gets its own composition, roughly 2–3 s each.
- **Plain-language translation of jargon:** "keeps the work separate so nothing breaks" instead of "worktrees"; "Who spoke when? Diarization."
- **Analogy and metaphor for mechanisms:** elephant vs goldfish, short-term vs long-term memory, "like the Matrix", "draft model guesses, main model checks".
- **Concrete scenarios over specs:** "drop in a 40-page contract", "ask it to triage your Slack and it sends the replies".
- **"What this means for you" bridge** after the technical part.
- **Honesty beats:** caveats ("still early, a few bugs"), who it's *not* for ("just chatting? skip it"), fine print. These raise credibility and appear in the best reels.
- **Primary-source proof on screen:** the README line, the tweet, the blog, the NYT headline, highlighted as it's read.

---

## 9. Psychological principles in play

Curiosity gap (withheld names, censor bars, "does it hold up?"); open loops (ToC preview, withheld DM bonus, "which first?"); loss aversion (paid → free, $ crossed out); authority and social proof (stars, Google engineers, Karpathy, 500k views); FOMO and in-groups ("most vibe coders don't know", "blowing up right now"); fear then relief (security threats → free fix); identity flattery ("developers are savage"); Zeigarnik / completion (empty 1–10 checklist filling in, counters); reciprocity (free value → comment for more); pattern interrupts every 8–12 s (memes, stamps, colour switches, full-screen type); rewatch density (204 wpm, 1.5 s visual changes); save triggers ("screenshot this", summary grids); share triggers ("send to a friend who's about to launch").

**CTA distribution:** comment-keyword DM ~55% (keyword often equal to the topic word: "AUDIT", "SOUND", "T3"), follow/save/share ~20%, pinned-comment link ~12%, question CTA ~5%, none (story/news) ~8%. The best CTAs **show the action**: a mocked comment box with the keyword being typed, then "Sent! Check your DMs".

---

## 10. Creator systems (consistency is a strategy)

The strongest accounts run a **fixed template** where only the content changes. Creator 37 appears 7 times with the same gradient, window card, blue italic keyword, and gold 3D CTA word. Creator 05 uses the same cinematic set, tweet highlights, and mint asterisk background. Creator 22 repeats its "China just open-sourced…" hook several times. Repetition builds recognition; every reel is instantly attributable.

*Takeaway for the skill:* keep a **channel brand kit** (fonts, accent, caption style, CTA treatment, mascot) constant across reels, and vary the **format and art direction per topic** within that kit.

---

## 11. Quality tiers (what separates top from bottom)

| | Bottom tier (automated README-scroll) | Top tier |
|---|---|---|
| Visual change | One scrolling screenshot | New composition every 1.5–3 s |
| Text legibility | Tiny README text | Rebuilt, large, highlighted |
| Voice | Flat TTS reading README-speak | Fast, opinionated, plain language |
| Audio | No music, no SFX | Bed at -25 dB plus functional SFX |
| Structure | What / features / install / CTA | Hook, re-hook, proof, caveat, verdict |
| Demo | None | Real or recreated demo of the outcome |

**The skill must automate the pipeline while producing top-tier output.** Faceless motion-graphics creators (Creator 30, Creator 63, Creator 32, the 8 Layers story) show that is achievable without a human on camera.

---

## 12. What can and cannot be replicated with our stack

| Technique | Replication path |
|---|---|
| Kinetic type, rebuilt UI, counters, diagrams, carousels, captions, transitions | **Remotion** (React → MP4), data-driven scene library. Full fidelity. |
| Illustrated story explainers | Remotion SVG scenes + generated illustrations (ElevenLabs Flows image models) with a fixed style prompt |
| Voice-over | ElevenLabs TTS with timestamps (primary), edge-tts (free fallback with word boundaries), faster-whisper alignment |
| Music bed | ElevenLabs Music (per reel, short); Openverse CC search as the free fallback |
| SFX | Procedurally synthesised local kit (whoosh, pop, click, tick, riser, ding), plus optional ElevenLabs SFX |
| AI presenter / avatar | ElevenLabs Flows **Creatify Aurora** (image + audio → talking head) or Veo 3.1. Optional, credit-heavy, used only when the format calls for a presenter. |
| Cinematic B-roll / hero shot | ElevenLabs Flows video (Seedance 2 / Veo 3.1 fast), 4–8 s clips, sparingly |
| Website and repo visuals | GitHub REST API data → rebuilt repo cards (better than screenshots); agent-browser screenshots or recordings of public pages when needed |
| A real human on camera | Not replicable; replaced by avatar, faceless motion graphics, or voice with mascot |
| Trend detection | GitHub search API, Hacker News Algolia, Reddit JSON, Hugging Face trending, arXiv, plus web search, with cross-source convergence scoring |
