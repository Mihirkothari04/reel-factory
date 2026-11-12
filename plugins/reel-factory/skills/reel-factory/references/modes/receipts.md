# Mode: Receipts, the evidence read-along (`receipts`)

**Identity:** the primary sources are the stage. Tweets, blog posts, papers, READMEs and fine print appear and get highlighted line by line as the voice reads them, building to an honest verdict. Trust is the product. (Creator 32' claim → test → verdict; Creator 05's synced tweet highlights; Creator 66's Karpathy bridge.)

## Construction
- **Real-page rule:** headlines, posts and quotes appear as `source` screenshots (`rf shot`) with the spoken words highlighted; `headline`/`quote` text cards only as a logged fallback.
- **Cards:** `quote` (posts: author, handle), `headline` (articles, blogs), `code` (README/config lines with `highlight`), `image` with `box` (screenshots), `bars` (third-party tests).
- **Highlight sync:** put the exact substring in `highlight`; build.py times each sweep to the first spoken key word. The VO must actually say (or closely paraphrase) the highlighted words.
- **Zoom-to-line:** for long pages use `walkthrough` with a screenshot `src` and `zoom`/`arrow` actions whose `say` is the word that triggers them.
- **Voice:** a skeptical journalist: "Does it hold up?", "Their own fine print says…", "Here's what they didn't say".
- **Captions:** `highlight` style, so captions and cards share the highlighter language.
- **Verdict:** a final `title` like a verdict pill ("3 s is real — on an M5 Pro").

## Beat template (claim-test, 40–60 s)
Claim hook (the boldest quotable line, on screen) → define the jargon → "Does it hold up?" (`punch`) → third-party evidence (`quote`/`bars`) → fine print (`code`/`headline` highlight) → honest verdict → optional CTA ("comment SOURCES for every link").

## Pitfalls
- Never fabricate a quote or a handle. Cards reproduce real text from facts.md (trim with "…" only).
- One source per card; trim long text to ≤ 30 words with the key phrase intact.
