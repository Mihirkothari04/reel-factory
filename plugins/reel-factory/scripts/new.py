"""Create a production folder.

usage: rf new "<working title>" [--root DIR]
Root: --root, else config.output_dir, else <current dir>/reel-productions. Prints the absolute production path.
"""
import argparse, datetime as dt, os
from pathlib import Path
from common import config, slugify

ap = argparse.ArgumentParser()
ap.add_argument("title")
ap.add_argument("--root")
a = ap.parse_args()
root = Path(a.root or config().get("output_dir") or Path(os.getcwd()) / "reel-productions")
base = root / f"{dt.date.today().isoformat()}-{slugify(a.title)}"
p, i = base, 2
while p.exists():
    p, i = Path(f"{base}-{i}"), i + 1
for d in ["research", "public/img", "out"]:
    (p / d).mkdir(parents=True, exist_ok=True)
(p / "log.md").write_text(f"# {a.title}\n\n", encoding="utf-8")
print(p.resolve())
