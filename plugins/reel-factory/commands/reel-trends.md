---
description: Show the top trending AI/tech topics for reels right now (no production)
argument-hint: "[niche hint, e.g. 'design tools' or 'security']"
---

Run only stage 1 of the **reel-factory** skill: launch the `reel-factory:trend-scout` agent with today's date and the niche hint `$ARGUMENTS` (if any), writing trends.json to the current folder under `reel-productions/`. Present its top 3 recommendations (topic, why now with numbers, angle, format, sample hook, sources) as a compact table, and end with the exact `/reel <topic>` command to produce the best one.
