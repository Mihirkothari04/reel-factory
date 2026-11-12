# Creation modes: how a reel is *constructed*

A **mode** decides how the information reaches the viewer: what is on stage, who (if anyone) presents, where the visuals come from, whether there is a voice, how fast it cuts, how loud the bed is, and which tools and agents do the work. A **skeleton** (`formats.md`) decides the order of beats. Pick the mode first, then a skeleton the mode supports.

Two reels on different topics can share a mode; two AI reels can use completely different modes. The categories come from 90 analysed reels, sorted by construction rather than by subject (`corpus.md` has the mapping).

| id | Mode | Construction in one line | Corpus share |
|---|---|---|---|
| `kinetic` | Kinetic Explainer | faceless designed scenes, one claim per composition | ~15% |
| `presenter` | Presenter + Board | face (avatar or your footage) + motion-graphics board | ~45% (largest) |
| `story` | Illustrated Story | named character, failure→fix chapters, progress stack | 1–2 (highest quality) |
| `newsroom` | Newsroom Brief | BREAKING banner, highlighted headlines, chronology | ~5% |
| `receipts` | Receipts | primary sources highlighted as they are read → verdict | ~7% |
| `catalog` | Rapid Catalog | preview grid, i/N carousel, cheat-sheet end frame | ~12% |
| `walkthrough` | Screen Walkthrough | one app window, cursor types/clicks/zooms through steps | ~10% |
| `cinematic` | Cinematic Hype | generated hero shots, film-slate HUD, 1–2 s cuts | ~6% |
| `silent` | Silent Showcase | no voice, beat-cut text over a stunning result | ~4% |
| `quicktake` | Quick Take | headline sticker over the source itself, same-day | ~9% |

Machine-readable registry: `modes.json` (defaults, QA overrides, requirements, fallbacks), used by `rf build`, `rf qa` and `rf modes`. One playbook per mode: `modes/<id>.md`. **Read the chosen mode's playbook before writing the brief.**

## Fit scoring (do this per topic, after research)

Score every *available* mode 1–5 on each axis, using the research, not habit:

1. **Shape fit**: does the topic's natural shape (one tool / many items / a timeline / a claim / a sequence of steps / a concept stack) match the mode's skeletons?
2. **Visual supply**: can we actually show it? (rebuilt UI and diagrams are always available; official media only if found; generated imagery if budget allows; real screen capture only if `browser_capture`.)
3. **Register**: the emotional tone the topic needs (sober for security and money; playful for design and fun tools; urgent for news).
4. **Audience**: what the target viewer expects and saves (devs: mechanism and commands; designers: taste and results; general: stakes and plain words).
5. **Freshness and speed**: breaking news favours `quicktake`/`newsroom`; evergreen favours `story`/`kinetic`/`catalog`.
6. **Variety**: subtract 1 if the last two productions (`rf modes` history) used the same mode, unless the channel deliberately runs a series.

Fit = mean of the six. Recommended = highest fit. Ties go to the cheaper mode.

## Presenting the choice (interactive runs)

Unless `--mode <id>` or `--mode ai` was given, `--count N` is running, or `config.modes.ask` is false:

1. In chat, print one table of **all** modes: `★` on the recommended one, the fit score, availability, and a **topic-specific** one-line description of what *this* reel would look like in that mode (for example "Newsroom: open on the Verge headline 'Cloudflare launches Kitesurf', banner 'Cloudflare ships a browser for AI agents', then the 24-hour developer reaction"). Never paste the generic `one_liner`; write what this topic becomes.
2. Ask with `AskUserQuestion` (one question, header "Mode"). Options:
   - `<Recommended mode> (Recommended)`: description = the topic-specific line plus why it wins;
   - the 2nd and 3rd best modes, each with its topic-specific line;
   - `AI Select`: "Let the Creative Director decide after weighing all modes, the research and recent history; may blend in one device from another mode."
   The automatic "Other" lets the user type any mode id from the table. Put the names of the remaining modes in the question text, so they are visible inside the dialog.
3. Record the choice and the reason in `brief.md`. This is the **only** question the pipeline asks; everything after it stays autonomous.

## AI Select

Not just "take the top score". Re-read facts.md angles and do-not-say, weigh the top 3 modes against the strongest *angle* (the most surprising true thing), check history for repetition, and pick one primary mode. You may borrow **at most two devices** from another mode when they serve the angle (for example a `receipts` quote card inside a `catalog`, or a `newsroom` banner on a `quicktake`). Write a 3–5 line justification in brief.md: chosen mode, runner-up, why the runner-up lost, and borrowed devices.

## Mode × skeleton compatibility

| skeleton | kinetic | presenter | story | newsroom | receipts | catalog | walkthrough | cinematic | silent | quicktake |
|---|---|---|---|---|---|---|---|---|---|---|
| spotlight | ● | ● | | | ● | | ○ | ● | ● | ● |
| listicle | ○ | ● | | | | ● | | ○ | ● | |
| tutorial | | ● | | | | | ● | | ○ | |
| news | | ○ | | ● | ● | | | | | ● |
| claim-test | ● | | | | ● | | | | | |
| problem-ladder | | | ● | | | | | | | |
| framework | ● | ○ | | | | | | | | |
| tier-list | ● | ● | | | | ● | | | | |
| comparison | ● | ● | | ○ | | | | | | |
| action-reaction | ● | | | ● | | | | ● | | ● |
| stack-roadmap | ● | | | | | ● | ● | | | |

● native · ○ works with care

## Fallbacks (never fail a run on a missing capability)

- `presenter` without avatar or footage → `kinetic`, keeping the presenter-style script (first person, verdict).
- `cinematic` with no image budget and no video_gen → `kinetic` on the `noir` theme with slate HUD and kinetic type.
- `story` with no image budget → diagram-driven story (flow/list/versus scenes as "illustrations"), same ladder structure.
- `walkthrough` without real captures → rebuilt UI (`walkthrough` scene with `rows`), still with cursor, typing and zoom.
