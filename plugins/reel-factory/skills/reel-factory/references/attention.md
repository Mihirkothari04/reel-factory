# Attention and spread: stop the scroll, hold to the end, keep them talking after

Read this every run. It covers every reel type (news, explainer, tool, list, story), and it governs the script, the edit and the post kit.

**Evidence:**
- 60 recent AI/tech reels with likes, comments and follower counts (batch "Saved 2 - last 60 Reels with engagement", 2026-11-26), watched whole: transcripts plus a frame every 2–3 s.
- The owner's own first two reels, through Instagram insights. Their skip rate was 61–62 %, the average watch 7–10 s of 83–94 s, and 0 comments. About 75 % of viewers were gone within 3–5 s.

**Why it matters:** Instagram lists **skip rate first** among the signals that decide reach. It then weighs shares, likes, saves, reposts and comments per viewer. Follower count does not cap reach:
- a 3.2K-follower page got 27K likes (8.6× its followers);
- a 22K page got 42K likes;
- 755K–981K pages often get under 1 % of their followers in likes.

Every new reel is tested on strangers, and the first seconds decide how far it travels.

## 1. STOP: the first 1.5 seconds

1. **The first 2–5 words carry the emotion or the stake.** That can be a human reaction, a vivid "you" scene, a blunt verdict, or a quote from someone famous. It is never an attribution, a date, a background fact or a topic name.

   | stops the scroll | gets skipped |
   |---|---|
   | "Mathematicians are crying, and the reason is this PDF." | "An Anthropic mathematician says Claude helped him…" (attribution first) |
   | "Imagine you speak English, and everyone on the call hears you in their own language." | "Someone open-sourced a translation tool called…" |
   | "Java is broken." | "A new vulnerability, CVE-2026-…, affects Java." |
   | "'Elon, please hire Jensen,' one tweet said." | "Breaking news: Jensen Huang has resigned." |
   | "Don't be dumb enough to think he's #1 only because of his guests." | "Here's the system behind a podcast." |

   News still follows the newest-first rule (hooks.md): the newest development, told through its most human or surprising detail.
2. **Keep the first sentence short enough to land in ≤ 3 s, about 12 words or fewer.** Put the rest of the stake in sentence two. A 25-word opener packed with three facts loses viewers before it finishes.
3. **The picture changes within the first second and keeps changing through 5 s.**
   - Measured on 15 top reels: 8 cut to a new picture within 0.8 s, with 4–23 big changes in their first 5 s.
   - The others hold one shot, but it *moves*: a live demo playing, a title building word by word, a grid filling.
   - Examples: a tweet pops onto a photo, a real clip cuts to a document, a face cuts to the proof.
   - Never hold one static shot for the whole hook. Our NVIDIA reel had 0 changes in 0–5 s and lost about 75 % of viewers by 5 s.
   - QA warns (`hook_motion`) when there is no big change in the first 2 s.
4. **Show a real human face or real proof at 0 s.** That means the person's own clip, their post, the headline, the result or the product working. Emotion on a real face beats any graphic.
5. **Add a persistent headline or progress device whenever the reel has a frame for it.** A title stays on screen ("50-minute interview, speakers labelled in 3 s"), or empty slots or a counter are visible ("1. … 10.", "03 / 45", "YOU KNOW: __ / 45"). Late arrivals understand the reel instantly, and empty slots pull viewers forward.

## 2. HOLD: the middle

1. **Run an open-loop ladder.** A new small question opens every 5–10 s, before the last one fully closes:
   - "Everyone thought that was the worst of it. It wasn't."
   - "Here's what most people miss."
   - "So, is Elon actually hiring him?" (a callback to the hook at 70 %)
   - "Then a new hire asks…"

   Never let 10 s pass where the viewer knows how the sentence ends.
2. **Build the story around a protagonist or a recurring scenario.**
   - Examples: Hugo, the mathematician who lost his decade of work; "Nova", the company AI that breaks again in every layer.
   - The problem → fix → new problem rhythm escalates by itself. This is the only pattern that held viewers past 100 s (a 128 s reel got 72K likes).
3. **Make the scale something the audience feels.** Compare numbers to something native to the audience:
   - "wiped out more than Reliance's entire value" (Indian audience);
   - "3,700 pages in his whole career, 3,500 pages in one night", drawn as two paper stacks.

   Use the config `audience` (country, age) to pick the comparison. Never use a raw "$X billion" alone.
4. **Let real people supply the emotion.** Use 2–3 short clips of the people involved: crying, angry, celebrating, a famous voice's one-line verdict. The narrator carries the facts.
5. **Change the picture every ~2 s for the whole reel**, not only in the hook. Each change shows the noun being said.
6. **Ask a mid-reel question at 40–60 %.**
   - Example: "Would you trust a proof no human understands? Hold that thought."
   - Or a self-scoring device: "count how many of these you knew".
   - It turns passive watching into an opinion before the end, so the end CTA lands on someone already engaged.
7. **Fit the length to the story's escalation, not to how much was researched.**
   - News and explainers: 35–60 s.
   - Tools and lists: 30–60 s.
   - Over 60 s only when a protagonist story escalates every beat (story mode), and the reason is logged.
   - The facts that don't fit go into the caption (§4).

## 3. END: loop and leave

1. **Use a callback ending.** The last line echoes the first, so the final frame flows back into the start and people rewatch:
   - "…but this time they got replaced by a PDF";
   - "…and Nova recommends your competitor";
   - "one equals sign broke Java's fastest code."
2. **End on the punchline or verdict, then the CTA in one short sentence of 3 s or less.** No sign-off, no "see you in the next one".
3. **Make the last frame save-worthy when there's a list.** Example: all 45 items on the final frame, with "Screenshot this."

## 4. BEYOND: the post kit (comments, shares, saves, follows)

Every reel ships `out/post-kit.md`. It is written from storyboard `engagement` (storyboard-schema.md) and posted by the team.

| lever | what top creators do | how we do it |
|---|---|---|
| **Comment keyword → DM** | "Comment SKILL and I'll send you the link." 30 of 57 use it, and they get about as many comments as likes. Reels without it get about 1 comment per 50 likes. | Only when there's a real deliverable: a source pack, full timeline, tool links, cheat sheet. One keyword, the topic word, UPPERCASE. |
| **Follow-gated DM** | "Follow first so my DM reaches you." / "Comment FOUNDER **and follow**." | Add it to every keyword CTA. It turns commenters into followers. |
| **Pinned comment holds the payload** | "All app names are in the pinned comment." / "The repo is pinned." | `engagement.pinned_comment`: the list, the link, or a two-sided debate question. Pin it right after posting. |
| **Caption = second act** | Extra quotes and facts not in the video, the fairness caveat, then a personal, identity-targeted question: "If you're a student right now: what would you do with four years…?" / "How many did you know?" / "Which layer does your team always skip?" | First line = the hook restated. Then 2–4 facts or quotes that didn't fit. Then ONE easy question about the **viewer** (answerable in one word or a number), not about the news. |
| **Named share target** | "Send it to a friend who's about to launch." / "Share this with all Windows users." / "…with someone building for Bharat." | `engagement.share_line`: a specific person the viewer knows, said in the reel or the caption. |
| **Follow with a promise** | "Follow, because the moment Nvidia names its new CEO, I'll break down what happens next." / "For the next 49 days, one growth system a day." | Follow CTAs always promise a specific next episode (a sequel, a series day), never "for more content". |
| **Story funnel** | Followers bring about 30 % of views through Stories. | `engagement.stories`: 3 frames. (1) Teaser + poll before posting. (2) Share the reel: "Here's what actually happened 👇". (3) A few hours later, a fact or question from the reel with a poll or slider. |
| **Off-platform community** | End card: "Join the free WhatsApp community." | Only when the owner has one. Configured in `config.brand.community`. |

## 5. Checklist (script critic and qa-reviewer apply it)

- [ ] First 2–5 words carry emotion or stake; first sentence ≤ ~12 words; no attribution-first.
- [ ] A new picture within ~1 s and changes through 5 s (or one shot that visibly moves); a real face or real proof at 0 s.
- [ ] Open-loop ladder: a new question at least every 10 s.
- [ ] Scale compared to something the audience knows.
- [ ] Mid-reel question or self-scoring device at 40–60 %.
- [ ] Callback ending; CTA ≤ 3 s; no sign-off.
- [ ] Length inside the mode range (news/explainer 35–60 s), or logged as story-mode escalation.
- [ ] `engagement` complete: pinned comment, caption question about the viewer, share target, follow promise, 3 story frames, plus a keyword and deliverable when one exists.
