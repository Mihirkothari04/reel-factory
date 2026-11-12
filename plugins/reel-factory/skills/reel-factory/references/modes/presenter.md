# Mode: Presenter + Board (`presenter`)

**Identity:** a face carries trust and personality; the board above it carries proof. The largest family in the corpus (Creator 37 ×7, Creator 22 ×6, Creator 05 ×6, Creator 12 ×4, and 11 of batch-02's 17 new reels). The face returns full-frame for emphasis and for the CTA push-in.

## Two ways to get a presenter
1. **Your own footage (free, best).** The Creative Director writes the script, the user records it (phone at face height, quiet room or lav, ~200 wpm, first word = the hook, no "hey guys"), then `RF voice P --footage clip.mp4`. The clip's audio becomes the VO, script words are aligned with Whisper, and the face is never time-cut (cutting would desync it). This is the one step that waits for the user: say exactly what to record (the script, framing, length) and stop until the clip exists.
2. **AI avatar.** `config.avatar.enabled` + a consented portrait (`avatar.image`), then `RF avatar P` (Creatify Aurora; credit-heavy, so state the cost first). "Good enough" is enough (Creator 58): the board carries the content.
Neither available → fall back to `kinetic`, keeping the first-person voice.

## Construction
- **Layout:** `split-avatar`: board y 80–1030 (stage scale 0.8), presenter below, captions at the seam (y 1010).
- **Board:** kinetic scene types, but fewer words (the face says them): logos, one number, one screenshot, one diagram per beat.
- **Script voice:** first person ("I tried this", "my pick"), opinions and verdicts. This mode carries opinion, ranking and tier lists that faceless reels can't.
- **Variants seen:** full-frame head with floating cards (Creator 55, Creator 26, the legal-checklist creator); circular "portal" frame (Creator 22); weatherman (standing in front of a wall display); webcam in black letterbox with a growing list beside the face. All need footage; with an avatar, use split.
- **Overlay devices that work on a face:** persistent title sticker; ToC chips (`meta.progress.style: "chips"`); one huge stat; 3D-emoji or reaction stickers as punctuation every ~4 s (original or licensed art only, never movie or TV frames).

## Beat template (listicle, 45–60 s)
Hook on the face + board headline → board-heavy middle (each item = one board card; the face returns between items for a one-line reaction) → "my pick" on the face → CTA push-in close-up.

## Pitfalls
- Board text sized for full frame: in split layout it renders at 0.8× and must be shorter.
- Footage that starts late: the first word must land ≤ 0.3 s in (trim the clip).
