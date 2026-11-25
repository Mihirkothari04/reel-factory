"""Record the owner's approval of the final script (owner hard rule, 2026-11-25).

usage: rf approve <prod_dir>

Run ONLY right after the owner explicitly approved the full final script in the conversation.
Writes P/approval.json with the script fingerprint; `rf voice` and `rf presenter` refuse to run
when the narration or soundbites change afterwards (approve again after the owner re-approves).
"""
import sys, time
from pathlib import Path
from common import load_json, log, save_json, script_sha


def main():
    prod = Path(sys.argv[1])
    sha = script_sha(load_json(prod / "storyboard.json"))
    save_json(prod / "approval.json", {"script_sha": sha, "approved_at": time.strftime("%Y-%m-%d %H:%M:%S")})
    log(prod, f"approve: owner approved the final script ({sha})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        a = {"narration": [{"text": "A."}], "soundbites": []}
        b = {"narration": [{"text": "B."}], "soundbites": []}
        assert script_sha(a) == script_sha(dict(a)) and script_sha(a) != script_sha(b)
        print("ok")
    else:
        main()
