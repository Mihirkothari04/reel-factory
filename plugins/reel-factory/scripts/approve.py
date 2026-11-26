"""Record the owner's approval of the final script (owner hard rule, 2026-11-25).

usage: rf approve <prod_dir> [--long "<why this reel must run past the mode's length>"]

Run ONLY right after the owner explicitly approved the full final script in the conversation.
Writes P/approval.json with the script fingerprint; `rf voice` and `rf presenter` refuse to run
when the narration or soundbites change afterwards (approve again after the owner re-approves).

Before recording, it refuses scripts that break the attention rules (references/attention.md, 2026-11-26):
 - estimated length over the mode's range (+10 %) unless --long gives the story-escalation reason;
 - a missing post kit (storyboard.engagement: caption question, pinned comment, share line, follow promise,
   3 story frames; a comment keyword needs its deliverable).
Show the owner the estimated length and the post kit together with the script.
"""
import re, sys, time
from pathlib import Path
from common import load_json, log, save_json, script_sha

WPS = 3.3  # spoken words per second incl. pauses (corpus 215 wpm; our presenter takes ran ~200)


def est_seconds(sb):
    words = sum(len(p.get("text", "").split()) for p in sb.get("narration") or [])
    sbs = sum(float(s.get("dur", 0)) for s in sb.get("soundbites") or [])
    return round(words / WPS + 0.4 * max(0, len(sb.get("narration") or []) - 1) + sbs, 1)


def engagement_issues(sb):
    e = sb.get("engagement") or {}
    bad = [f"engagement.{k} missing" for k in ("caption_question", "pinned_comment", "share_line", "follow_promise") if not str(e.get(k, "")).strip()]
    if e.get("caption_question") and "?" not in e["caption_question"]:
        bad.append("engagement.caption_question is not a question")
    if len(e.get("stories") or []) < 3:
        bad.append("engagement.stories needs 3 frames (teaser+poll, reel share, follow-up)")
    if e.get("keyword") and not e.get("deliverable"):
        bad.append("engagement.keyword without a real deliverable")
    return bad


def first_sentence_words(sb):
    n = sb.get("narration") or []
    return len(re.split(r"(?<=[.!?])\s", n[0].get("text", ""))[0].split()) if n else 0


def main():
    prod = Path(sys.argv[1])
    long_why = sys.argv[sys.argv.index("--long") + 1] if "--long" in sys.argv else ""
    sb = load_json(prod / "storyboard.json")
    from build import mode_spec
    lo, hi = (mode_spec((sb.get("meta") or {}).get("mode")).get("defaults") or {}).get("length", [15, 60])
    est, stop = est_seconds(sb), []
    if est > hi * 1.1 and not long_why:
        stop.append(f"estimated {est}s > mode max {hi}s: cut the beats that don't escalate (facts go to the caption), "
                    f"or pass --long \"<story-escalation reason>\"")
    if sb.get("narration"):
        stop += engagement_issues(sb)
    if stop:
        sys.exit("STOP (attention rules, references/attention.md):\n - " + "\n - ".join(stop))
    if first_sentence_words(sb) > 14:
        print(f"warn: first sentence is {first_sentence_words(sb)} words; the stake should land in <=3 s (~12 words)")
    sha = script_sha(sb)
    save_json(prod / "approval.json", {"script_sha": sha, "approved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                       "est_seconds": est, **({"long_reason": long_why} if long_why else {})})
    log(prod, f"approve: owner approved the final script ({sha}), est {est}s" + (f", long: {long_why}" if long_why else ""))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        a = {"narration": [{"text": "A."}], "soundbites": []}
        b = {"narration": [{"text": "B."}], "soundbites": []}
        assert script_sha(a) == script_sha(dict(a)) and script_sha(a) != script_sha(b)
        assert est_seconds({"narration": [{"text": " ".join(["w"] * 33)}], "soundbites": [{"dur": 5}]}) == 15.0
        assert len(engagement_issues({})) == 5
        ok = {"engagement": {"caption_question": "Yes or no?", "pinned_comment": "x", "share_line": "x", "follow_promise": "x",
                             "stories": [1, 2, 3], "keyword": "AI", "deliverable": "links"}}
        assert engagement_issues(ok) == []
        assert first_sentence_words({"narration": [{"text": "Java is broken. Not some app."}]}) == 3
        print("ok")
    else:
        main()
