# Mode: Newsroom Brief (`newsroom`)

**Identity:** it looks and sounds like news. A persistent BREAKING banner, real headlines highlighted as they are read, a fast chronology, escalation, balance, stakes. (Creator 54's big-tech CEO scandal story; Creator 02's ticker; Creator 12's red news banner; Creator 36's launch takes.)

## Construction
- **Real-page rule:** headlines, posts and quotes appear as `source` screenshots (`rf shot`) with the spoken words highlighted; `headline`/`quote` text cards only as a logged fallback.
- **Theme:** `signal` (condensed caps display, red accent); captions `pill`.
- **Banner:** `meta.banner = {"kicker": "BREAKING", "text": "Cloudflare ships a *browser* for AI agents"}`. It stays the whole reel (the stage shrinks to make room). Kickers: BREAKING, JUST IN, UPDATE, EXPLAINED.
- **Evidence cards:** `headline` (outlet, date, headline, `highlight` phrases; build.py syncs each sweep to the moment the VO says it), `quote` for statements, `image` for og/press images, `stat` for the key number, `punch` stamps on the turns.
- **Chronology:** date kickers on `title` ("12 NOV"), or a `list` timeline.
- **Audio:** tense pulse bed (prompt: "tense minimal news pulse, 120 bpm, low synth, ticking hi-hat, no vocals"), musicVolume 0.34; impacts on stamps.
- **Pacing:** the fastest narrated mode, 1.2–3.0 s per scene (QA enforces).

## Beat template (news, 35–60 s; attention.md)
Hook = the newest development told through its most human or surprising detail, 12 words or fewer ("'Elon, please hire Jensen,' one tweet said." / "Nvidia's staff packed the lobby cheering. Jensen is back."), real face or post on screen by 0.8 s → who and what (headline card) → chronology, one beat per 5–8 s, each ending on an open loop ("Everyone thought that was the worst of it. It wasn't.") → **"Now here's where it gets crazy"** (re-hook: the escalation) + a mid-reel question to the viewer → **"But here's the catch"** (what isn't proven, the counter-view) → so-what for the viewer, in a scale they feel (config audience) → callback to the hook + a one-line CTA (a follow promise for the next development). Facts that don't fit 60 s go into the caption.

## Truth rules (stricter here)
- Every claim maps to an outlet in facts.md, and the outlet is on screen.
- People: "reports say", "allegedly", "according to"; no generated likenesses; prefer documents, logos, maps, headlines.
- Absolute dates. Unconfirmed points go inside the "catch" beat.
