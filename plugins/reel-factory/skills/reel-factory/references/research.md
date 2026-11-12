# Research protocol (trend-scout, topic-researcher, fact-checker)

## Trend discovery (Mode 1)

1. **Hard signals:** `python "${CLAUDE_PLUGIN_ROOT}/scripts/rf.py" trends --days 7 --out <prod_root>/trends.json` covers GitHub new repos by star velocity, GitHub trending (daily and weekly), Hacker News, Hugging Face trending models, and Lobsters, with spam filtering and cross-source convergence scoring.
2. **Soft signals (web search):** AI and tech news from the last 7 days (major-lab launches, model releases, big open-source drops), what AI creators are posting on Instagram, TikTok, YouTube Shorts, and X, Reddit discussions (r/LocalLLaMA, r/ClaudeAI, r/ChatGPT, r/singularity), and Product Hunt top launches. Run several searches with different phrasings and include the current month and year.
3. **Score each candidate 1–5** on: *novelty* (≤14 days old; ≤7 is better), *momentum* (stars/day, HN points, number of independent sources: **convergence is the strongest signal**), *audience value* (free, saves time or money, solves a felt pain, wow outcome), *visualisability* (can we *show* it?), *verifiability* (primary source exists), *saturation risk* (already covered to death? find a fresh angle or skip), *brand safety*.
4. Return the **top 3** with evidence links and a recommended pick plus format. The orchestrator decides without asking the user.

Skip: spam or malware-lure repos (fake stars, "Pro 2026 standalone installer"), crypto pumps, unverified rumours, anything requiring login to show, and scandal stories with no reliable outlet.

## Topic research (both modes)

Run two `topic-researcher` agents **in parallel**:
- **A, primary-source and technical:** official repo, README, docs, launch blog, paper; exact numbers, install commands, requirements, license, who built it, how it works (mechanism), limitations, demo assets (og images, GIFs, video links). Use `rf sources repo owner/name --prod <dir>` and `rf sources og <url> --prod <dir>` for free facts and images.
- **B, reception and context:** news coverage, HN, Reddit, and X discussion (`rf sources hn "<query>"`), third-party tests or benchmarks, criticisms, competitors and alternatives, "why now", what creators already said (to find an *unclaimed* angle), and lesser-known facts.

Each writes into `<prod>/research/` and returns a compact brief.

- **Source screenshots (both researchers):** for every headline, post or quote you expect on screen, capture the real page.
  - Use Firecrawl `firecrawl_scrape` with `formats: ["screenshot"]`, `mobile: true` and `screenshotOptions: {fullPage: false}`.
  - Then run `rf shot <screenshot-url-or-file> --prod P --name <id> --find "<exact on-page phrase>"`.
  - If Firecrawl is unavailable, list the page URLs under `## Screenshots to capture` in your research file. The Creative Director captures them with agent-browser, asking the owner first unless `config.source_shots_browser` is true.
  - Quote the exact on-page wording so `--find` matches.

## facts.md format (single source for the script)

```
## Claims
| id | claim (exact, quotable) | source URL | date | confidence (high/med/low) | note |
| F1 | Strix has 45.2k GitHub stars | https://github.com/usestrix/strix | 2026-11-12 | high | API, live |

## Mechanism (how it works, plain language)
## Numbers worth showing
## Angles (3–5, each with why it would hook)
## Lesser-known / surprising facts
## Caveats / criticisms
## Visual assets available (paths in public/ or URLs)
## Do-not-say (unverified, contested, legally risky)
```

## Verification rules

- Numbers need a primary source or two independent secondary sources. Star counts come live from the API on production day.
- Dates must be absolute. Write "announced 10 Nov 2026", never "recently".
- Quotes must be verbatim with a link. Paraphrases are labelled as such.
- A source shown on screen is the real page: the highlighted words in the screenshot match facts.md word for word.
- Mark low-confidence claims as attribution ("the team claims…") or drop them.
- People and news: reputable outlets only, use the allegation language the outlet used, and include the counter-statement if one exists.
