# Category `agent-skill`: a skill, plugin or MCP server that makes an AI agent do a job

**Read only when** the reel's subject is one or more agent add-ons (Claude Code skills, plugins, MCP servers, slash commands, CLAUDE.md files, Codex/Cursor equivalents). Evidence: 61 of the 100 batch-04 reels (median 48 s, 35–56; 207 wpm, 185–232; first cut 2.4 s).

## Who watches and why the reel is built this way
The viewer already uses an AI coding agent and wants it to be **better at one job** (design, tokens, testing, research, video, security). They decide in seconds whether the add-on is worth installing. So the reel has to answer three things on screen: *what changes for my agent*, *is it trustworthy* (who built it, is it real), *how do I get it* (one line, or the keyword). The face is a recommender ("I use this", "you only need five"); the proof is the agent visibly behaving differently.

## Opening lock (verbatim corpus patterns)
| pattern | STOP → AMPLIFY → COMMIT |
|---|---|
| brand + recency | "Google's Android team just released free skills…" → "thousands of Google engineers use them" → the mechanism |
| reduction | "Claude has over 100,000 skills…" → "…but honestly, you only need five." → numbered arrows 1–5 drawn on screen |
| pain / contrast | "Claude is great at code but terrible at design." → "…here's the fix" → before/after |
| threat | "Your Claude skills might have malicious code hidden inside them…" → "NVIDIA just solved this" → the scan |
| profession / outcome | "Claude Code just killed web designers." / "A $10,000 website with basically one command" → the finished site at 0.5–4 s → "here's the setup" |
| person first | "Who is this guy, and why is every developer installing his skills?" (the builder's real photo/post) |
| prohibition | "Do not build a new website until you have these six Claude skills." |

## Proof shots that work (pick 2–4 per reel)
1. **The install line** typed into the agent, or **the agent installing it itself** (Claude Code running `/plugin install …`). One line; OS-branch lines only if they differ ("Mac → …, Windows → …").
2. **The skill's own file**: SKILL.md / README open in an IDE with its description or trigger line highlighted as it is read. Cheap, checkable.
3. **The command running**: the slash command typed, the agent's real output streaming.
4. **Same input, with and without** (strongest for behaviour-changing skills): two opposite prompts the stock model agrees with, then the skill on the same input; or a red failing terminal state turning green; or opposed counters (tokens without vs with).
5. **The output itself**: the site, video, image, PR it produced; "← rendered this video" when the reel itself was made with it (truthfully).
6. **Works with any agent**: a row of Claude Code / Codex / Cursor / Gemini logos (6 of 20 Claude reels in one chunk).
7. **Authority**: "built by Anthropic / Vercel / Google / Addy Osmani / Matt Pocock", shown with the real post or repo owner, never a generated face.

## By sub-type
| sub-type | proof that lands |
|---|---|
| design skills (Hallmark, impeccable, taste, DESIGN.md) | **slop autopsy**: the AI-generic page with `callout` tags naming each cliché ("PURPLE GRADIENT", "INTER FONT (AGAIN)", "CARDS ON CARDS") → wipe → the premium result; 3 outputs from 3 recognisable inputs stacked |
| token / cost tools (Headroom, MarkItDown, CodeBurn, compaction, routers) | the agent's own usage bar filling (pain meter); unit cost × N = total; a shrinking bar "BEFORE 10K → after"; for routers, a radio list or sorting bins choosing a model per input |
| workflow / process skills (grill-me → to-prd → to-issues, spec kits, council) | the chain: each skill's output feeding the next; for multi-agent skills a **cast**: one icon + one-line job per role, roster stacked first |
| MCP servers | one micro-widget per server showing *what changes for the agent* (a form filled by the browser MCP, outdated API line struck and the live doc below it) |
| security skills / scanners | the scan output with counts, the vulnerable line, authorised-testing framing |
| media skills (video, image, motion) | the output, then the prompt that made it |

## Construction with our studio engine
- Mode `presenter` (split/corner) with a `walkthrough` segment for the live demo; ~45–60 % of the frame time is proof.
- Shots: real captures (`RF shot`, agent-browser `record` of public pages); rebuilt `terminal`/`code` scenes only where a capture is unreadable.
- gfx: `label` + `icon` brand pills on each named tool; `callout` for autopsies; `counter` for stars/tokens; `sticker` logos on the exact word they are named.
- Beat template (spotlight, 40–50 s): STOP on the outcome/pain → name + who built it + one trust number → install (one line) → mechanism in 2–3 shown steps → A/B or output proof (re-hook "but here's the part that surprised me") → honest limit → CTA.

## CTA and caption
- Keyword = the tool's name or the giveaway (SETUP, CLAUDE, MCP); the DM carries the install commands. Free tool links can be open; gate the setup guide.
- Caption = the **install steps** or a cheat sheet: what it does → install command → "Honest limit:" → "works with Codex/Cursor too" footnote → save line.

## Pitfalls seen in this category
- Claiming behaviour the reel never shows (the A/B is the cure).
- Using Anthropic's/Claude's mascot or marks as our branding (show them only where they appear in a real capture).
- Proper nouns mangled on screen ("CLODCODE") or by TTS: lexicon entry for every product name; write on-screen names from the source.
- Overclaim: "one command" over four installs; "the official Anthropic …" for a community repo; crediting a repo to a famous person who only tweeted it.
- A 10–15 s face-only tail after the last proof.

Evidence (batch-04): Creator 37 (Promptive Sentry, 5 skills, find-skills), Creator 45 (agent-browser, find-skills, 5 skills), Creator 99 (Headroom, Hallmark, agent-skills), Creator 22 (MarkItDown, CodeBurn, Octogent), Creator 71 (Council), Creator 69 (LLM Council A/B), Creator 83 (3 chained skills), Creator 73 (5 MCP servers), Creator 78 (6 plugins, RuFlo), Creator 81 / Creator 67 / Creator 76 ("killed web designers", one-command site), Creator 93 (Picsart CLI), Creator 05 (Matt Pocock skills), Creator 84 (CLAUDE.md guardrails), Creator 85 (6 website skills), Creator 80 (GSAP skills), Creator 100 (DESIGN.md extractor), Creator 72 (Higgsfield MCP).
