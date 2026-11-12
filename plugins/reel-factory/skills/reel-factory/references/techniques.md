# Technique registry

Every discrete technique the system knows, with evidence, the modes it serves, and **where it is implemented**. `/reel-learn` checks new reels against this list before adding anything; a technique seen in a new reel either strengthens an entry (`seen` +1) or becomes a new one. Status: **engine** (a scene/overlay/prop renders it), **script** (a tool does it), **guide** (written guidance only; Claude applies it while writing), **avoid** (anti-pattern).

IDs are stable; never renumber. `seen` counts distinct creators.

## Hooks and retention
| id | technique | seen | modes | status / where |
|---|---|---|---|---|
| T-hook-first-sentence | payoff in sentence one, VO on frame 1 | all | all | guide (playbook) · QA `vo_starts_immediately` |
| T-hook-sticker | persistent hook title for late arrivals / muted viewers | 25+ | all | engine `meta.hookTitle` |
| T-toc-preview | preview every item up front (open loop) | 8 | catalog, presenter | engine `grid`, `progress.style:"chips"` |
| T-toc-chips | chips build under the title, then the current chip stays as a section label | 2 (batch-02) | catalog, presenter | engine `meta.progress` (`style: "chips"`) |
| T-rehook | "but here's the smart part / where it gets crazy" at 40–60% | 30+ | narrated | guide (hooks.md) · `rehook: true` riser |
| T-end-open-loop | "stay to the end, I'll give you the tool / show you how" | 2 (batch-02) | walkthrough, presenter | guide (hooks.md); only if the end delivers |
| T-series-number | "Day 5" / "Day 1" / "DEBUG WITHOUT DEPLOY 07" series tag | 3 | any | guide · `title.kicker` or hookTitle |
| T-killed-profession | "<AI> just killed <profession>" hook, resolved fast | 2 | presenter, kinetic | guide (hooks.md) |
| T-challenge-score | "I bet you know fewer than 10" + `__/45` counter | 1 | catalog | guide |
| T-censor-reveal | withhold the famous name/face (censor bar), reveal at 3 s | 1 | presenter, newsroom | guide (no real-person generation) |
| T-context-bridge | "back in the day… now AI closes the gap" before the list | 1 (batch-02) | presenter, catalog | guide |

## Visual
| id | technique | seen | modes | status / where |
|---|---|---|---|---|
| T-rebuilt-ui | redraw product UI crisp at phone size instead of raw screenshots | 15+ | kinetic, presenter | engine `terminal` `chat` `code` `repo` `walkthrough` |
| T-star-odometer | GitHub star count rolls up | 8 | kinetic, catalog | engine `repo` |
| T-selection-box | Figma-style selection box on the key word | 6 | all | engine rich `[box]` |
| T-serif-emphasis | italic serif accent on the emphasised word | 10+ | all | engine rich `*em*`, caption `serif` |
| T-highlight-sync | highlighter sweeps a source line exactly when it is read | 5 | receipts, newsroom | engine `quote.highlightAt`, `headline.highlightAt` · script build.py speech sync |
| T-zoom-to-source | camera zooms to the README/page section being spoken | 1 (batch-02 Recordly) | quicktake, receipts | engine `walkthrough` (`src` + `zoom` with `say`) |
| T-cursor-demo | cursor glides, types, clicks with a pulse, auto-zoom | 4 | walkthrough | engine `walkthrough` actions |
| T-arrow-annotation | big animated arrows pointing at UI elements | 3 (incl. 2 batch-02) | walkthrough, receipts | engine `walkthrough` action `arrow` |
| T-circle-annotation | red hand-drawn circles / arrows on screenshots | 3 | walkthrough, presenter | engine `image.box` (rect); guide |
| T-news-banner | persistent BREAKING / HEADLINE lower-third | 3 | newsroom | engine `meta.banner` |
| T-headline-card | outlet + date + headline with black highlighter | 2 | newsroom, receipts | engine `headline` |
| T-film-slate | corner brackets, timecode, SCENE n/N | 1 | cinematic | engine `meta.slate` |
| T-progress-stack | cumulative stack/checklist as a progress bar | 3 | story, catalog, walkthrough | engine `meta.progress`, `list.check` |
| T-carousel-dof | card carousel, focused card sharp, neighbours blurred, i/N | 1 | catalog | engine `carousel` |
| T-cheat-sheet | dense end frame + "Screenshot this" | 2 | catalog | engine `sheet` |
| T-typewriter-title | title types itself with an underscore cursor | 2 (Creator 55, Creator 60) | presenter, silent, kinetic | engine `title.typewriter` |
| T-concept-icon-card | one illustrated 3D/isometric icon per concept, locked style | 1 (batch-02) | catalog, presenter | guide (art-direction.md prompt template) · `RF image` |
| T-price-receipt | the competitor's real pricing page as the price anchor | 2 | quicktake, kinetic | guide (screenshot via `RF sources og`) |
| T-reaction-sticker | small reaction stickers above the presenter every ~4 s | 3 | presenter only | guide; original/licensed art only |
| T-metaphor-visual | an analogy drawn literally (elephant vs goldfish, Matrix city) | 6 | kinetic, story, cinematic | guide |
| T-pixel-mascot | recurring small mascot as a brand motif | 5 | any | guide (generate an original mascot; never Claude's/others' marks) |

## Audio and editing
| id | technique | seen | modes | status / where |
|---|---|---|---|---|
| T-200wpm | ~200 wpm, pauses cut | all | narrated | script voice.py tighten + retempo |
| T-minus14 | −14 LUFS master | all | all | script render.py two-pass loudnorm |
| T-bed-duck | music bed ~10 dB under the voice, ducked | 84% | narrated | engine music curve |
| T-functional-sfx | whoosh/pop/type/click/riser/ding | 20+ | all | script build.py auto SFX |
| T-beat-cuts | cuts on the music's beat (no VO) | 3 | silent | script build.py `beat_grid` + `silent_timing` |
| T-own-footage | presenter is the user's own clip, aligned not cut | n/a | presenter | script voice.py `--footage` |

## CTA
| id | technique | seen | modes | status / where |
|---|---|---|---|---|
| T-cta-show-action | mock comment box with the keyword typed, "Sent! Check your DMs" | 6 | all | engine `cta` |
| T-withheld-bonus | "I'll DM all 20, plus the ones for sound" | 4 | catalog | guide |
| T-friction-removal | "you don't have to code or download anything" right before the CTA | 2 | presenter, walkthrough | guide |
| T-share-target | "send it to a friend who's about to launch" | 3 | catalog | guide |

## Avoid
| id | anti-pattern | seen | why |
|---|---|---|---|
| A-readme-scroll | blind README auto-scroll + TTS reading README copy | 7 | the bottom quality tier (Creator 44, Creator 28, Semantica, Next AI Draw.io) |
| A-title-mismatch | hook title promising something else ("lifetime free AI tools" over animation libraries) | 1 (batch-02) | breaks trust; comments call it out |
| A-tiny-16x9 | a 16:9 demo letterboxed in a 9:16 frame with no zoom | 3 | 60% of the frame is black; zoom to the action instead |
| A-repost | reposting another creator's video | 3 | zero original value; rights risk |
| A-misuse | promoting tools to strip watermarks or bypass safety | 1 | guardrail |
