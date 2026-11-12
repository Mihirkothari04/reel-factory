import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useVideoConfig } from "remotion";
import { Video } from "@remotion/media";
import { fmtNum, useProgress, useSpring, useT } from "../anim";
import { Rich } from "../rich";
import { useStage, useTheme } from "../theme";
import { Center } from "./text";

export const src = (x: string) => (/^https?:\/\//.test(x) ? x : staticFile(x));

/** Minimal app window: thin title bar with a mono path label (no fake traffic lights). */
export const Window: React.FC<{ title?: string; children: React.ReactNode; width?: number; dark?: boolean; style?: React.CSSProperties }> = ({
  title,
  children,
  width = 940,
  dark,
  style,
}) => {
  const t = useTheme();
  const { s } = useStage();
  const bg = dark ? "#121214" : t.surface;
  const fg = dark ? "#EDEBE6" : t.ink;
  return (
    <div style={{ width, background: bg, color: fg, border: `1.5px solid ${dark ? "#2A2A2F" : t.line}`, borderRadius: t.radius, overflow: "hidden", ...style }}>
      {title !== undefined && (
        <div style={{ padding: `${14 * s}px ${24 * s}px`, borderBottom: `1.5px solid ${dark ? "#2A2A2F" : t.line}`, fontFamily: t.mono, fontSize: 24 * s, color: dark ? "#9C998F" : t.muted }}>
          {title}
        </div>
      )}
      {children}
    </div>
  );
};

/** GitHub-style repo card with star odometer. props: owner, name, description, stars, language?, license?, topics?, highlight?, image? */
export const Repo: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const k = useSpring(0, 15);
  const count = useProgress(0.25, Math.min(1.6, dur * 0.55));
  const hl = useProgress(0.9, 0.6);
  const meta = [p.language, p.license, p.updated].filter(Boolean);
  return (
    <Center gap={30 * s}>
      <Window title={`github.com/${p.owner}/${p.name}`} style={{ scale: interpolate(k, [0, 1], [0.93, 1]), opacity: k, textAlign: "left" }}>
        {p.image && <Img src={src(p.image)} style={{ width: "100%", display: "block", borderBottom: `1.5px solid ${t.line}` }} />}
        <div style={{ padding: `${36 * s}px ${44 * s}px`, display: "flex", flexDirection: "column", gap: 22 * s }}>
          <div style={{ fontFamily: t.sans, fontSize: 54 * s, fontWeight: 800, letterSpacing: "-0.02em" }}>
            <span style={{ color: t.muted, fontWeight: 500 }}>{p.owner} / </span>
            {p.name}
          </div>
          {p.description && <div style={{ fontFamily: t.sans, fontSize: 42 * s, lineHeight: 1.32, color: t.ink }}><Rich text={p.description} /></div>}
          {p.topics?.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              {p.topics.slice(0, 5).map((x: string) => (
                <span key={x} style={{ fontFamily: t.mono, fontSize: 28 * s, padding: "6px 14px", borderRadius: 6, border: `1.5px solid ${t.line}`, color: t.muted }}>{x}</span>
              ))}
            </div>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 28, fontFamily: t.mono, fontSize: 32 * s, color: t.muted }}>
            <span style={{ color: t.ink, fontWeight: 600, fontSize: 48 * s, fontVariantNumeric: "tabular-nums" }}>
              <span style={{ color: t.accent }}>★</span> {fmtNum(Math.round((p.stars ?? 0) * count))}
            </span>
            {meta.map((m: string) => <span key={m}>{m}</span>)}
          </div>
        </div>
      </Window>
      {p.highlight && (
        <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 44 * s, color: t.ink, opacity: hl, translate: `0 ${(1 - hl) * 20}px`, maxWidth: 900 }}>
          <Rich text={p.highlight} />
        </div>
      )}
    </Center>
  );
};

/** Terminal with typed command and streamed output. props: title?, lines:[{t:'cmd'|'out'|'ok'|'err'|'dim', text}] */
export const Terminal: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const time = useT();
  const k = useSpring(0, 16);
  const lines: { t: string; text: string }[] = p.lines ?? [];
  // schedule: commands type at ~28 chars/s, outputs pop 0.18s apart
  let clock = 0.25;
  const sched = lines.map((l) => {
    const st = clock;
    const d = l.t === "cmd" ? Math.min(1.6, l.text.length / 28) : 0.05;
    clock += d + (l.t === "cmd" ? 0.25 : 0.18);
    return { st, d };
  });
  const scale = clock > dur * 0.9 ? (dur * 0.9) / clock : 1;
  const color = (k: string) => (k === "ok" ? "#62D196" : k === "err" ? "#FF6B5B" : k === "dim" ? "#7C7A74" : k === "cmd" ? "#F2F0EA" : "#C9C6BE");
  return (
    <Center>
      <Window title={p.title ?? "terminal"} dark style={{ opacity: k, scale: interpolate(k, [0, 1], [0.95, 1]), textAlign: "left" }}>
        <div style={{ padding: `${30 * s}px ${36 * s}px`, minHeight: 360 * s, fontFamily: t.mono, fontSize: 40 * s, lineHeight: 1.45 }}>
          {lines.map((l, i) => {
            const st = sched[i].st * scale;
            const d = sched[i].d * scale;
            if (time < st) return null;
            const n = l.t === "cmd" ? Math.floor(Math.min(1, (time - st) / Math.max(d, 0.01)) * l.text.length) : l.text.length;
            const typing = l.t === "cmd" && n < l.text.length;
            return (
              <div key={i} style={{ color: color(l.t), whiteSpace: "pre-wrap" }}>
                {l.t === "cmd" && <span style={{ color: t.accent }}>$ </span>}
                {l.t === "ok" && "✓ "}
                {l.t === "err" && "✗ "}
                {l.text.slice(0, n)}
                {typing && <span style={{ background: "#F2F0EA", color: "transparent" }}>_</span>}
              </div>
            );
          })}
        </div>
      </Window>
      {p.caption && <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 44 * s, color: t.ink, marginTop: 30 * s }}><Rich text={p.caption} /></div>}
    </Center>
  );
};

/** Chat mock: user prompt types, AI reply streams. props: app?, messages:[{role:'user'|'ai', text}] */
export const Chat: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const time = useT();
  const msgs: { role: string; text: string }[] = p.messages ?? [];
  const per = (dur * 0.85) / Math.max(1, msgs.length);
  return (
    <Center>
      <Window title={p.app ?? "chat"} style={{ textAlign: "left" }}>
        <div style={{ padding: 34 * s, display: "flex", flexDirection: "column", gap: 22 * s, minHeight: 420 * s }}>
          {msgs.map((m, i) => {
            const st = 0.2 + i * per;
            if (time < st) return null;
            const n = Math.floor(Math.min(1, (time - st) / (per * 0.7)) * m.text.length);
            const user = m.role === "user";
            return (
              <div key={i} style={{ alignSelf: user ? "flex-end" : "flex-start", maxWidth: "86%", background: user ? t.accent : "transparent", color: user ? t.accentInk : t.ink, border: user ? "none" : `1.5px solid ${t.line}`, borderRadius: t.radius, padding: `${18 * s}px ${24 * s}px`, fontFamily: t.sans, fontSize: 42 * s, lineHeight: 1.35 }}>
                {m.text.slice(0, n)}
              </div>
            );
          })}
        </div>
      </Window>
    </Center>
  );
};

/** Image / screenshot with Ken Burns + optional highlight box. props: src, frame?:'window'|'none', url?, kenburns?:'in'|'out'|'up', box?:{x,y,w,h} (0..1), caption? */
export const ImageScene: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s, w, h } = useStage();
  const k = useSpring(0, 18);
  const kb = useProgress(0, dur, (x) => x);
  const boxIn = useProgress(Math.min(0.8, dur * 0.3), 0.5);
  const z = p.kenburns === "out" ? interpolate(kb, [0, 1], [1.12, 1]) : interpolate(kb, [0, 1], [1, 1.1]);
  const ty = p.kenburns === "up" ? interpolate(kb, [0, 1], [0, -8]) : 0;
  if (p.frame === "full") {
    return (
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img src={src(p.src)} style={{ width: w, height: h, objectFit: "cover", scale: z, translate: `0 ${ty}%` }} />
        {p.caption && <Cap text={p.caption} />}
      </AbsoluteFill>
    );
  }
  return (
    <Center gap={28 * s}>
      <Window title={p.url ?? (p.frame === "none" ? undefined : "")} style={{ opacity: k, scale: interpolate(k, [0, 1], [0.95, 1]) }}>
        <div style={{ position: "relative", overflow: "hidden", maxHeight: (p.maxH ?? 1100) * s }}>
          <Img src={src(p.src)} style={{ width: "100%", display: "block", scale: z, translate: `0 ${ty}%`, transformOrigin: p.origin ?? "50% 30%" }} />
          {p.box && (
            <div style={{ position: "absolute", left: `${p.box.x * 100}%`, top: `${p.box.y * 100}%`, width: `${p.box.w * 100}%`, height: `${p.box.h * 100}%`, border: `5px solid ${t.accent}`, borderRadius: 10, opacity: boxIn, scale: interpolate(boxIn, [0, 1], [1.15, 1]) }} />
          )}
        </div>
      </Window>
      {p.caption && <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 46 * s, color: t.ink, maxWidth: 900 }}><Rich text={p.caption} /></div>}
    </Center>
  );
};

const Cap: React.FC<{ text: string }> = ({ text }) => {
  const t = useTheme();
  return (
    <div style={{ position: "absolute", left: 88, right: 88, top: 220, fontFamily: t.display, fontWeight: t.displayWeight, fontSize: 92, lineHeight: 1.02, color: "#fff", letterSpacing: "-0.02em", textShadow: "0 2px 24px rgba(0,0,0,.45)" }}>
      <Rich text={text} emColor="#fff" />
    </div>
  );
};

/** Video clip (generated b-roll / screen recording). props: src, fit?, caption?, trim? */
export const VideoScene: React.FC<{ p: any; dur: number }> = ({ p }) => {
  const { fps } = useVideoConfig();
  const { w, h } = useStage();
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <Video src={src(p.src)} muted trimBefore={Math.round((p.trim ?? 0) * fps)} style={{ width: w, height: h, objectFit: p.fit ?? "cover" }} />
      {p.caption && <Cap text={p.caption} />}
    </AbsoluteFill>
  );
};

/** CTA: comment-box mock types the keyword, then a "sent" confirmation — shows the viewer exactly what to do.
 * props: kind:'comment'|'follow'|'save', keyword?, line?, sent? */
export const Cta: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const time = useT();
  const k = useSpring(0, 14);
  const kw: string = p.keyword ?? "";
  const typeStart = 0.5;
  const typed = Math.floor(Math.max(0, Math.min(1, (time - typeStart) / 0.7)) * kw.length);
  const sentAt = typeStart + 1.0;
  const sent = useProgress(sentAt, 0.35);
  const big = p.kind === "comment" ? `Comment “${kw}”` : p.kind === "save" ? "Save this" : "Follow";
  return (
    <Center gap={38 * s}>
      <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, textTransform: t.displayCase, fontSize: 112 * s, lineHeight: 1.02, letterSpacing: "-0.03em", color: t.ink, scale: interpolate(k, [0, 1], [0.9, 1]), opacity: k }}>
        <Rich text={p.headline ?? big.replace(kw, `*${kw}*`)} />
      </div>
      {p.line && <div style={{ fontFamily: t.sans, fontSize: 44 * s, color: t.muted, maxWidth: 860, opacity: k }}><Rich text={p.line} /></div>}
      {p.kind === "comment" && (
        <div style={{ width: 860, display: "flex", flexDirection: "column", gap: 18 * s, opacity: k }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20, background: t.surface, border: `1.5px solid ${t.line}`, borderRadius: 999, padding: `${18 * s}px ${30 * s}px`, fontFamily: t.sans, fontSize: 38 * s, color: t.ink, textAlign: "left" }}>
            <span style={{ flex: 1 }}>
              {typed === 0 ? <span style={{ color: t.muted }}>Add a comment…</span> : kw.slice(0, typed)}
            </span>
            <span style={{ fontWeight: 700, color: typed === kw.length ? t.accent : t.muted }}>Post</span>
          </div>
          <div style={{ alignSelf: "flex-start", background: t.accent, color: t.accentInk, fontFamily: t.sans, fontWeight: 700, fontSize: 34 * s, padding: `${14 * s}px ${26 * s}px`, borderRadius: t.radius, opacity: sent, translate: `0 ${(1 - sent) * 16}px` }}>
            {p.sent ?? "Sent — check your DMs"}
          </div>
        </div>
      )}
    </Center>
  );
};

/** Source/config file view: line numbers, highlighted lines, optional redaction of secrets.
 * props: file, lines: string[], highlight?: number[] (1-based), redact?: string[] (substrings shown as ••••), caption?, lang? */
export const Code: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const time = useT();
  const k = useSpring(0, 16);
  const lines: string[] = p.lines ?? [];
  const hl: number[] = p.highlight ?? [];
  const per = Math.min(0.12, (dur * 0.35) / Math.max(1, lines.length));
  const hlIn = useProgress(Math.min(0.4 + lines.length * per, dur * 0.5), 0.35);
  const mask = (x: string) => (p.redact ?? []).reduce((acc: string, r: string) => acc.split(r).join("•".repeat(Math.min(12, r.length))), x);
  const longest = Math.max(1, ...lines.map((l) => l.length));
  const avail = 940 - 128 * s - 12;
  const fs = Math.min((lines.length > 12 ? 30 : 36) * s, avail / (longest * 0.62));
  return (
    <Center gap={30 * s}>
      <Window title={p.file ?? "file"} dark style={{ opacity: k, scale: interpolate(k, [0, 1], [0.95, 1]), textAlign: "left" }}>
        <div style={{ padding: `${24 * s}px 0`, fontFamily: t.mono, fontSize: fs, lineHeight: 1.55 }}>
          {lines.map((l, i) => {
            const on = time >= 0.2 + i * per;
            const isHl = hl.includes(i + 1);
            return (
              <div key={i} style={{ display: "flex", opacity: on ? 1 : 0, background: isHl ? `rgba(255,255,255,${0.1 * hlIn})` : "transparent", borderLeft: `6px solid ${isHl && hlIn > 0.5 ? t.accent : "transparent"}`, padding: `0 ${28 * s}px 0 ${18 * s}px` }}>
                <span style={{ color: "#6E6C66", minWidth: 56 * s, textAlign: "right", marginRight: 26 * s }}>{i + 1}</span>
                <span style={{ color: isHl && hlIn > 0.5 ? "#FFFFFF" : "#CFCBC2", whiteSpace: "pre-wrap", overflowWrap: "break-word" }}>{mask(l)}</span>
              </div>
            );
          })}
        </div>
      </Window>
      {p.caption && <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 46 * s, color: t.ink, maxWidth: 900, opacity: hlIn }}><Rich text={p.caption} /></div>}
    </Center>
  );
};
