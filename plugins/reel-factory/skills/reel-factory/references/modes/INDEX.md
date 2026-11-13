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

## Structures and elements: combine, don't pick one

Successful reels combine methods: a presenter hook that turns into a screen walkthrough, a cinematic cold open on an explainer, a newsroom banner over a quick take. So the choice has **two layers**:

- **Structures** (the 10 modes above) are the storytelling backbone: who and what carries the reel and how the beats are built. A reel has **one primary structure** and may **sequence up to two more** as segments, for example `presenter → walkthrough → presenter` (hook, demo, verdict).
- **Elements** are individual techniques layered on top, from `techniques.md` and the engine:

| element | what it adds | requires | conflicts |
|---|---|---|---|
| `ai-presenter` | talking-head avatar (full frame or split) for hook, verdict or CTA | presenter provider (HeyGen / MuseTalk) | silent |
| `source-shots` | real page or post screenshots with synced highlights (hard rule for web sources) | capture ladder | |
| `cursor-demo` | app window with cursor, typing, zoom and arrows | screenshots or rebuilt UI | |
| `cinematic-broll` | generated hero shots, slate HUD, fast cuts | image or video budget | sober topics (security, money) |
| `breaking-banner` | persistent lower-third banner | | cinematic slate (one HUD at a time) |
| `progress-stack` | progress bar or ToC chips (steps, ladder) | 3+ steps | |
| `typewriter-title` | typed kinetic hook | | |
| `stat-pops` | big number count-ups as pattern interrupts | numbers in facts.md | |
| `carousel` | i/N cards flying past | 3+ items | |
| `cheat-sheet` | dense end frame (screenshot bait) | 6+ items | |
| `illustrated-character` | a fictional mascot through the reel (story ladder) | image budget | presenter as the main face |
| `beat-cuts` | text beats snapped to music beats | music | dense narration |

**Combination rules:**
- One face at a time: an avatar presenter and an illustrated character can't both lead.
- One persistent HUD at a time: banner, slate or progress.
- At most 4 elements in a 60 s reel.
- Every element must serve the angle in brief.md. Visual variety is not a reason on its own.
- When segments switch structure, the narration profile switches too, with a spoken bridge sentence (speechwriting skill).

Storyboard: `meta.mode` = primary structure; `meta.segments` = `[{"mode": "presenter", "scenes": ["s1", "s2"]}, {"mode": "walkthrough", "scenes": ["s3", …]}]` (optional, for sequenced structures); `meta.elements` = element ids. Scenes may carry `"mode"` to mark which segment they belong to.

## Presenting the choice (interactive runs)

Unless `--mode` was given, `--count N` is running, or `config.modes.ask` is false:

1. **In chat**, print two tables.
   - **Structures:** all 10 modes, with `★` on the recommendation, fit score and availability. Add a **topic-specific** line saying what *this* reel becomes in that mode (never the generic `one_liner`).
   - **Elements:** the elements that fit this topic, each with a one-line effect for this reel.
   - Then show the **recommended combination** as a concrete line, for example: "★ presenter hook (avatar) → walkthrough of the claim flow → presenter verdict + source-shots + progress-stack".
2. **Ask once** with `AskUserQuestion` and two **multi-select** questions. The dialog allows 4 options per question.
   - Q1 (header "Structures", `multiSelect: true`): the 3 best-fit structures (the recommended one marked "(Recommended)") and `AI Select`. The question text names the remaining modes and says "Other: type mode ids in order, e.g. presenter, walkthrough".
   - Q2 (header "Elements", `multiSelect: true`): the 4 best-fit elements for this topic, the recommended ones marked "(Recommended)". The question text lists the other compatible elements.
   - Selected structures are taken **in the order the user typed or ticked them**. The first is primary, and the others become segments in a sensible beat order.
   - If both answers are AI Select, or empty, do a full AI Select.
3. **Validate** against the combination rules. If a pick conflicts, keep the user's intent, drop the conflicting part, and say why in brief.md.
4. Record structures, segments, elements and reasons in `brief.md`. This is the **only** question the pipeline asks.

## AI Select (combination-aware)

Not just "take the top score":
1. Re-read the facts.md angles and do-not-say.
2. Weigh the top structures against the strongest *angle*, the visual supply, the audience and recent history.
3. Choose the **combination**: 1 primary structure, 0–2 sequenced segments, and 1–4 elements that each serve the angle.

Prefer simple. A single structure with two strong elements beats a three-segment patchwork. Write a 3–6 line justification in brief.md: the combination, the runner-up combination, why it lost, and how the segments bridge in the narration.

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
