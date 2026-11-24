# Category `github-repo`: an open-source project as the subject

**Read only when** the reel presents a repo / open-source tool (what it is, who built it, how to run it). Evidence: 77 of the 100 batch-04 reels (median 48.5 s, 37–57; 201 wpm, 175–231; first cut 3.1 s). Often combined with `agent-skill`, `oss-alternative` or `top-n`.

## Who watches and why the reel is built this way
Builders scrolling for useful projects. Their questions: *what does it do for me*, *is it legit* (stars, builder, company), *can I run it* (install, local, free, API key?). A repo has no ad budget and no official video, so the creator's proof is the repo itself made watchable: the page zoomed to the line being read, the demo GIF cropped to the action, the star count, the builder's real profile. The quality gap in this category is enormous: the bottom tier is automated README-scroll channels; the top tier turns the same README into a guided tour.

## Opening lock (verbatim corpus patterns)
- Discovery: "Someone just open-sourced…" / brand + recency: "Vercel just open-sourced…", "China just open-sourced…" (Creator 22 formula).
- Authority: "The man who taught the world machine learning just open-sourced his own AI coworker."
- Pain / villain: "You are losing 4 GB of RAM every morning because of hidden web browsers inside your apps." → "A tool called Pake just fixed this."
- Person first: "Who is this guy?" over the builder's real photo/post.
- At 0 s the screen shows the thing: the result/demo, the repo page, or the villain; never more than ~1 s of face alone.

## Proof shots that work
1. **The repo page, zoomed** to the line being read (`image` shot with `highlight`, camera moving to each phrase); the camera ending on the **star button**.
2. **Stars with a date or momentum**: "★ 8,540 · 18 Oct 2026", a Star History line drawing itself (`RF shot` of star-history.com), "+970 today". Round spoken numbers only downward to a milestone ("over 40K" for 42.5k) and keep screen and caption identical.
3. **The builder**: their real X/LinkedIn profile or announcement post (arrow on the name), the company behind it. Credit them in the caption (`Repo by @…`).
4. **The demo GIF/video panned or cropped to the action**, never letterboxed small (A-tiny-16x9); README badge row as a quick credibility shot.
5. **Run it**: one curl/npm line, the `localhost` URL visible (proves it runs locally), the first result.
6. **Breadth at a glance**: a logo wall for "40 connectors", the README table walked row by row *with zoom*, community outputs shown with their creators' own credits.

## Construction with our studio engine
- Mode `presenter` (split or corner) is the default; `quicktake` for same-day trending repos (hook sticker over the source, 20–35 s).
- Every narrated feature = one zoom/highlight on the real page or one demo crop; a new picture every 1.5–2.5 s.
- gfx: `counter` for stars (dated `label` under it), `sticker` of the logo on its name, `label` source chips ("github.com/owner/repo").
- Beat template (spotlight, 35–50 s): STOP outcome/pain → name + builder + stars → 2–3 capabilities, each shown → re-hook (the surprising capability or "and it runs fully local") → run it (one line) → honest limit (needs your own API key, early, Mac only) → CTA.

## Quality tiers (learn from both ends)
- **Floor (automated channels: Creator 44, gittrend, fork.cast, gitscout):** TTS reading README copy over a blind scroll, no zoom, tiny text, no presenter. Avoid all of that.
- **Cheap things the floor does right (copy them):** caption line `⭐ 4,397 · 📈 +970 today · Python`; `Repo by @author`; a script that follows the README's section order so each zoom is easy to place.

## CTA and caption
- Keyword (tool name / REPO / the giveaway) or the link in the first comment; "screenshot this" over the install block when one command is the whole value.
- Caption: one-line summary → link or keyword → stars line (dated) → install command → honest limit → credit to the builder → 3–6 specific hashtags or a search-phrase line.

## Pitfalls seen in this category
- Blind README scroll + README-speak (the floor).
- Star counts that disagree between VO, screen and caption (4 of the repo reels: 20k/22k, 45k/33.5k, 167k/143k, 95k/90k).
- False recency ("shipped last week" for a years-old project); unmeasured multipliers ("20x LIGHTER") shown as posters.
- B-roll of a different repo while this one is named.
- Crediting the repo to a famous person who only shared it; head-of-state or celebrity photos as decoration.

Evidence (batch-04): Creator 12 (prompts.chat, DeepInfer, T3 Code), Creator 22 (Wan2GP, Unlimited-OCR, TencentDB memory, Octogent), Creator 05 (OpenWorker, Deepsec), Creator 37 (Strix, Cloudflare audit), Creator 92 (Pake), Creator 96 (best-practice repo, Matt Pocock skills: phone filming a monitor, finger as pointer), Creator 87 (Spec Kit table walk), alassafi (Recordly: zoom to the star button), Creator 68 (ArcReel badge row), and the floor channels above.
