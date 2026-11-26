"""Instagram comment -> follow-gated DM automation (free Cloudflare Worker; attention.md §4).

usage:
  rf dm setup                   deploy/update the worker from ~/.reel-factory/secrets/ig-dm.env (Cloudflare login needed once:
                                `npx wrangler login`); prints the Callback URL, Verify token and Privacy URL for the Meta app
  rf dm subscribe               subscribe the Instagram account to comments/messages webhooks (after Meta setup)
  rf dm arm <prod_dir>          create this reel's automation from storyboard.engagement (keyword, deliverable, link or hosted page)
  rf dm list | health | poll    show automations / account + last events / run the fallback poller now
  rf dm off <id|KEYWORD>        deactivate an automation

Secrets never pass through the chat: the owner fills ig-dm.env, setup uploads it as Worker secrets and keeps
the generated verify/admin tokens in ~/.reel-factory/secrets/ig-dm.local.json.
"""
import html, json, re, secrets, shutil, subprocess, sys, tempfile
from pathlib import Path
from common import HOME, PLUGIN, WIN, config, load_json, log, save_json

SECRETS = HOME / "secrets" / "ig-dm.env"
LOCAL = HOME / "secrets" / "ig-dm.local.json"
WDIR = HOME / "dm-worker"
NEEDED = ["IG_USER_ID", "IG_TOKEN", "IG_APP_SECRET", "META_APP_SECRET"]


def wrangler(*args, check=True):
    r = subprocess.run(["npx", "--yes", "wrangler@4", *args], cwd=WDIR, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", shell=WIN, timeout=300)
    if check and r.returncode:
        sys.exit(f"wrangler {' '.join(args[:2])} failed:\n{(r.stdout + r.stderr)[-1500:]}")
    return r.stdout + r.stderr


def read_env():
    vals = {}
    for line in SECRETS.read_text(encoding="utf-8").splitlines() if SECRETS.exists() else []:
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"')
    miss = [k for k in NEEDED if not vals.get(k)]
    if miss:
        sys.exit(f"fill {', '.join(miss)} in {SECRETS} first (Meta app guide), then run again")
    return vals


def setup():
    vals = read_env()
    WDIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PLUGIN / "dm-worker" / "worker.mjs", WDIR / "worker.mjs")
    if "You are not authenticated" in wrangler("whoami", check=False):
        sys.exit("Cloudflare login needed once: run `npx wrangler login` (browser -> Allow), then `rf dm setup` again")
    st = load_json(LOCAL) if LOCAL.exists() else {}
    st.setdefault("VERIFY_TOKEN", secrets.token_urlsafe(18))
    st.setdefault("ADMIN_TOKEN", secrets.token_urlsafe(32))
    if not st.get("kv_id"):
        out = wrangler("kv", "namespace", "create", "reel-factory-dm")
        st["kv_id"] = re.search(r'"?id"?\s*[:=]\s*"([0-9a-f]{32})"', out).group(1)
    handle = (config().get("dm") or {}).get("handle") or (config().get("brand") or {}).get("handle") or ""
    (WDIR / "wrangler.toml").write_text(
        'name = "reel-factory-dm"\nmain = "worker.mjs"\ncompatibility_date = "2026-11-01"\nworkers_dev = true\n\n'
        f'[vars]\nHANDLE = "{handle.lstrip("@")}"\n\n[[kv_namespaces]]\nbinding = "DM"\nid = "{st["kv_id"]}"\n\n'
        '[triggers]\ncrons = ["*/2 * * * *"]\n', encoding="utf-8")
    out = wrangler("deploy")
    st["endpoint"] = re.search(r"https://[\w.-]+\.workers\.dev", out).group(0)
    save_json(LOCAL, st)
    sec = {"IG_TOKEN": vals["IG_TOKEN"], "IG_USER_ID": vals["IG_USER_ID"], "VERIFY_TOKEN": st["VERIFY_TOKEN"], "ADMIN_TOKEN": st["ADMIN_TOKEN"],
           "APP_SECRETS": ",".join(v for v in (vals.get("IG_APP_SECRET"), vals.get("META_APP_SECRET")) if v)}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(sec, f)
    try:
        wrangler("secret", "bulk", f.name)
    finally:
        Path(f.name).unlink()
    print(f"worker live: {st['endpoint']}\n\nPaste into the Meta app:\n  Callback URL : {st['endpoint']}/webhook\n"
          f"  Verify token : {st['VERIFY_TOKEN']}\n  Privacy URL  : {st['endpoint']}/privacy\n  Data deletion: {st['endpoint']}/data-deletion")


def call(method, route, body=None):
    import requests
    st = load_json(LOCAL) if LOCAL.exists() else sys.exit("run `rf dm setup` first")
    r = requests.request(method, f"{st['endpoint']}/admin/{route}", json=body, timeout=60,
                         headers={"authorization": f"Bearer {st['ADMIN_TOKEN']}"})
    try:
        d = r.json()
    except ValueError:
        d = {"error": r.text[:300]}
    if r.status_code >= 400:
        sys.exit(f"{route}: HTTP {r.status_code} {d}")
    return d


def page_html(title, body):
    """plain text / light markdown -> a small mobile page (headings, bullets, links)"""
    out = []
    for ln in body.splitlines():
        t = html.escape(ln.strip())
        t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', t)
        t = re.sub(r"(?<![\"'>])(https?://[^\s<]+)", r'<a href="\1">\1</a>', t)
        out.append(f"<h2>{t[3:]}</h2>" if t.startswith("## ") else f"<li>{t[2:]}</li>" if t.startswith(("- ", "* ")) else f"<p>{t}</p>" if t else "")
    return (f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>'
            '<style>body{font:16px/1.6 system-ui,sans-serif;max-width:680px;margin:32px auto;padding:0 16px;color:#16202a;background:#f7f9fa}'
            f'h1{{font-size:22px}}h2{{font-size:18px;margin-top:24px}}a{{color:#0b6e75}}</style><h1>{html.escape(title)}</h1>' + "\n".join(out))


def arm(prod):
    sb = load_json(prod / "storyboard.json")
    e = sb.get("engagement") or {}
    if not e.get("keyword"):
        sys.exit("storyboard.engagement.keyword is empty: this reel has no comment-keyword CTA")
    title = e.get("deliverable") or "the full breakdown"
    a = {"id": re.sub(r"[^a-z0-9-]", "", prod.name.lower())[:48], "keyword": e["keyword"].strip().upper(),
         "aliases": e.get("keyword_aliases", []), "deliverable_title": title[:1].upper() + title[1:],
         "deliverable_text": e.get("dm_deliverable_text", f"As promised: {title}. Thanks for following!"),
         "link_title": e.get("link_title", "Open"), "opener": e.get("dm_opener"),
         "public_replies": e.get("public_replies") or ["Sent! Check your DMs 📩", "Just sent it, check your requests 👀", "In your DMs now 🚀"]}
    if e.get("link"):
        a["link"] = e["link"]
    else:  # host the deliverable: the owner-written page, else caption + sources
        body = e.get("deliverable_page") or "\n".join([sb.get("caption", ""), "", "## Sources", *[f"- {s}" for s in sb.get("sources_in_caption", [])]])
        a["page"] = page_html(a["deliverable_title"], body)
    a = {k: v for k, v in a.items() if v is not None}
    d = call("PUT", "automations", a)
    log(prod, f"dm: armed keyword {d['keyword']} -> {d.get('link')}")
    print(json.dumps({k: d.get(k) for k in ("id", "keyword", "link")}, indent=2))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "setup":
        setup()
    elif cmd == "subscribe":
        print(json.dumps(call("POST", "subscribe"), indent=2))
    elif cmd == "arm":
        arm(Path(sys.argv[2]))
    elif cmd == "list":
        print(json.dumps([{k: a.get(k) for k in ("id", "keyword", "active", "link")} for a in call("GET", "automations")], indent=2))
    elif cmd == "off":
        call("DELETE", f"automations?id={sys.argv[2]}")
        print("deactivated", sys.argv[2])
    elif cmd == "health":
        print(json.dumps(call("GET", "health"), indent=2, ensure_ascii=False))
    elif cmd == "poll":
        print(json.dumps(call("POST", "poll")))
    elif cmd == "--selftest":
        h = page_html("T", "## Sources\n- https://a.b/c\n[x](https://d.e)")
        assert '<a href="https://a.b/c">' in h and '<a href="https://d.e">x</a>' in h and "<h2>Sources</h2>" in h
        print("ok")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
