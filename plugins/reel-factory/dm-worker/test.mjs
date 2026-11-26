// node --test dm-worker/test.mjs : the whole follow-gate flow against a fake Graph API and an in-memory KV
import test from "node:test";
import assert from "node:assert/strict";
import worker, { handleWebhook, validSignature, match, ts, poll } from "./worker.mjs";

function setup({ follows = false, quickReplyRefused = false } = {}) {
  const kv = new Map();
  const calls = [];
  const env = {
    IG_USER_ID: "17800", HANDLE: "demo.page", APP_SECRETS: "wrong,s3cret", VERIFY_TOKEN: "vt", ADMIN_TOKEN: "adm", IG_TOKEN: "tok",
    DM: { get: async k => kv.get(k) ?? null, put: async (k, v) => void kv.set(k, v), delete: async k => void kv.delete(k) },
  };
  globalThis.fetch = async (url, init = {}) => {
    const body = init.body ? JSON.parse(init.body) : null;
    calls.push({ url: String(url), method: init.method || "GET", body });
    const ok = (d) => new Response(JSON.stringify(d), { status: 200 });
    if (String(url).includes("fields=is_user_follow_business")) return ok({ is_user_follow_business: follows, username: "fan" });
    if (String(url).endsWith("/17800/messages")) {
      if (quickReplyRefused && body.recipient.comment_id && body.message.quick_replies)
        return new Response(JSON.stringify({ error: { message: "quick replies not allowed" } }), { status: 400 });
      return ok({ recipient_id: "x", message_id: "m" });
    }
    return ok({ id: "r" });
  };
  kv.set("automations", JSON.stringify([{ id: "nv1", keyword: "NVIDIA", link: "https://example.com/t", link_title: "Timeline",
    deliverable_title: "Full timeline", public_replies: ["Sent! Check your DMs 📩"] }]));
  return { env, kv, calls };
}
const sent = calls => calls.filter(c => c.url.endsWith("/17800/messages")).map(c => c.body);
const comment = (id, text, from = "555") => ({ object: "instagram", entry: [{ changes: [{ field: "comments", value: { id, text, from: { id: from, username: "fan" }, media: { id: "m1" } } }] }] });
const tap = (mid, from = "555") => ({ object: "instagram", entry: [{ messaging: [{ sender: { id: from }, recipient: { id: "17800" }, message: { mid, text: "I'm following ✅", quick_reply: { payload: "F:nv1" } } }] }] });

test("signature: HMAC-SHA256 with any configured secret", async () => {
  const { env } = setup();
  const raw = '{"a":1}';
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode("s3cret"), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const hex = [...new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw)))].map(b => b.toString(16).padStart(2, "0")).join("");
  assert.equal(await validSignature(raw, "sha256=" + hex, env), true);
  assert.equal(await validSignature(raw, "sha256=00", env), false);
  assert.equal(await validSignature(raw, null, env), false);
});

test("keyword match is whole-word and case-insensitive", () => {
  const autos = [{ id: "a", keyword: "NVIDIA" }, { id: "b", keyword: "AI", media_id: "m9" }];
  assert.equal(match(autos, "nvidia!! 🔥")?.id, "a");
  assert.equal(match(autos, "nvidias"), undefined);
  assert.equal(match(autos, "AI please", "m1"), undefined);
  assert.equal(match(autos, "AI please", "m9")?.id, "b");
});

test("comment -> one private reply with a follow button + public reply; duplicates and own comments ignored", async () => {
  const { env, calls } = setup();
  await handleWebhook(env, comment("c1", "NVIDIA"));
  await handleWebhook(env, comment("c1", "NVIDIA"));            // Meta redelivery
  await handleWebhook(env, comment("c2", "NVIDIA", "17800"));   // our own comment
  await handleWebhook(env, comment("c3", "great reel"));        // no keyword
  const s = sent(calls);
  assert.equal(s.length, 1);
  assert.deepEqual(s[0].recipient, { comment_id: "c1" });
  assert.equal(s[0].message.quick_replies[0].payload, "F:nv1");
  assert.ok(calls.some(c => c.url.endsWith("/c1/replies")));
});

test("private reply falls back to text when quick replies are refused", async () => {
  const { env, calls } = setup({ quickReplyRefused: true });
  await handleWebhook(env, comment("c1", "nvidia"));
  const s = sent(calls);
  assert.equal(s.length, 2);
  assert.match(s[1].message.text, /reply DONE/);
});

test("button tap: not following -> follow prompt again; following -> link card", async () => {
  let { env, calls } = setup({ follows: false });
  await handleWebhook(env, tap("t1"));
  assert.match(sent(calls)[0].message.text, /Follow @demo.page/);
  assert.equal(sent(calls)[0].message.quick_replies[0].payload, "F:nv1");
  ({ env, calls } = setup({ follows: true }));
  await handleWebhook(env, tap("t2"));
  await handleWebhook(env, tap("t2"));  // duplicate delivery
  const s = sent(calls);
  assert.equal(s.length, 1);
  assert.equal(s[0].message.attachment.payload.elements[0].buttons[0].url, "https://example.com/t");
});

test("typing DONE uses the remembered automation; unrelated DMs are left alone", async () => {
  const { env, calls, kv } = setup({ follows: true });
  kv.set("u:555", "nv1");
  await handleWebhook(env, { object: "instagram", entry: [{ messaging: [{ sender: { id: "555" }, message: { mid: "d1", text: "done" } }] }] });
  await handleWebhook(env, { object: "instagram", entry: [{ messaging: [{ sender: { id: "777" }, message: { mid: "d2", text: "hello, collab?" } }] }] });
  assert.equal(sent(calls).length, 1);
});

test("webhook verification + admin auth", async () => {
  const { env } = setup();
  const ctx = { waitUntil: p => p };
  let r = await worker.fetch(new Request("https://w.dev/webhook?hub.mode=subscribe&hub.verify_token=vt&hub.challenge=42"), env, ctx);
  assert.equal(await r.text(), "42");
  r = await worker.fetch(new Request("https://w.dev/webhook?hub.mode=subscribe&hub.verify_token=no&hub.challenge=42"), env, ctx);
  assert.equal(r.status, 403);
  r = await worker.fetch(new Request("https://w.dev/admin/automations"), env, ctx);
  assert.equal(r.status, 401);
  r = await worker.fetch(new Request("https://w.dev/admin/automations", { method: "PUT", headers: { authorization: "Bearer adm" },
    body: JSON.stringify({ id: "x2", keyword: "nvidia" }) }), env, ctx);
  assert.equal(r.status, 409);  // keyword already active
  r = await worker.fetch(new Request("https://w.dev/admin/automations", { method: "PUT", headers: { authorization: "Bearer adm" },
    body: JSON.stringify({ id: "rh1", keyword: "PROOF", page: "<h1>Sources</h1>" }) }), env, ctx);
  assert.equal((await r.json()).link, "https://w.dev/d/rh1");
  r = await worker.fetch(new Request("https://w.dev/d/rh1"), env, ctx);
  assert.match(await r.text(), /Sources/);
});

test("poller: first sight never answers old comments, then answers new ones once", async () => {
  const { env, calls } = setup();
  const now = Date.now();
  const iso = t => new Date(t).toISOString().replace(/\.\d{3}Z$/, "+0000");
  let comments = [{ id: "old", text: "NVIDIA", timestamp: iso(now - 60e3), from: { id: "9" } }];
  globalThis.fetch = (orig => async (url, init) => {
    if (String(url).includes("/media?")) return new Response(JSON.stringify({ data: [{ id: "m1", timestamp: iso(now - 3600e3) }] }));
    if (String(url).includes("/comments?")) return new Response(JSON.stringify({ data: comments }));
    if (String(url).includes("/conversations?")) return new Response(JSON.stringify({ data: [] }));
    return orig(url, init);
  })(globalThis.fetch);
  await poll(env);
  assert.equal(sent(calls).length, 0);
  comments = [...comments, { id: "new", text: "nvidia pls", timestamp: iso(Date.now() + 5e3), from: { id: "8" } }];
  await poll(env);
  await poll(env);
  assert.equal(sent(calls).length, 1);
  assert.equal(ts("2026-11-26T10:00:00+0000"), Date.parse("2026-11-26T10:00:00Z"));
});
