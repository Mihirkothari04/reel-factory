import React, { useMemo } from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { OUT } from "./anim";
import { Rich } from "./rich";
import { useTheme } from "./theme";
import type { CaptionStyle, Word } from "./types";

type Chunk = { words: Word[]; s: number; e: number };

const clean = (w: string) => w.toLowerCase().replace(/[^a-z0-9$%+.#-]/g, "").replace(/\.$/, "");

/** Group words into 1–3 word chunks, breaking on punctuation and pauses (corpus: 1–4 words, word-synced). */
export const chunkWords = (words: Word[], maxWords = 3, maxChars = 18): Chunk[] => {
  const out: Chunk[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) out.push({ words: cur, s: cur[0].s, e: cur[cur.length - 1].e });
    cur = [];
  };
  words.forEach((w, i) => {
    const prev = words[i - 1];
    const chars = cur.reduce((a, x) => a + x.w.length + 1, 0) + w.w.length;
    if (cur.length && (cur.length >= maxWords || chars > maxChars || (prev && w.s - prev.e > 0.35))) flush();
    cur.push(w);
    if (/[.!?,;:]$/.test(w.w)) flush();
  });
  flush();
  // extend each chunk until next one starts (no flicker), cap at +0.6s
  out.forEach((c, i) => (c.e = Math.min(out[i + 1]?.s ?? c.e + 0.6, c.e + 0.6)));
  return out;
};

export const Captions: React.FC<{ words: Word[]; emphasis: string[]; style: CaptionStyle; y: number }> = ({ words, emphasis, style, y }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  const caps = style === "caps";
  const chunks = useMemo(() => chunkWords(words, caps ? 2 : 3, caps ? 14 : 18), [words, caps]);
  const em = useMemo(() => new Set(emphasis.map(clean)), [emphasis]);
  if (style === "none") return null;
  const c = chunks.find((x) => now >= x.s - 0.04 && now < x.e);
  if (!c) return null;
  const pop = OUT(Math.min(1, (now - c.s + 0.04) / 0.12));

  const base: React.CSSProperties = {
    position: "absolute",
    left: 70,
    right: 70,
    top: y,
    translate: "0 -50%",
    display: "flex",
    justifyContent: "center",
    pointerEvents: "none",
  };
  const words_ = c.words.map((w, i) => {
    const isEm = em.has(clean(w.w));
    const spoken = now >= w.s - 0.02;
    return { w: w.w, isEm, spoken, key: i };
  });

  if (style === "pill") {
    return (
      <div style={base}>
        <div style={{ background: "rgba(16,16,18,0.9)", borderRadius: 16, padding: "14px 28px", fontFamily: t.sans, fontWeight: 800, fontSize: 58, lineHeight: 1.15, color: "#F7F5F0", textAlign: "center", scale: interpolate(pop, [0, 1], [0.92, 1]), letterSpacing: "-0.01em" }}>
          {words_.map((x) => (
            <span key={x.key} style={{ color: x.isEm ? t.accent : "#F7F5F0", opacity: x.spoken ? 1 : 0.45 }}>{x.w} </span>
          ))}
        </div>
      </div>
    );
  }
  if (style === "highlight") {
    return (
      <div style={base}>
        <div style={{ fontFamily: t.sans, fontWeight: 800, fontSize: 62, lineHeight: 1.2, color: t.ink, textAlign: "center", scale: interpolate(pop, [0, 1], [0.94, 1]), letterSpacing: "-0.015em" }}>
          {words_.map((x) => (
            <span key={x.key} style={x.isEm ? { background: t.accent, color: t.accentInk, padding: "0 10px", borderRadius: 6, margin: "0 4px" } : { opacity: x.spoken ? 1 : 0.4 }}>
              {x.w}{" "}
            </span>
          ))}
        </div>
      </div>
    );
  }
  if (style === "serif") {
    return (
      <div style={base}>
        <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 60, lineHeight: 1.2, color: t.ink, textAlign: "center", scale: interpolate(pop, [0, 1], [0.94, 1]) }}>
          {words_.map((x) => (
            <span key={x.key} style={x.isEm ? { fontFamily: t.serif, fontStyle: "italic", fontWeight: 400, color: t.accent, fontSize: 68 } : { opacity: x.spoken ? 1 : 0.4 }}>
              {x.w}{" "}
            </span>
          ))}
        </div>
      </div>
    );
  }
  // caps
  return (
    <div style={base}>
      <div style={{ fontFamily: t.display, fontWeight: 900, fontSize: 92, lineHeight: 1, textTransform: "uppercase", color: t.ink, textAlign: "center", letterSpacing: "-0.02em", scale: interpolate(pop, [0, 1], [1.15, 1]) }}>
        {words_.map((x) => (
          <span key={x.key} style={x.isEm ? { background: t.accent, color: t.accentInk, padding: "0 12px" } : {}}>{x.w} </span>
        ))}
      </div>
    </div>
  );
};

/** Persistent hook sticker for late arrivals / muted viewers (≈25% of corpus). */
export const HookTitle: React.FC<{ text: string; until: number }> = ({ text, until }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  if (now > until) return null;
  const k = OUT(Math.min(1, now / 0.25));
  const out = interpolate(now, [until - 0.2, until], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 150, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: k * out }}>
      <div style={{ background: t.dark ? t.ink : t.ink, color: t.bg, fontFamily: t.sans, fontWeight: 800, fontSize: 48, lineHeight: 1.15, padding: "14px 26px", borderRadius: 10, maxWidth: 900, textAlign: "center", letterSpacing: "-0.01em" }}>
        <Rich text={text} emColor={t.dark ? t.bg : t.accent} />
      </div>
    </div>
  );
};

export const HudLabel: React.FC<{ text: string }> = ({ text }) => {
  const t = useTheme();
  return (
    <div style={{ position: "absolute", top: 140, left: 88, fontFamily: t.mono, fontSize: 28, color: t.muted, letterSpacing: "0.02em" }}>
      {text}
    </div>
  );
};

export const Handle: React.FC<{ text: string }> = ({ text }) => {
  const t = useTheme();
  return <div style={{ position: "absolute", top: 140, right: 88, fontFamily: t.mono, fontSize: 26, color: t.muted }}>{text}</div>;
};

/** Persistent news lower-third (Newsroom mode): red kicker block + white headline box. Sits above the caption line. */
export const Banner: React.FC<{ text: string; kicker?: string; y: number }> = ({ text, kicker = "BREAKING", y }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = OUT(Math.min(1, frame / (0.35 * fps)));
  return (
    <div style={{ position: "absolute", top: y, left: 56, right: 56, display: "flex", alignItems: "stretch", translate: `${(1 - k) * -120}px 0`, opacity: k }}>
      <div style={{ background: t.bad, color: "#FFFFFF", fontFamily: t.display, fontWeight: 800, fontSize: 34, padding: "14px 22px", display: "flex", alignItems: "center", letterSpacing: "0.04em" }}>{kicker}</div>
      <div style={{ flex: 1, background: "#FFFFFF", color: "#111111", fontFamily: t.sans, fontWeight: 800, fontSize: 38, lineHeight: 1.15, padding: "14px 22px" }}>
        <Rich text={text} emColor={t.bad} />
      </div>
    </div>
  );
};

/** Film-slate HUD (Cinematic mode): corner brackets, title line, running timecode, scene n/N. */
export const Slate: React.FC<{ title: string; sceneStarts: number[] }> = ({ title, sceneStarts }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  const n = sceneStarts.filter((s) => now >= s).length;
  const tc = [Math.floor(now / 3600), Math.floor(now / 60) % 60, Math.floor(now) % 60, frame % fps].map((x) => String(x).padStart(2, "0")).join(":");
  const br = (pos: React.CSSProperties, r: number): React.ReactNode => (
    <div style={{ position: "absolute", width: 46, height: 46, ...pos, borderColor: t.muted, borderStyle: "solid", borderWidth: 0, rotate: `${r}deg`, borderTopWidth: 3, borderLeftWidth: 3 }} />
  );
  const txt: React.CSSProperties = { position: "absolute", fontFamily: t.mono, fontSize: 24, color: t.muted, letterSpacing: "0.04em", textTransform: "uppercase" };
  return (
    <>
      {br({ left: 44, top: 120 }, 0)}
      {br({ right: 44, top: 120 }, 90)}
      {br({ left: 44, top: 1440 }, 270)}
      {br({ right: 44, top: 1440 }, 180)}
      <div style={{ ...txt, left: 104, top: 128 }}>{title}</div>
      <div style={{ ...txt, right: 104, top: 128 }}>TC {tc}</div>
      <div style={{ ...txt, left: 104, top: 1452 }}>SCENE {String(n).padStart(2, "0")}/{String(sceneStarts.length).padStart(2, "0")}</div>
    </>
  );
};

/** Persistent progress tracker (story ladders, steps, catalogs): N segments fill as items complete, current label at right. */
export const Progress: React.FC<{ items: string[]; at: number[]; style?: "bar" | "chips" }> = ({ items, at, style = "bar" }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  const done = at.filter((a) => now >= a).length;
  if (style === "chips") {
    // table-of-contents chips: all items visible from the start (open loop); reached ones fill, current one outlined
    return (
      <div style={{ position: "absolute", top: 128, left: 70, right: 70, display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "center" }}>
        {items.map((x, i) => {
          const k = OUT(Math.min(1, Math.max(0, (now - i * 0.12) / 0.3)));
          const on = i < done;
          const cur = i === done - 1;
          return (
            <div key={i} style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 28, padding: "8px 16px", borderRadius: 8, opacity: k, translate: `0 ${(1 - k) * 12}px`, background: on ? (cur ? t.accent : t.surface) : "transparent", color: cur ? t.accentInk : on ? t.ink : t.muted, border: `2px solid ${cur ? t.accent : t.line}` }}>
              {i + 1}. {x}
            </div>
          );
        })}
      </div>
    );
  }
  if (done === 0) return null;
  const cur = items[done - 1];
  return (
    <div style={{ position: "absolute", top: 136, left: 88, right: 88, display: "flex", alignItems: "center", gap: 22 }}>
      <div style={{ flex: 1, display: "flex", gap: 6 }}>
        {items.map((_, i) => (
          <div key={i} style={{ flex: 1, height: 8, borderRadius: 4, background: i < done ? t.accent : t.line }} />
        ))}
      </div>
      <div style={{ fontFamily: t.mono, fontSize: 26, color: t.ink, whiteSpace: "nowrap" }}>
        {String(done).padStart(2, "0")}/{String(items.length).padStart(2, "0")} · {cur}
      </div>
    </div>
  );
};
