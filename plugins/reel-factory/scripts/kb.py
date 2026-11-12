"""Knowledge-base housekeeping for /reel-learn.

usage: rf kb where              -> prints the WRITABLE plugin source dir (the knowledge base) and the installed copy
       rf kb bump [minor|patch] -> bump plugin.json + marketplace version, then refresh the installed plugin

The installed plugin is a cached COPY (~/.claude/plugins/cache/...). Knowledge-base edits must go to the source folder
the local marketplace points at; after editing, `rf kb bump` makes the next Claude Code session load them.
"""
import json, shutil, subprocess, sys
from pathlib import Path
from common import PLUGIN, load_json, save_json

CC = Path.home() / ".claude" / "plugins"


def source_dir():
    """plugin source = the directory marketplace that lists reel-factory (falls back to the running copy)"""
    km = CC / "known_marketplaces.json"
    if km.exists():
        for name, m in load_json(km).items():
            src = (m.get("source") or {})
            if src.get("source") == "directory":
                root = Path(src["path"])
                mp = root / ".claude-plugin" / "marketplace.json"
                if mp.exists():
                    for p in load_json(mp).get("plugins", []):
                        if p.get("name") == "reel-factory":
                            return name, (root / p["source"]).resolve()
    return None, PLUGIN


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "where"
    market, src = source_dir()
    if cmd == "where":
        if not market:
            print(f"no writable source: installed from a remote marketplace (running copy: {PLUGIN}).\n"
                  "Plugin updates replace that copy, so /reel-learn must not edit it. To evolve your own version:\n"
                  "  git clone <the reel-factory repo> && claude plugin marketplace add ./reel-factory\n"
                  "  claude plugin install reel-factory@reel-factory --scope user\n"
                  "Until then, lessons go to ~/.reel-factory/learnings.md (read on every run).")
            sys.exit(2)
        print(f"source (edit here): {src}\nmarketplace: {market}\nrunning copy: {PLUGIN}")
        return
    if cmd == "bump":
        part = sys.argv[2] if len(sys.argv) > 2 else "minor"
        pj = src / ".claude-plugin" / "plugin.json"
        meta = load_json(pj)
        a, b, c = map(int, meta["version"].split("."))
        meta["version"] = f"{a}.{b + 1}.0" if part == "minor" else f"{a}.{b}.{c + 1}"
        save_json(pj, meta)
        modes = src / "skills" / "reel-factory" / "references" / "modes" / "modes.json"
        if modes.exists():
            m = load_json(modes); m["version"] = meta["version"]; save_json(modes, m)
        print(f"version -> {meta['version']}")
        exe = shutil.which("claude")
        if exe and market:
            for args in (["plugin", "marketplace", "update", market], ["plugin", "update", f"reel-factory@{market}"]):
                r = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
                print(" ".join(args), "->", (r.stdout + r.stderr).strip()[-300:])
        print("restart Claude Code (or start a new session) to load the new version; then run `rf setup` once to sync the runtime engine.")
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
