"""Show or change reel-factory preferences (~/.reel-factory/config.json).

usage: rf config                      print config
       rf config set brand.handle @me  set a dotted key (JSON values accepted: true, 3, null, "x")
"""
import json, sys
from common import HOME, config, save_json

cfg = config()
if len(sys.argv) >= 4 and sys.argv[1] == "set":
    key, raw = sys.argv[2], " ".join(sys.argv[3:])
    try:
        val = json.loads(raw)
    except json.JSONDecodeError:
        val = raw
    node = cfg
    *path, last = key.split(".")
    for k in path:
        node = node.setdefault(k, {})
    node[last] = val
    save_json(HOME / "config.json", cfg)
print(json.dumps(cfg, indent=2))
