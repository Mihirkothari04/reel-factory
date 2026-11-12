# Hook, re-hook and CTA library

Always draft **5 hooks** from different formulas, score each 1–5 on *(specific, surprising, relevant to the target viewer, visualisable in 1 s, true)*, and use the winner. Keep the runner-up as the on-screen `hookTitle` if it adds information.

## Hook formulas (frequency in corpus)

| # | Formula | Template | Corpus example |
|---|---|---|---|
| 1 | Discovery (15) | "Someone just built/open-sourced **[thing]** that **[outcome]**" | "Someone just built a trap for rogue AI agents" |
| 2 | Brand + recency (16) | "**[Brand]** just **[released/dropped]** **[thing]** that **[outcome]**" | "Google's own Android team just released free skills that teach AI agents to build Android apps the right way" |
| 3 | Number + promise (20) | "**[N]** **[things]** that **[job]**" / "…worth installing for X" | "7 GitHub repos worth installing for Claude — each makes it better at a real job" |
| 4 | Pain callout (7) | "You're probably **[painful habit]**" / "Your **[thing]** is **[bad]** and you don't know it" | "Your vibe-coded app is slow" |
| 5 | Contrarian imperative (6) | "Never **[common habit]** again. Use **[X]** instead." / "Stop paying for…" | "Never use /compact again" |
| 6 | Threat (6) | "Your **[thing]** might **[danger]**" | "Your Claude skills might have malicious code hidden inside them" |
| 7 | Result-first (6) | "I tried **[X]** and **[surprising measurable result]**" | "…came back 0% AI-generated" |
| 8 | Authority (4) | "**[Descriptor of famous person/org]** just **[did X]**" | "The man who taught the world machine learning just open-sourced his own AI coworker" |
| 9 | Irony / drama (4) | "**[Giant]** couldn't **[do X]**, and **[underdog]** did it better" | "…Fable 5 refused to run the scan; an open model did it better" |
| 10 | Challenge (2) | "**[N]** **[things]**. I bet you know fewer than **[k]**." | "45 places to launch your startup…" |
| 11 | Coined term (1) | "There's a new kind of **[field]**: it's called **[term]**" | "scroll engineering" |
| 12 | Vivid metaphor (5) | "A **[peanut-sized / Matrix-like / X-alternative]** **[thing]** that…" | "A free alternative to Palantir that can predict the future" |
| 13 | Question (3) | "What happens when you **[action]**?" / "Does your **[thing]** look like *this*?" | "Does your vibe-coded site look like this when you want it to look like this?" |

**Visual hook pairings:** a kinetic `title` building word by word with one `[box]` or `*em*` word; the result shown immediately (`image`/`terminal`); a famous *logo* (never a person's likeness); a big `stat` count-up; a `grid` preview of N items.

**Added from batch-02 (2026-11-12):**
- **Disruption claim, resolved fast:** "Claude just killed web designers." Seen with 2 creators (MotionSites, AIS). Pay it off within 5 s with the real reason ("…your setup can build the same sites"), or it reads as clickbait.
- **Insider-secret question:** "Did you know the best designers use GitHub as their asset library?"
- **Wrong way → right way:** "Many people just Google their keyword. What you actually have to do is…" (local-SEO heatmaps).
- **"This is probably why…":** "This is probably why your new page isn't showing up in Google. And the fix is simple." Diagnosis + relief in one breath.
- **End open loop (retention for 60–100 s reels):** "Stay to the end and I'll show you how to build one in under 60 seconds" / "…I'll give you a tool that does it." Only if the end delivers it.
- **Series tag:** "Day 1 of…" / "DEBUG WITHOUT DEPLOY · 07" under the title builds a habit (follow CTA).

**Hook killers (never):** greetings, channel intros, "in today's video", "let me tell you about", starting with the product name and no outcome, a question with an obvious answer, a hook the reel doesn't pay off, a title that promises something else than the content (batch-02 "lifetime free AI tools" over animation libraries).

## Re-hook phrases (place at 40–60%)

"But here's the smart part." · "And here's the trick." · "Now this next one is huge." · "But that's not even the most interesting part." · "OK, but this is the fun part." · "Now here's where it gets crazy." · "But here's the catch." · "Does that claim actually hold up?"

## Transitions inside lists

"First… / Second… / And finally…" · "Next up…" · "Number three is the one I use every day." · "The last one is the shortcut."

## Honesty beats

"It's still early, so expect a few bugs." · "If you're just chatting, skip it — this only helps with tool-heavy sessions." · "You'll still need to test with real customers." · "Read what a skill can run before you install it." · "Nobody has publicly proven X."

## CTA patterns

| Type | When | Template | Engine |
|---|---|---|---|
| Comment keyword → DM (~55%) | Tools, lists, resources (a link or guide exists) | "Comment **WORD** and I'll send you the link / all N links / the full setup." Keyword = the topic word, UPPERCASE, one word. | `cta` kind `comment` |
| Withheld bonus | Lists | "…and I'll send all 20, including the ones for sound and physics." | `cta` + `line` |
| Save / screenshot | Cheat sheets, checklists | "Save this for your next launch." / "Screenshot this." | `cta` kind `save` or a final `list` |
| Share-to-friend | Niche-useful | "Send this to a friend who's about to launch." | `cta` kind `save` + `line` |
| Question | Comparisons, frameworks | "Which one would you use? / Which first — comment a number." | `title` |
| Series follow | Series | "Follow so you don't miss Day 6." | `cta` kind `follow` |
| None | News, story twist endings | End on the verdict or punchline | `title` / `punch` |

The comment-keyword CTA implies the account owner will send links by DM (manual or ManyChat-style automation). If that's not set up, prefer save/share or "link in the caption/bio".
