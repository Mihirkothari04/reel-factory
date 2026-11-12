---
description: Produce a complete Instagram Reel autonomously — give a topic/URL, or nothing for trend discovery
argument-hint: "[topic | URL | auto] [--mode <id>|ai] [--format …] [--theme …] [--length 45] [--footage clip.mp4] [--draft] [--count N] [--no-music]"
---

Use the **reel-factory** skill (load it with the Skill tool if it isn't loaded) and run its full pipeline now.

Arguments: `$ARGUMENTS`

- Empty or `auto` → **Mode 1: trend discovery** (trend-scout picks the topic from live data).
- Anything else → **Mode 2: user topic** (treat it as the topic, URL, or brief; flags as described in the skill).

After research, offer the **creation-mode choice** once (10 modes with topic-specific one-liners, a ★ recommendation and an "AI Select" option; skipped with `--mode <id>`, `--mode ai`, or `--count`). Everything else is autonomous: make every creative and technical decision yourself, log decisions in the production's `brief.md`, use free fallbacks when a paid service is unavailable, and only report back when the reel is rendered and QA'd (or if setup is impossible). Presenter mode with `--footage`/own recording is the only case that waits for the user's clip.
