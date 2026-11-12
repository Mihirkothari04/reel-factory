# Mode: Screen Walkthrough (`walkthrough`)

**Identity:** show, don't tell. One app window stays on stage while a cursor glides, types the exact prompt and clicks, big arrows point at what matters, and the camera zooms to every action. "Step 1… Step 5", before → after. This is the grammar viewers expect from modern demos (Recordly's own features: cursor smoothing, zoom on click, click bounce, styled frame). (Humanize-AI tutorial; Creator 22' Framer steps; Creator 11' cron hack; the Search Console creator's yellow arrows; ChatGPT slash commands typed live.)

## Construction
- **Main scene:** `walkthrough`: `url` (title bar), `src` (screenshot/mock in `public/img/`) or `rows` (rebuilt app text), and `actions` (coordinates 0..1 of the window content; `say` = the VO word that triggers the action, converted to `at` by build.py; clicks and typing get SFX automatically):
  - `{"type":"move","x":0.3,"y":0.5,"say":"open"}`
  - `{"type":"type","x":0.08,"y":0.6,"w":0.84,"text":"/mockup create mockup on a floating phone","say":"type"}`
  - `{"type":"click","x":0.85,"y":0.75,"say":"submit"}`
  - `{"type":"arrow","x":0.42,"y":0.31,"from":"top","say":"sitemap"}` (big yellow pointer, bobbing; `until` to remove it)
  - `{"type":"zoom","x":0.5,"y":0.6,"scale":1.6,"say":"result"}`
  - `{"type":"box","x":0.1,"y":0.2,"w":0.5,"h":0.1,"say":"indexed"}`
- **Step signposts:** spoken "Step N" + `label: "STEP 2 / 5"`, or `meta.progress` with step names (bar or chips).
- **Supporting scenes:** `chat` (prompt → answer), `terminal` (install), `code` (config), before/after as `versus` or two `image`s.
- **Visual supply:** official screenshots/og images (`RF sources og`) and rebuilt UI. Mocks must never impersonate a real product's UI as if it were a recording. With `browser_capture: true` (agent-browser; public read-only pages; ask first) real screenshots can be captured.
- **Open loop:** "stay until the end, I'll give you the tool that does this automatically" (2 corpus reels): only if the end really delivers.
- **Recap:** one sentence on *why* it works ("now Claude has the tools, the guidance and the reference").
- **CTA:** "comment SETUP for the full guide / prompt / PDF".

## Beat template (tutorial, 40–55 s)
Before → after hook (or the result first: the heatmap, the 0% detector) → Step 1…N (4–8 s each, inside one or two walkthrough scenes) → recap → CTA.

## Pitfalls
- Tiny UI: zoom to the action (scale 1.5–2.0) or point an arrow every time something happens.
- Coordinates guessed blind: open the screenshot, find the input or button, then set x/y.
- Coordinates are fractions of the **image you pass in `src`**; the window takes that image's aspect and shrinks to fit the stage, so nothing is cropped. Crop big desktop shots to the part you talk about first (text must be legible at phone size).
