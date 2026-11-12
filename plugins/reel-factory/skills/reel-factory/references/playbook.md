# Reel playbook: production rules distilled from 88 top AI/tech reels

Full evidence: `corpus-analysis.md` (synthesis) and `corpus-notes.md` (one section per reel). Numbers are corpus medians.

## The non-negotiables

1. **Payoff in the first sentence, spoken at 0.0 s.** Every narrated reel in the corpus starts talking on frame 1. No greeting, no "hey guys", no "in this video", no logo sting.
2. **The visual hook lands with the verbal hook.** At 0–1 s the screen shows the thing itself (the result, the number, the famous logo, the headline building word by word). Never show an empty or slow intro.
3. **One claim, one visual.** A new composition every **1.5–3 s**. Nothing static for more than about 4 s.
4. **Fast, dense, plain voice-over.** About 190–230 wpm, no filler, sentences under 15 words, second person ("you"), concrete nouns and numbers.
5. **Specific beats generic.** Use a number, name, price, star count, time saved, or percentage in nearly every sentence where facts allow. "45,000 stars", "two cents", "61% fewer tokens".
6. **A re-hook at 40–60%.** "But here's the smart part / this next one is huge / here's where it gets crazy / but here's the catch."
7. **An honesty beat.** One caveat, limitation, or "who it's not for". It raises trust, and the best reels in the corpus all have one.
8. **A CTA that shows the action.** Comment-keyword with a mocked comment box (about 55% of the corpus), save/share ("send this to a friend who…"), or a question ("which one would you use?"). Story and news formats may end on the verdict instead.
9. **Captions on, word-synced, 1–3 words, one accent keyword per chunk.** The reel must work on mute.
10. **Audio standard:** -14 LUFS integrated, instrumental bed about 10–12 dB under the voice and ducked under speech, functional SFX (whoosh on cuts, pop on cards, typing on terminals, ding on CTA), nothing louder than the voice.

## Length

- Default **35–55 s** (corpus median 51 s, middle half 35–60 s).
- Single-tool spotlight: 30–45 s. Listicles: 45–60 s (about 7–9 s per item). Story or problem-ladder explainers may run 60–120 s *only* if every beat escalates.
- Ultra-short lists (12–20 s, names only) suit loopable "save this" content.

## Retention mechanics (use at least 4 per reel)

- **Open loop in the hook**: preview N items, withhold a name ("the man who taught the world ML…"), or ask a question you answer later.
- **Progress devices**: `i / N` labels, item counters, a checklist that fills, a cumulative stack or flow.
- **Pattern interrupt every 8–12 s**: `punch`, `stat`, stamp, theme-consistent colour flip, a big number.
- **Escalation**: each item or beat is bigger than the last; save the strongest for second-to-last (last is the CTA).
- **Re-hook phrase** at mid-point (see hooks.md).
- **Payoff visual**: show the outcome (a rebuilt UI, a terminal result, before/after bars), not just the logo.
- **Rewatch density**: fast VO plus a fast visual cadence makes people replay.
- **Save trigger**: a summary list or cheat-sheet frame near the end ("screenshot this").

## Information design

- Translate jargon on first use: "Who spoke when? That's called *diarization*."
- Explain mechanisms with **one analogy** (elephant vs goldfish, short- vs long-term memory, "like the Matrix").
- Follow the technical part with a **"what this means for you"** sentence.
- Use **concrete scenarios** over spec lists: "drop in a 40-page contract → clean structured text."
- **Primary source on screen**: the README line, tweet, or blog sentence, highlighted as it's read (`quote`, `repo.highlight`).
- **Rebuild UI instead of screenshotting dense pages.** The top creators redraw product UI so it's legible at phone size. Use `terminal`, `chat`, `repo`, and `list` scenes with the real strings.

## Psychology toolkit (choose deliberately, don't stack them all)

Curiosity gap · loss aversion (paid → free, "$1,000+/mo" struck through) · authority and social proof (stars, big-company engineers, named experts) · FOMO/in-group ("most vibe coders don't know these") · fear → relief (threat, then free fix) · identity callout ("if you use Claude Code…") · completion (Zeigarnik: empty list fills) · reciprocity (free value, then the comment CTA) · contrarian imperative ("Never use /compact again").

## Credibility and ethics (hard rules)

- Every factual claim (numbers, dates, who built what, benchmarks) must trace to a source in `research/facts.md`. The fact-checker blocks unsourced claims.
- Attribute claims you can't verify ("the team says…", "reportedly"). Never invent stats, testimonials, comments, or star counts.
- **Real people:** never generate their likeness, never put words in their mouth, and never stage them endorsing anything. Show headlines, documents, logos, or neutral imagery. For news about real people, use "reports say", cite the outlet, and include the "not proven" balance beat.
- Don't promote malware, credential tools, piracy, or ways to evade safety or provenance systems.
- When AI-generated imagery or voice is used, note it in the caption (Instagram's "AI info" label is recommended).

## Topic fit

Strong: a free or open-source tool shipped in the last 14 days with a visible outcome; a big-brand launch with a "what it means for you" angle; a curated list solving one job; a counter-intuitive framework; a security threat with a free fix; a money or time saver with numbers.
Weak: abstract opinions with no visual, topics already saturated for 3+ weeks without a new angle, anything you can't show.

## Series and brand

Keep one channel kit fixed across reels: brand accent, caption style, CTA treatment, handle (config `brand`). Vary **format and art direction per topic** inside it. Series devices ("Day 5 of…", "Part 2") build return viewers.
