# Reel categories: subject-specific construction (read ONLY for a matching reel)

The general knowledge base (playbook, modes, formats, hooks, studio) applies to every reel. The files in this folder apply **only** to reels of their category. They describe how creators build that particular kind of reel, and why. **Never carry a category's devices into a reel of another type.** An incident, news, explainer or story reel keeps its own construction; it gets nothing from these files.

| id | category | file | read when the reel is about… |
|---|---|---|---|
| `agent-skill` | Claude / agent skill, plugin or MCP server for a task | `agent-skill.md` | one or more skills, plugins, MCP servers, slash commands or agent add-ons (Claude Code, Codex, Cursor…) that make an AI agent do a job |
| `github-repo` | GitHub repo / open-source tool | `github-repo.md` | an open-source project or repo as the subject (what it does, who built it, how to run it) |
| `oss-alternative` | open-source alternative to an AI tool or technology | `oss-alternative.md` | a free / open-source thing positioned *against* a paid or famous incumbent |
| `top-n` | top-N list of repos / skills / plugins / tools | `top-n.md` | several tools/repos/skills presented as a numbered list |

- Set `meta.category` in `storyboard.json` (one id, or a list when they combine, e.g. `["top-n", "agent-skill"]`). Record the choice in brief.md.
- Combinations are normal (a "5 free repos that replace paid tools" reel is `top-n` + `oss-alternative` + `github-repo`). Read every matching file; when two disagree, the more specific wins (`oss-alternative` > `github-repo`; `top-n` decides the list structure).
- If the topic matches none of them, read none of them.

Evidence: batch-04, "AI Dev Tools Reels" Parts 01–02 (100 reels saved 2026-04-23 → 2026-11-10; 42 new to the library + 58 already analysed, re-mined for captions and CTAs). Tags per reel: agent-skill 61, github-repo 77, oss-alternative 6, top-n 13 (a reel can carry several). Per-reel notes: `analysis/notes/batch-04-*.md` in the project; rows in `corpus.md` › batch-04.

## Why these reels look the way they do (and why our incident/news reels don't)

The viewer of a dev-tool reel has a different job than the viewer of an incident/news reel, and every device follows from that job.

| | dev-tool reels (these 4 categories) | incident / news / explainer reels |
|---|---|---|
| the viewer's question | "Is this worth installing, and how do I get it?" | "What happened, why, and what does it mean for me?" |
| what counts as proof | the tool **working**: install line, the agent running it, its output, the same input with and without it; trust signals (stars, the builder, the big company behind it) | sources: outlet headlines, official posts, documents, footage of the named people and places, a dated chronology |
| presenter's role | a **recommender** ("I use this", "my pick", "honestly you only need five"): first person, opinions, short face moments between proof shots | a **reporter / narrator**: attributes claims, keeps balance ("not proven"), carries the stakes |
| motion graphics | rebuilt UI, terminals, install logs, slash-command menus, logo pills, rival logos struck out, callout tags on flaws, star counters, list counters and chips | headline cards with highlights, maps, timelines, counters for numbers, labels with outlet and date |
| CTA economics | the link is the product: comment-keyword → DM, caption cheat sheet, first-comment link; the reel exists to deliver a tool | follow / save / share or no CTA; nothing to "get" |
| caption | a working document (names, install commands, honest limits) | context and sources |
| freshness | days (a repo trending this week) | hours (the event) |

So when a dev-tool reel shows a struck-out rival logo or a typed install command, that is because its viewer is shopping for a tool. In an outage report the same device would be noise. Keep them apart.

## Traits shared by the four categories (this family only)

Measured on the 100 reels (library metrics; IQR in brackets):
- length 48 s (35–57); speech 0.9 of the runtime; voice from frame 1; −14 LUFS; 200–210 wpm median (fast creators 230–258).
- **Presenter + board is the norm** (35 of the 42 new reels; the rest walkthrough, quicktake, silent): split (content top, face below), full-frame selfie with overlays in the headroom, or a keyed presenter over the content. The face is short and personal; the proof carries the reel.
- **The proof is the tool itself**, captured for real: README/site pages zoomed to the line being read, the terminal, the agent's UI, the output. Rebuilt UI only where a capture is unreadable.
- **CTA = comment keyword → DM** in ~60 %; the keyword names the tool or the giveaway. The rest: first-comment link, "screenshot this" over the install block, follow-only.
- **Caption = a deliverable** (see each file): cheat sheet, full script, or the caveat the VO had no room for.
- **The same numbers everywhere.** 7 of 100 reels contradict themselves (VO "20k stars", caption "22k"); `rf build`/`rf qa` now warn when VO, screen and caption disagree.

## Engine support used by these categories

All optional studio gfx; nothing changes for reels that don't use them (`studio.md` › gfx):
- `sticker` + `"strike": true`: a red slash crosses the logo out ~0.35 s after it lands (rival / paid tool).
- `label` + `"icon": "cut/logo.svg"`: a brand pill (logo + name).
- `callout`: a tag at `x,y` joined by a leader line to the element at `tx,ty` (flaws, parts, security holes).
- Fast `shots` (0.3 s apart) for a flash preview; `scene` shots (`terminal`, `repo`, `walkthrough`, `carousel`, `sheet`, `grid`, `list`) for rebuilt UI.
