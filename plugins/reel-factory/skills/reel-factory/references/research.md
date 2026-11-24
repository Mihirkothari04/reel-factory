# Research protocol (trend-scout, topic-researcher, fact-checker)

## Trend discovery (Mode 1)

1. **Hard signals:** `python "${CLAUDE_PLUGIN_ROOT}/scripts/rf.py" trends --days 7 --out <prod_root>/trends.json` covers GitHub new repos by star velocity, GitHub trending (daily and weekly), Hacker News, Hugging Face trending models, and Lobsters, with spam filtering and cross-source convergence scoring.
1b. **Newsletter leads:** `rf news ingest` (picks up any new daily `*_AI-Tech-Newsletters.zip` from ~/Downloads; no-op when nothing is new), then `rf news leads --days 3`. It lists stories from the user's subscribed AI/tech newsletters, ranked by how many **distinct newsletters** covered each one across days, with tracking links already resolved to the real outlet or official URL. Several newsletters on one story counts as convergence for *momentum*. The rows are newsletter claims and only leads: open the real link and confirm the date and facts before scoring *verifiability*.
2. **Soft signals (web search):** AI and tech news from the last 7 days (major-lab launches, model releases, big open-source drops), what AI creators are posting on Instagram, TikTok, YouTube Shorts, and X, Reddit discussions (r/LocalLLaMA, r/ClaudeAI, r/ChatGPT, r/singularity), and Product Hunt top launches. Run several searches with different phrasings and include the current month and year.
3. **Score each candidate 1–5** on: *novelty* (≤14 days old; ≤7 is better), *momentum* (stars/day, HN points, number of independent sources: **convergence is the strongest signal**), *audience value* (free, saves time or money, solves a felt pain, wow outcome), *visualisability* (can we *show* it?), *verifiability* (primary source exists), *saturation risk* (already covered to death? find a fresh angle or skip), *brand safety*.
4. Return the **top 3** with evidence links and a recommended pick plus format. The orchestrator decides without asking the user.

Skip: spam or malware-lure repos (fake stars, "Pro 2026 standalone installer"), crypto pumps, unverified rumours, anything requiring login to show, and scandal stories with no reliable outlet.

## Topic research (both modes)

**Why the workflow is built like this.** Generic web search plus a fetch tool that gets 403s from official sites, X and Reddit made whatever loaded easily (one trade site) the source of everything. Information originates and gains attention on official posts, company newsrooms, famous people's X accounts, big mastheads, Reddit, GitHub and papers. `rf intel` reaches those through official, free access paths, and the evidence ledger makes source quality measurable.

1. **Source map.** The Creative Director picks the topic type in `sources.json → routing` (big-lab launch, open-source repo, paper/model, policy, viral moment, business tool) and passes the source types plus the relevant `rf intel handles` and subreddits to the researchers.
2. Run two `topic-researcher` agents **in parallel**:
   - **A, Origin Hunter:**
     - official newsroom feeds (`rf intel feeds --tier official`);
     - the official X posts of the company, CEO, founders and researchers (`rf intel handles`, then `rf intel x <url>`: text, date, verified, likes, replies);
     - repos (`rf intel repo`: stars, star velocity, releases, contributors), papers (`rf intel papers`), docs and help pages (`rf intel read`).
     - Gather exact numbers, mechanism, limitations and demo assets.
     - Start with `rf news grep "<topic keywords>" --days 14`. The user's newsletters often name the primary links (official blog, changelog, repo, paper), already resolved. Follow each one to the original. Never ledger a newsletter as the source for a claim.
   - **B, Coverage & Community:**
     - press breadth (`rf intel news`: Google News across hundreds of publishers; prefer press-tier mastheads);
     - reactions with engagement (`rf intel reddit`, `rf intel hn`, notable X posts);
     - competitors, criticisms, third-party tests, "why now", and how other creators covered it, to find the *unclaimed* angle.
3. **Ledger gate.** `rf intel score --prod <dir>` ranks sources by tier, originality, engagement, recency and corroboration. Before scripting, fix every warning:
   - every key claim needs an original;
   - no publisher may supply more than 30 % of claims;
   - at least one community signal;
   - no lead-only source on screen.

   Popularity ranks discovery; verification decides truth.
4. `rf sources repo|og` still fetch og-images for visuals.

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

- Every claim traces to a ledger entry (`research/sources.json`) with publisher, date and engagement. For announcements, the **original** (official post or page, the CEO's X post, the repo or the paper) is the source; press coverage corroborates it.
- TechCrunch and other `onscreen_ok:false` sites are research leads only: follow them to the original and never show them on screen.
- Numbers need a primary source or two independent secondary sources. Star counts come live from the API on production day.
- Dates must be absolute. Write "announced 10 Nov 2026", never "recently".
- Quotes must be verbatim with a link. Paraphrases are labelled as such.
- A source shown on screen is the real page: the highlighted words in the screenshot match facts.md word for word.
- Mark low-confidence claims as attribution ("the team claims…") or drop them.
- People and news: reputable outlets only, use the allegation language the outlet used, and include the counter-statement if one exists.
