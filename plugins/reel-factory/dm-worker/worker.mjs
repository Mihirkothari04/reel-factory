// reel-factory: Instagram comment -> follow-gated DM automation on a free Cloudflare Worker.
//
// Flow (Meta's official Instagram API with Instagram Login; references/attention.md §4):
//   1. Someone comments a reel's keyword. A webhook arrives, or the cron poller (fallback) finds the comment.
//   2. One private reply to that comment: the opener plus an "I'm following ✅" quick-reply button.
//      Meta allows one private reply per comment, within 7 days.
//   3. Tapping the button (or replying DONE / the keyword) opens the 24 h messaging window, and we get an IGSID.
//   4. GET /{IGSID}?fields=is_user_follow_business. If they follow, send the deliverable (link button); if not, send the follow prompt again.
// Storage: KV binding DM holds the automations, dedupe keys, cursors, the refreshed token and a short event log.
// Secrets: IG_TOKEN, IG_USER_ID, APP_SECRETS (comma list), VERIFY_TOKEN, ADMIN_TOKEN. Var: HANDLE.

const G = "https://graph.instagram.com/v26.0";
const DAY = 86400;

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/webhook" && req.method === "GET") {
      const p = url.searchParams;
      return p.get("hub.mode") === "subscribe" && p.get("hub.verify_token") === env.VERIFY_TOKEN
        ? new Response(p.get("hub.challenge")) : new Response("forbidden", { status: 403 });
    }
    if (url.pathname === "/webhook" && req.method === "POST") {
      const raw = await req.text();
      if (!(await validSignature(raw, req.headers.get("x-hub-signature-256"), env))) return new Response("bad signature", { status: 401 });
      ctx.waitUntil(handleWebhook(env, JSON.parse(raw)));
      return new Response("ok");
    }
    if (url.pathname === "/privacy") return html(PRIVACY(env));
    if (url.pathname === "/data-deletion") return html(DELETION(env));
    if (url.pathname.startsWith("/d/")) {  // hosted deliverable pages (rf dm arm --body)
      const page = await env.DM.get("page:" + url.pathname.slice(3));
      return page ? html(page) : new Response("not found", { status: 404 });
    }
    if (url.pathname.startsWith("/admin/")) {
      if (req.headers.get("authorization") !== `Bearer ${env.ADMIN_TOKEN}`) return new Response("unauthorized", { status: 401 });
      return admin(req, url, env);
    }
    return new Response("reel-factory dm worker");
  },
  async scheduled(_evt, env, ctx) {
    ctx.waitUntil(cron(env));
  },
};

// ---------- webhook ----------
export async function handleWebhook(env, body) {
  if (body.object !== "instagram") return;
  const last = Number(await env.DM.get("last_webhook_at") || 0);
  if (Date.now() - last > 600e3) await env.DM.put("last_webhook_at", String(Date.now()));  // poller backs off while webhooks flow
  for (const e of body.entry || []) {
    for (const ch of e.changes || []) if (ch.field === "comments" && ch.value) await onComment(env, ch.value);
    for (const m of e.messaging || []) await onMessage(env, m);
  }
}

export async function validSignature(raw, header, env) {
  if (!header || !header.startsWith("sha256=")) return false;
  for (const secret of String(env.APP_SECRETS || "").split(",").map(s => s.trim()).filter(Boolean)) {
    const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw)));
    if ("sha256=" + [...sig].map(b => b.toString(16).padStart(2, "0")).join("") === header) return true;
  }
  return false;
}

// ---------- automations ----------
async function automations(env) {
  return JSON.parse(await env.DM.get("automations") || "[]");
}

const norm = s => String(s || "").toLowerCase().normalize("NFKC");

export function match(autos, text, mediaId) {
  const t = " " + norm(text).replace(/[^\p{L}\p{N}]+/gu, " ") + " ";
  return autos.find(a => a.active !== false && (!a.media_id || a.media_id === mediaId) &&
    [a.keyword, ...(a.aliases || [])].some(k => k && t.includes(" " + norm(k).replace(/[^\p{L}\p{N}]+/gu, " ").trim() + " ")));
}

const button = a => [{ content_type: "text", title: (a.button || "I'm following ✅").slice(0, 20), payload: "F:" + a.id }];

export async function onComment(env, c) {
  if (!c?.id || !c.text || c.from?.id === env.IG_USER_ID) return;
  const a = match(await automations(env), c.text, c.media?.id);
  if (!a || await env.DM.get("c:" + c.id)) return;
  await env.DM.put("c:" + c.id, "1", { expirationTtl: 8 * DAY });
  if (c.from?.id) await env.DM.put("u:" + c.from.id, a.id, { expirationTtl: 7 * DAY });
  const opener = a.opener || `Hey! I've got ${a.deliverable_title || "it"} ready for you. Make sure you're following @${env.HANDLE} so I can send it, then tap the button 👇`;
  let r = await send(env, { comment_id: c.id }, { text: opener, quick_replies: button(a) });
  if (!r.ok)  // the quick reply was refused on a private reply: plain text that asks for a reply
    r = await send(env, { comment_id: c.id }, { text: `${opener}\n\nFollow @${env.HANDLE}, then reply DONE here.` });
  if (a.public_replies?.length)
    await api(env, "POST", `/${c.id}/replies`, { message: a.public_replies[Math.floor(Math.random() * a.public_replies.length)] });
  await note(env, `comment ${a.keyword} @${c.from?.username || c.from?.id}: private reply ${r.ok ? "sent" : "FAILED " + r.error}`);
}

export async function onMessage(env, m) {
  const s = m.sender?.id;
  if (!s || s === env.IG_USER_ID || m.message?.is_echo) return;
  const mid = m.message?.mid || m.postback?.mid;
  if (mid) {
    if (await env.DM.get("m:" + mid)) return;
  }
  const text = m.message?.text || m.postback?.title || "";
  const payload = m.message?.quick_reply?.payload || m.postback?.payload || "";
  const autos = await automations(env);
  let a = payload.startsWith("F:") ? autos.find(x => x.id === payload.slice(2)) : match(autos, text);
  if (!a && /^\s*(done|followed|following|i'?m following|i am following)\b/i.test(text)) {
    const id = await env.DM.get("u:" + s);
    a = autos.find(x => x.id === id && x.active !== false);
  }
  if (!a) return;  // an ordinary DM: leave it for a human
  if (mid) await env.DM.put("m:" + mid, "1", { expirationTtl: 2 * DAY });
  await gate(env, s, a);
}

export async function gate(env, s, a) {
  const p = await api(env, "GET", `/${s}?fields=is_user_follow_business,username`);
  if (p.ok && p.json.is_user_follow_business === true) {
    const msg = a.link
      ? { attachment: { type: "template", payload: { template_type: "generic", elements: [{
          title: (a.deliverable_title || "Here it is").slice(0, 80), subtitle: (a.deliverable_text || "").slice(0, 80),
          buttons: [{ type: "web_url", url: a.link, title: (a.link_title || "Open").slice(0, 20) }] }] } } }
      : { text: a.deliverable_text || "Here it is!" };
    let r = await send(env, { id: s }, msg);
    if (!r.ok && a.link) r = await send(env, { id: s }, { text: `${a.deliverable_text || "Here it is"} 👇\n${a.link}` });
    await note(env, `deliver ${a.keyword} -> @${p.json.username || s}: ${r.ok ? "sent" : "FAILED " + r.error}`);
  } else {
    const r = await send(env, { id: s }, { text: a.follow_text || `Almost there! Follow @${env.HANDLE} first, then tap the button again 👇`, quick_replies: button(a) });
    await note(env, `gate ${a.keyword} -> ${s}: not following${p.ok ? "" : " (lookup failed: " + p.error + ")"}, prompt ${r.ok ? "sent" : "FAILED"}`);
  }
}

// ---------- Graph API ----------
async function token(env) {
  return (await env.DM.get("token")) || env.IG_TOKEN;
}

export async function api(env, method, path, body) {
  const init = { method, headers: { Authorization: `Bearer ${await token(env)}` } };
  if (body) { init.headers["Content-Type"] = "application/json"; init.body = JSON.stringify(body); }
  try {
    const res = await fetch(G + path, init);
    const json = await res.json().catch(() => ({}));
    return res.ok && !json.error ? { ok: true, json } : { ok: false, json, error: json.error?.message || `HTTP ${res.status}` };
  } catch (e) {
    return { ok: false, json: {}, error: String(e) };
  }
}

const send = (env, recipient, message) => api(env, "POST", `/${env.IG_USER_ID}/messages`, { recipient, message });

async function note(env, line) {
  const log = JSON.parse(await env.DM.get("log") || "[]");
  log.unshift(new Date().toISOString() + " " + line);
  await env.DM.put("log", JSON.stringify(log.slice(0, 40)));
}

// ---------- cron: token refresh + polling fallback (only while webhooks are silent) ----------
export async function cron(env) {
  const tokAt = Number(await env.DM.get("token_at") || 0);
  if (Date.now() - tokAt > 7 * DAY * 1000) await refreshToken(env);
  const autos = (await automations(env)).filter(a => a.active !== false);
  const lastHook = Number(await env.DM.get("last_webhook_at") || 0);
  if (!autos.length || Date.now() - lastHook < 6 * 3600e3) return;
  await poll(env);
}

export async function refreshToken(env) {
  const res = await fetch(`https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=${await token(env)}`);
  const j = await res.json().catch(() => ({}));
  if (j.access_token) {
    await env.DM.put("token", j.access_token);
    await env.DM.put("token_at", String(Date.now()));
  }
  await note(env, `token refresh ${j.access_token ? "ok, expires in " + Math.round((j.expires_in || 0) / DAY) + " d" : "FAILED " + (j.error?.message || res.status)}`);
}

// Meta stamps look like 2026-11-26T10:00:00+0000; compare as epoch ms
export const ts = s => Date.parse(String(s || "").replace(/([+-]\d\d)(\d\d)$/, "$1:$2")) || 0;

// KV cursor (epoch ms). Writes only when it moves (free tier: 1,000 KV writes/day). First sight starts from now,
// so an old comment is never answered by a newly armed keyword.
async function cursor(env, key, newest) {
  const old = Number(await env.DM.get(key) || 0);
  if (!old) { await env.DM.put(key, String(Math.max(newest, Date.now()))); return null; }
  if (newest > old) await env.DM.put(key, String(newest));
  return old;
}

export async function poll(env) {
  const media = await api(env, "GET", `/${env.IG_USER_ID}/media?fields=id,timestamp&limit=4`);
  for (const md of media.json.data || []) {
    if (Date.now() - ts(md.timestamp) > 7 * DAY * 1000) continue;
    const list = (await api(env, "GET", `/${md.id}/comments?fields=id,text,timestamp,from&limit=50`)).json.data || [];
    const since = await cursor(env, "seen:" + md.id, Math.max(0, ...list.map(c => ts(c.timestamp))));
    if (since) for (const c of list) if (ts(c.timestamp) > since) await onComment(env, { ...c, media: { id: md.id } });
  }
  const conv = await api(env, "GET", `/me/conversations?platform=instagram&fields=updated_time,messages.limit(3){id,from,message,created_time}&limit=10`);
  const msgs = (conv.json.data || []).flatMap(c => c.messages?.data || []);
  const since = await cursor(env, "seen:conv", Math.max(0, ...msgs.map(m => ts(m.created_time))));
  if (since) for (const m of msgs) if (ts(m.created_time) > since && m.from?.id !== env.IG_USER_ID)
    await onMessage(env, { sender: { id: m.from?.id }, message: { mid: m.id, text: m.message } });
}

// ---------- admin API (rf dm) ----------
async function admin(req, url, env) {
  const j = (d, status = 200) => new Response(JSON.stringify(d, null, 2), { status, headers: { "content-type": "application/json" } });
  const route = url.pathname.slice(7);
  if (route === "automations" && req.method === "GET") return j(await automations(env));
  if (route === "automations" && req.method === "PUT") {
    const a = await req.json();
    if (!a.id || !a.keyword) return j({ error: "id and keyword required" }, 400);
    const list = (await automations(env)).filter(x => x.id !== a.id);
    if (list.some(x => x.active !== false && norm(x.keyword) === norm(a.keyword))) return j({ error: `keyword ${a.keyword} already active` }, 409);
    if (a.page) { await env.DM.put("page:" + a.id, a.page); a.link = `${url.origin}/d/${a.id}`; delete a.page; }
    list.push({ active: true, created_at: new Date().toISOString(), ...a });
    await env.DM.put("automations", JSON.stringify(list));
    return j(a);
  }
  if (route === "automations" && req.method === "DELETE") {
    const id = url.searchParams.get("id");
    const list = (await automations(env)).map(x => (x.id === id || norm(x.keyword) === norm(id) ? { ...x, active: false } : x));
    await env.DM.put("automations", JSON.stringify(list));
    return j(list);
  }
  if (route === "subscribe" && req.method === "POST")
    return j(await api(env, "POST", `/${env.IG_USER_ID}/subscribed_apps?subscribed_fields=comments,messages,messaging_postbacks`));
  if (route === "health") {
    const me = await api(env, "GET", `/me?fields=user_id,username,followers_count`);
    return j({ account: me.ok ? me.json : me.error, last_webhook_at: Number(await env.DM.get("last_webhook_at") || 0) || null,
      token_refreshed_at: Number(await env.DM.get("token_at") || 0) || null, automations: (await automations(env)).filter(a => a.active !== false).map(a => a.keyword),
      log: JSON.parse(await env.DM.get("log") || "[]") });
  }
  if (route === "poll" && req.method === "POST") { await poll(env); return j({ ok: true }); }
  if (route === "refresh-token" && req.method === "POST") { await refreshToken(env); return j({ ok: true }); }
  return j({ error: "unknown route" }, 404);
}

// ---------- static pages ----------
const html = body => new Response(body, { headers: { "content-type": "text/html; charset=utf-8" } });
const page = (title, inner) => `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:680px;margin:40px auto;padding:0 16px;color:#1b1b1b;background:#fff}h1{font-size:22px}</style><h1>${title}</h1>${inner}`;
const PRIVACY = env => page("Privacy policy", `<p>This service sends a direct message on Instagram to people who comment a keyword on posts by @${env.HANDLE} or message the account.</p>
<p>It processes only what Instagram's official API provides for that purpose: the comment text, your Instagram-scoped ID and username, and whether you follow the account. It keeps an ID only to avoid duplicate messages (deleted automatically within 8 days) and never sells or shares data.</p>
<p>Contact: send a direct message to @${env.HANDLE} on Instagram.</p>`);
const DELETION = env => page("Data deletion", `<p>We keep no profile data. Short-lived IDs used to avoid duplicate messages expire within 8 days. To ask for immediate deletion, send a direct message to @${env.HANDLE} on Instagram with the word DELETE and we will remove any record within 24 hours.</p>`);
