/**
 * Scene types added for the creation modes (modes.json):
 *   walkthrough — app window + cursor performing typed/click/zoom actions   (Screen Walkthrough mode)
 *   headline    — article / press card with outlet, date and highlighted headline (Newsroom, Receipts)
 *   carousel    — depth-of-field card stack stepping through many items (Rapid Catalog)
 *   sheet       — dense two-column cheat sheet, the screenshot frame (Rapid Catalog, Framework)
 * Timing props (`at`, `revealAt`, `highlightAt`) are seconds from scene start; build.py fills them from the VO.
 */
import React from "react";
import { AbsoluteFill, Img, interpolate } from "remotion";
import { OUT, stagger, useProgress, useSpring, useT } from "../anim";
import { Rich } from "../rich";
import { useStage, useTheme } from "../theme";
import { Center } from "./text";
import { src, Window } from "./ui";

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

type Action =
  | { type: "move"; x: number; y: number; at?: number }
  | { type: "click"; x: number; y: number; at?: number }
  | { type: "type"; x: number; y: number; w?: number; text: string; at?: number; cps?: number }
  | { type: "zoom"; x: number; y: number; scale?: number; at?: number }
  | { type: "box"; x: number; y: number; w: number; h: number; at?: number }
  | { type: "arrow"; x: number; y: number; at?: number; until?: number; from?: "top" | "left" | "right" | "bottom"; color?: string };

/** props: url?, src? (screenshot / mock), rows? (rebuilt text lines when no src), aspect? (w/h of content, default 0.75), actions[] (coords 0..1 of content) */
export const Walkthrough: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const now = useT();
  const k = useSpring(0, 18);
  const W = 940;
  const H = Math.min(1060 * s, W / (p.aspect ?? 0.75));
  const acts: Action[] = p.actions ?? [];
  const at = acts.map((a, i) => a.at ?? 0.4 + (i * Math.max(0.6, dur - 1.2)) / Math.max(1, acts.length));
  // cursor path: glide between positional actions
  const pos = acts.map((a, i) => ({ x: a.x + ("w" in a && a.type === "box" ? a.w / 2 : 0), y: a.y + ("h" in a ? (a as any).h / 2 : 0), t: at[i] })).filter((_, i) => acts[i].type !== "zoom" && acts[i].type !== "arrow");
  let cx = 0.86, cy = 0.9;
  pos.forEach((q, i) => {
    const from = i === 0 ? { x: 0.86, y: 0.9 } : pos[i - 1];
    const e = OUT(clamp01((now - (q.t - 0.45)) / 0.45));
    if (now >= q.t - 0.45) { cx = from.x + (q.x - from.x) * e; cy = from.y + (q.y - from.y) * e; }
  });
  // camera zoom: latest zoom action eases in
  let zs = 1, zx = 0.5, zy = 0.5;
  acts.forEach((a, i) => {
    if (a.type !== "zoom") return;
    const e = OUT(clamp01((now - at[i]) / 0.6));
    if (e > 0) { zs = 1 + ((a.scale ?? 1.6) - 1) * e; zx = a.x; zy = a.y; }
  });
  const click = acts.map((a, i) => (a.type === "click" ? clamp01((now - at[i]) / 0.35) : 0));
  return (
    <Center>
      <Window title={p.url ?? ""} style={{ opacity: k, scale: interpolate(k, [0, 1], [0.95, 1]) }}>
        <div style={{ position: "relative", width: W, height: H, overflow: "hidden", background: t.surface }}>
          <div style={{ position: "absolute", inset: 0, scale: zs, transformOrigin: `${zx * 100}% ${zy * 100}%` }}>
            {p.src ? (
              <Img src={src(p.src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} />
            ) : (
              <div style={{ padding: 44 * s, display: "flex", flexDirection: "column", gap: 26 * s }}>
                {(p.rows ?? []).map((r: string, i: number) => (
                  <div key={i} style={{ fontFamily: i === 0 ? t.display : t.sans, fontWeight: i === 0 ? 800 : 500, fontSize: (i === 0 ? 60 : 46) * s, color: i === 0 ? t.ink : t.muted, lineHeight: 1.25 }}>
                    <Rich text={r} />
                  </div>
                ))}
              </div>
            )}
            {acts.map((a, i) => {
              if (a.type === "type") {
                const n = Math.floor(Math.max(0, now - at[i]) * (a.cps ?? 22));
                const shown = a.text.slice(0, n);
                if (now < at[i] - 0.3) return null;
                return (
                  <div key={i} style={{ position: "absolute", left: `${a.x * 100}%`, top: `${a.y * 100}%`, width: `${(a.w ?? 0.8) * 100}%`, translate: "0 -50%", background: t.bg, border: `2px solid ${t.accent}`, borderRadius: 10, padding: `${16 * s}px ${22 * s}px`, fontFamily: t.mono, fontSize: 42 * s, color: t.ink, minHeight: 50 * s, lineHeight: 1.3 }}>
                    {shown}<span style={{ opacity: Math.floor(now * 2.5) % 2 ? 1 : 0, color: t.accent }}>▍</span>
                  </div>
                );
              }
              if (a.type === "box") {
                const e = OUT(clamp01((now - at[i]) / 0.4));
                return e > 0 ? <div key={i} style={{ position: "absolute", left: `${a.x * 100}%`, top: `${a.y * 100}%`, width: `${a.w * 100}%`, height: `${a.h * 100}%`, border: `5px solid ${t.accent}`, borderRadius: 10, opacity: e, scale: interpolate(e, [0, 1], [1.12, 1]) }} /> : null;
              }
              if (a.type === "arrow") {
                // big annotation arrow pointing at a UI element (corpus: yellow arrows on Search Console walkthroughs)
                const e = OUT(clamp01((now - at[i]) / 0.3));
                if (e <= 0 || (a.until !== undefined && now > a.until)) return null;
                const bob = Math.sin((now - at[i]) * 7) * 10 * s;
                const rot = { top: 0, right: 90, bottom: 180, left: -90 }[a.from ?? "top"];
                return (
                  <div key={i} style={{ position: "absolute", left: `${a.x * 100}%`, top: `${a.y * 100}%`, width: 0, height: 0, rotate: `${rot}deg` }}>
                    <svg width={110 * s} height={130 * s} viewBox="0 0 22 26" style={{ position: "absolute", left: -55 * s, top: -138 * s + bob, opacity: e, scale: interpolate(e, [0, 1], [1.4, 1]), filter: "drop-shadow(0 3px 2px rgba(0,0,0,.45))" }}>
                      <path d="M7 1h8v13h6L11 25 1 14h6z" fill={a.color ?? "#FFD21F"} stroke="#111" strokeWidth="1.3" strokeLinejoin="round" />
                    </svg>
                  </div>
                );
              }
              if (a.type === "click" && click[i] > 0 && click[i] < 1) {
                return <div key={i} style={{ position: "absolute", left: `${a.x * 100}%`, top: `${a.y * 100}%`, width: 90 * s, height: 90 * s, translate: "-50% -50%", borderRadius: 999, border: `4px solid ${t.accent}`, opacity: 1 - click[i], scale: 0.4 + click[i] }} />;
              }
              return null;
            })}
          </div>
          {acts.length > 0 && (
            <svg width={44 * s} height={44 * s} viewBox="0 0 24 24" style={{ position: "absolute", left: `${(zx + (cx - zx) * zs) * 100}%`, top: `${(zy + (cy - zy) * zs) * 100}%`, filter: "drop-shadow(0 2px 3px rgba(0,0,0,.35))", scale: click.some((c) => c > 0 && c < 0.4) ? 0.85 : 1 }}>
              <path d="M3 2l7.5 19 2.6-7.6L21 10.8z" fill={t.dark ? "#fff" : "#111"} stroke={t.dark ? "#111" : "#fff"} strokeWidth="1.4" />
            </svg>
          )}
        </div>
      </Window>
      {p.caption && <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 46 * s, color: t.ink, maxWidth: 900 }}><Rich text={p.caption} /></div>}
    </Center>
  );
};

/** props: outlet, date?, headline, highlight?: string[], highlightAt?: number[], dek?, image?, author? */
export const Headline: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const now = useT();
  const k = useSpring(0, 16);
  const hl: string[] = p.highlight ?? [];
  const at: number[] = p.highlightAt ?? hl.map((_, i) => 0.5 + i * Math.min(0.9, dur / (hl.length + 1)));
  const parts: { txt: string; hi: number }[] = [];
  let rest: string = p.headline ?? "";
  hl.forEach((h, i) => {
    const j = rest.indexOf(h);
    if (j < 0) return;
    parts.push({ txt: rest.slice(0, j), hi: -1 }, { txt: h, hi: i });
    rest = rest.slice(j + h.length);
  });
  parts.push({ txt: rest, hi: -1 });
  return (
    <Center>
      <div style={{ width: 940, background: "#FFFFFF", color: "#121212", borderRadius: t.radius, overflow: "hidden", textAlign: "left", opacity: k, scale: interpolate(k, [0, 1], [0.94, 1]), border: `1.5px solid ${t.line}` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: `${26 * s}px ${44 * s}px`, borderBottom: "1.5px solid #E2E0DA" }}>
          <span style={{ fontFamily: t.serif, fontStyle: "italic", fontWeight: 600, fontSize: 42 * s }}>{p.outlet}</span>
          {p.date && <span style={{ fontFamily: t.mono, fontSize: 26 * s, color: "#5A5A5A" }}>{p.date}</span>}
        </div>
        {p.image && <Img src={src(p.image)} style={{ width: "100%", maxHeight: 420 * s, objectFit: "cover", display: "block" }} />}
        <div style={{ padding: `${34 * s}px ${44 * s}px ${40 * s}px` }}>
          <div style={{ fontFamily: t.sans, fontWeight: 800, fontSize: (p.size ?? 58) * s, lineHeight: 1.18, letterSpacing: "-0.015em" }}>
            {parts.map((x, i) => {
              if (x.hi < 0) return <span key={i}>{x.txt}</span>;
              const e = OUT(clamp01((now - at[x.hi]) / 0.45));
              return (
                <span key={i} style={{ backgroundImage: "linear-gradient(#121212,#121212)", backgroundRepeat: "no-repeat", backgroundSize: `${e * 100}% 100%`, color: e > 0.5 ? "#FFFFFF" : "#121212", padding: "0 6px" }}>{x.txt}</span>
              );
            })}
          </div>
          {p.dek && <div style={{ fontFamily: t.sans, fontSize: 34 * s, lineHeight: 1.35, color: "#4A4A4A", marginTop: 22 * s }}>{p.dek}</div>}
          {p.author && <div style={{ fontFamily: t.mono, fontSize: 24 * s, color: "#6A6A6A", marginTop: 22 * s }}>{p.author}</div>}
        </div>
      </div>
    </Center>
  );
};

/** props: items: [{name, desc?, tag?, meta?}], revealAt? (focus change times), total? (for the i/N counter), offset? (index of items[0] in the full list) */
export const Carousel: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const now = useT();
  const items: any[] = p.items ?? [];
  const at: number[] = p.revealAt ?? stagger(items.length, dur, 0.1, 0.4);
  const idx = Math.max(0, at.filter((a) => now >= a).length - 1);
  // focus glides from the previous card to the current one over 0.35 s
  const focus = idx === 0 ? 0 : idx - 1 + OUT(clamp01((now - at[idx]) / 0.35));
  const total = p.total ?? items.length;
  const H = 300 * s;
  return (
    <AbsoluteFill>
      {items.map((it, i) => {
        const d = i - focus;
        if (Math.abs(d) > 2.2) return null;
        const a = Math.abs(d);
        return (
          <div key={i} style={{ position: "absolute", left: 70, right: 70, top: "50%", translate: `0 ${-H / 2 + d * (H + 30 * s)}px`, scale: 1 - a * 0.1, opacity: 1 - a * 0.42, filter: `blur(${a * 5}px)`, background: t.surface, border: `1.5px solid ${a < 0.5 ? t.accent : t.line}`, borderRadius: t.radius, padding: `${30 * s}px ${40 * s}px`, height: H, display: "flex", flexDirection: "column", justifyContent: "center", gap: 14 * s, textAlign: "left" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 20 }}>
              <span style={{ fontFamily: t.display, fontWeight: t.displayWeight, fontSize: 58 * s, color: t.ink, letterSpacing: "-0.02em" }}><Rich text={it.name} /></span>
              {it.tag && <span style={{ fontFamily: t.mono, fontSize: 26 * s, color: t.accentInk, background: t.accent, padding: "4px 12px", borderRadius: 6, whiteSpace: "nowrap" }}>{it.tag}</span>}
            </div>
            {it.desc && <div style={{ fontFamily: t.sans, fontSize: 38 * s, lineHeight: 1.25, color: t.muted }}><Rich text={it.desc} /></div>}
            {it.meta && <div style={{ fontFamily: t.mono, fontSize: 26 * s, color: t.muted }}>{it.meta}</div>}
          </div>
        );
      })}
      <div style={{ position: "absolute", bottom: 30 * s, left: 0, right: 0, textAlign: "center", fontFamily: t.mono, fontSize: 32 * s, color: t.muted }}>
        {String((p.offset ?? 0) + idx + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
      </div>
    </AbsoluteFill>
  );
};

/** props: title, items: [{name, tag?}] or string[], cols? (1|2), stamp? (e.g. "Screenshot this"), note? (e.g. "checked 12 Nov 2026") */
export const Sheet: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const k = useSpring(0, 18);
  const items: { name: string; tag?: string }[] = (p.items ?? []).map((x: any) => (typeof x === "string" ? { name: x } : x));
  const cols = p.cols ?? (items.length > 8 ? 2 : 1);
  const rows = Math.ceil(items.length / cols);
  const fs = Math.min(cols === 1 ? 58 : 40, 620 / rows) * s;
  const stampIn = useProgress(Math.min(1.0, dur * 0.45), 0.35);
  return (
    <Center>
      <div style={{ position: "relative", width: 940, background: t.surface, border: `1.5px solid ${t.line}`, borderRadius: t.radius, padding: `${40 * s}px ${44 * s}px`, textAlign: "left", opacity: k, scale: interpolate(k, [0, 1], [0.95, 1]) }}>
        <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, textTransform: t.displayCase, fontSize: 60 * s, color: t.ink, letterSpacing: "-0.02em", marginBottom: 8 * s }}><Rich text={p.title ?? ""} /></div>
        {p.note && <div style={{ fontFamily: t.mono, fontSize: 24 * s, color: t.muted, marginBottom: 24 * s }}>{p.note}</div>}
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, 1fr)`, gridAutoFlow: "column", gridTemplateRows: `repeat(${rows}, auto)`, columnGap: 36 * s, rowGap: 10 * s }}>
          {items.map((it, i) => (
            <div key={i} style={{ display: "flex", gap: 14 * s, alignItems: "baseline", fontFamily: t.sans, fontSize: fs, color: t.ink, lineHeight: 1.25 }}>
              <span style={{ fontFamily: t.mono, fontSize: fs * 0.7, color: t.accent, minWidth: fs * 1.4 }}>{String(i + 1).padStart(2, "0")}</span>
              <span style={{ fontWeight: 600 }}>{it.name}</span>
              {it.tag && <span style={{ fontFamily: t.mono, fontSize: fs * 0.62, color: t.muted }}>{it.tag}</span>}
            </div>
          ))}
        </div>
        {p.stamp && (
          <div style={{ position: "absolute", right: -18, top: -34 * s, background: t.accent, color: t.accentInk, fontFamily: t.sans, fontWeight: 800, fontSize: 36 * s, padding: `${10 * s}px ${22 * s}px`, borderRadius: 8, rotate: "4deg", opacity: stampIn, scale: interpolate(stampIn, [0, 1], [1.4, 1]) }}>
            {p.stamp}
          </div>
        )}
      </div>
    </Center>
  );
};
