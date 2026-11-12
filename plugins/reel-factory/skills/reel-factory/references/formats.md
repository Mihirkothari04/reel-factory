# Formats: 11 story skeletons observed in the corpus

A skeleton is the **order of beats**; the creation mode (`modes/INDEX.md`) is **how the reel is built**. Choose the mode first, then a skeleton the mode supports (compatibility table in `modes/INDEX.md`). Record the skeleton id in `storyboard.json` as `"skeleton"`.

Pick **one** per reel from the topic shape, not habit. Timings assume about 200 wpm. Each beat lists the scene types that fit it.

## Decision guide

| Topic shape | Format |
|---|---|
| One new tool, repo, skill, or feature | **1 Tool spotlight** |
| Several tools solving one job, or "N best…" | **2 Listicle** |
| "How to do X" with a clear sequence | **3 Step tutorial** |
| A launch or event with drama or stakes (company, people, policy) | **4 News explainer** |
| A bold claim worth testing (speed, accuracy, "beats X") | **5 Claim → test → verdict** |
| A concept with several layers or parts that build on each other | **6 Problem-ladder story** |
| A confusing field to simplify | **7 Framework reduction** |
| Comparing many options on one axis (money, speed, price) | **8 Tier list / ranking** |
| Two to four competing products | **9 Comparison + verdict** |
| A company did X and the internet answered within days | **10 Action → reaction** |
| Several tools that only make sense in a build order | **11 Stack roadmap** |

---

## 1. Tool spotlight `spotlight` (35–45 s)

| Beat | Time | Content | Scenes |
|---|---|---|---|
| Hook | 0–3 s | Discovery or brand-recency claim + outcome | `title` (kinetic) or `image`/`terminal` showing the result |
| Credibility | 3–7 s | Name it, who built it, stars, free/open-source | `repo`, `stat` |
| Mechanism | 7–22 s | How it works in 2–4 visual steps | `flow`, `terminal`, `chat`, `hub` |
| Re-hook | ~50% | "But here's the smart part…" + the most surprising capability | `punch` → `versus`/`quote` |
| Proof | | Number, benchmark, third-party quote | `stat`, `bars`, `quote` |
| Caveat | | Limitation or who it's not for | `title` with `_muted_` sub |
| CTA | last 3–4 s | Comment keyword / save | `cta` |

## 2. Listicle "N things" `listicle` (45–60 s; 3–7 items)

Hook with N and the promise → **preview grid** (`grid` of all N, an open loop) → items 1…N (`item` with i/N, plus one demo scene each) → restraint advice ("don't install all of them — pick the one that fits your week") → CTA with a **withheld bonus** ("…and I'll send you all 7, plus 3 more for…"). Order items by escalating wow; the strongest goes second-to-last.

## 3. Step tutorial `tutorial` (40–60 s)

Before→after hook ("make your site go from *this* to *this*") → Step 1…5, each spoken as "Step N" with one action and one visual (`terminal`, `chat`, `image` + `box`) → recap of **why** it works ("now Claude has the tools, the guidance, and the reference") → CTA "comment SETUP for the commands".

## 4. News explainer `news` (50–80 s)

"Breaking / just announced" hook with the stake → who and what (`quote` of the announcement, `image` of the headline) → chronology → **"Now here's where it gets crazy"** escalation → **"But here's the catch"** balance → so-what for the viewer ("this was never just about X") → close on the stakes or a question. Cite outlets on screen. Real-people rules apply.

## 5. Claim → test → verdict `claim-test` (40–55 s)

Claim hook ("a tiny model labels a 50-min interview in 3 seconds") → define the jargon → **"Does it hold up?"** (`punch`) → third-party test (`quote` + `bars`) → the fine print (`quote` highlight) → honest verdict (`title`: "3 s is real — on an M5 Pro"). Optional CTA.

## 6. Problem-ladder story `problem-ladder` (60–120 s)

Give a named protagonist (a product or bot, *not* a real person) a goal. Each beat is **failure → fix (concept n)**. Escalate the stakes. A cumulative stack (`list` with `check`, or `flow`) grows as the progress bar. End with a **callback twist** to the first failure. This is the best format in the corpus for teaching 5–8 concepts.

## 7. Framework reduction `framework` (40–55 s)

"There are only N problems / layers / rules in X" → numbered buckets (each a `title` with a `kicker` "01 / 05" plus a supporting visual) → summary grid or `list` (the screenshot frame) → question CTA "which one first? comment a number" (seeds the next reel).

## 8. Tier list / ranking `tier-list` (50–90 s)

Hook with the ranking axis and expectation violation ("…the results are not what you'd expect") → lowest tier first with a score (`stat` with suffix "/10") → … → top tier last → the takeaway. Built for debate in the comments.

## 9. Comparison + verdict `comparison` (40–60 s)

Hook on the launch or the rivalry → what each does (`versus`, `bars` on price/speed) → reasons (2–3) → caveat → "my pick" (`punch`) → question CTA "which would you use?".

## 10. Action → reaction `action-reaction` (35–50 s)

"Company did X → within 24 hours someone built the opposite / the community did Y" (Creator 52' watermark remover; the Vercel-vs-Fable irony). Hook with the reaction's punchline → the action (headline or quote card, dated) → the reaction (repo, post, numbers) → why it matters (who wins, what it says about the field) → stance or question CTA. Tribal framing ("developers are savage") is allowed; recommending misuse tools is not.

## 11. Stack roadmap `stack-roadmap` (25–60 s)

"Here's the exact order": tools placed along a build pipeline (UI → design → front-end → back-end → hosting → shortcut), each one step (Creator 34; the Creator 67 "Claude just killed web designers" setup: install A → add B → connect C → just describe). A `flow` of the whole stack first, then one beat per stage, then the result. Stronger than a random list because the order is the insight.

---

## Mapping topic → art direction (default; override for contrast)

| Topic mood | Theme | Caption style |
|---|---|---|
| Developer tools, CLIs, agents, security | `terminal` or `night` | `pill` or `caps` |
| Design, creative tools, writing, careers | `paper` | `serif` |
| Listicles, resources, product roundups | `swiss` | `highlight` |
| News, launches, big-tech, policy | `signal` | `pill` |
| Explainers, frameworks, stories | `paper` or `night` | `serif` or `pill` |
