import React from "react";
import { AbsoluteFill, Img, interpolate } from "remotion";
import { fmtNum, OUT, stagger, useProgress, useSpring, useT } from "../anim";
import { Rich } from "../rich";
import { useStage, useTheme } from "../theme";
import { Center } from "./text";
import { src } from "./ui";

const Tile: React.FC<{ label: string; size: number; bg?: string; fg?: string }> = ({ label, size, bg, fg }) => {
  const t = useTheme();
  const letters = label.replace(/[^A-Za-z0-9]/g, "").slice(0, 2) || "•";
  return (
    <div style={{ width: size, height: size, borderRadius: t.radius, background: bg ?? t.ink, color: fg ?? t.bg, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: t.sans, fontWeight: 800, fontSize: size * 0.38, letterSpacing: "-0.03em", flexShrink: 0 }}>
      {letters.charAt(0).toUpperCase() + letters.slice(1).toLowerCase()}
    </div>
  );
};

/** Listicle item. props: index, total, name, desc, tag?, stars?, image?, url? */
export const Item: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const k = useSpring(0, 15);
  const d = useProgress(0.35, 0.5);
  const st = useProgress(0.5, Math.min(1.2, dur * 0.5));
  return (
    <Center gap={34 * s} align="left" pad={96}>
      <div style={{ fontFamily: t.mono, fontSize: 34 * s, color: t.accent, fontWeight: 600, opacity: k }}>
        {String(p.index).padStart(2, "0")} / {String(p.total).padStart(2, "0")}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 30 * s, translate: `${(1 - k) * 60}px 0`, opacity: k }}>
        <Tile label={p.name} size={128 * s} bg={t.accent} fg={t.accentInk} />
        <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, textTransform: t.displayCase, fontSize: (p.name.length > 14 ? 78 : 96) * s, lineHeight: 1, letterSpacing: "-0.03em", color: t.ink }}>
          {p.name}
        </div>
      </div>
      <div style={{ fontFamily: t.sans, fontSize: 48 * s, lineHeight: 1.3, color: t.ink, opacity: d, translate: `0 ${(1 - d) * 18}px`, maxWidth: 880 }}>
        <Rich text={p.desc} />
      </div>
      {p.image && (
        <div style={{ width: 888, borderRadius: t.radius, overflow: "hidden", border: `1.5px solid ${t.line}`, opacity: d }}>
          <Img src={src(p.image)} style={{ width: "100%", display: "block", maxHeight: 520 * s, objectFit: "cover", objectPosition: "top" }} />
        </div>
      )}
      <div style={{ display: "flex", gap: 22, fontFamily: t.mono, fontSize: 32 * s, color: t.muted, opacity: d }}>
        {p.stars != null && <span><span style={{ color: t.accent }}>★</span> {fmtNum(Math.round(p.stars * st))}</span>}
        {p.tag && <span style={{ border: `1.5px solid ${t.line}`, padding: "4px 14px", borderRadius: 6 }}>{p.tag}</span>}
        {p.url && <span>{p.url}</span>}
      </div>
    </Center>
  );
};

/** Horizontal comparison bars. props: title?, unit?, bars:[{label, value, highlight?}], note? */
export const Bars: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const grow = useProgress(0.3, Math.min(1.4, dur * 0.5));
  const bars: { label: string; value: number; highlight?: boolean }[] = p.bars ?? [];
  const max = Math.max(...bars.map((b) => b.value), 1);
  return (
    <Center align="left" gap={34 * s} pad={96}>
      {p.title && <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, textTransform: t.displayCase, fontSize: 72 * s, lineHeight: 1.05, color: t.ink, letterSpacing: "-0.02em" }}><Rich text={p.title} /></div>}
      {bars.map((b, i) => {
        const g = OUT(Math.max(0, Math.min(1, grow * 1.3 - i * 0.12)));
        return (
          <div key={i} style={{ width: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: t.sans, fontSize: 38 * s, fontWeight: 700, color: b.highlight ? t.ink : t.muted, marginBottom: 10 }}>
              <span>{b.label}</span>
              <span style={{ fontFamily: t.mono, fontVariantNumeric: "tabular-nums" }}>{fmtNum(b.value * g, p.decimals ?? 0)}{p.unit ?? ""}</span>
            </div>
            <div style={{ height: 44 * s, background: t.line, borderRadius: 6, overflow: "hidden" }}>
              <div style={{ width: `${(b.value / max) * 100 * g}%`, height: "100%", background: b.highlight ? t.accent : t.muted, borderRadius: 6 }} />
            </div>
          </div>
        );
      })}
      {p.note && <div style={{ fontFamily: t.mono, fontSize: 26 * s, color: t.muted }}>{p.note}</div>}
    </Center>
  );
};

/** Sequential pipeline. props: title?, nodes:[string], direction?: 'down' */
export const Flow: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const time = useT();
  const nodes: string[] = p.nodes ?? [];
  const at: number[] = p.revealAt ?? stagger(nodes.length, dur, 0.3, 0.5);
  return (
    <Center gap={0}>
      {p.title && <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, textTransform: t.displayCase, fontSize: 64 * s, color: t.ink, marginBottom: 40 * s, letterSpacing: "-0.02em" }}><Rich text={p.title} /></div>}
      {nodes.map((n, i) => {
        const k = OUT(Math.max(0, Math.min(1, (time - at[i]) / 0.35)));
        const active = time >= at[i] && (i === nodes.length - 1 || time < at[i + 1]);
        return (
          <React.Fragment key={i}>
            {i > 0 && <div style={{ width: 4, height: 54 * s * k, background: t.line, margin: "6px 0" }} />}
            <div style={{ opacity: k, scale: interpolate(k, [0, 1], [0.9, 1]), minWidth: 560, padding: `${22 * s}px ${36 * s}px`, borderRadius: t.radius, background: active ? t.accent : t.surface, color: active ? t.accentInk : t.ink, border: `1.5px solid ${active ? t.accent : t.line}`, fontFamily: t.sans, fontWeight: 700, fontSize: 42 * s, display: "flex", gap: 22, alignItems: "center" }}>
              <span style={{ fontFamily: t.mono, fontSize: 28 * s, opacity: 0.7 }}>{String(i + 1).padStart(2, "0")}</span>
              <Rich text={n} />
            </div>
          </React.Fragment>
        );
      })}
    </Center>
  );
};

/** Hub and spokes. props: center, spokes:[string] */
export const Hub: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s, w, h } = useStage();
  const time = useT();
  const spokes: string[] = p.spokes ?? [];
  const at = stagger(spokes.length, dur, 0.4, 0.5);
  const R = Math.min(300 * s, w * 0.3);
  const cx = w / 2;
  const cy = h / 2;
  const c = useSpring(0, 13);
  return (
    <AbsoluteFill>
      <svg width={w} height={h} style={{ position: "absolute" }}>
        {spokes.map((_, i) => {
          const a = (i / spokes.length) * Math.PI * 2 - Math.PI / 2;
          const k = Math.max(0, Math.min(1, (time - at[i]) / 0.3));
          return <line key={i} x1={cx} y1={cy} x2={cx + Math.cos(a) * R * k} y2={cy + Math.sin(a) * R * k} stroke={t.line} strokeWidth={4} />;
        })}
      </svg>
      <div style={{ position: "absolute", left: cx, top: cy, translate: "-50% -50%", scale: c, padding: `${30 * s}px ${40 * s}px`, borderRadius: t.radius, background: t.accent, color: t.accentInk, fontFamily: t.display, fontWeight: t.displayWeight, fontSize: 56 * s, whiteSpace: "nowrap" }}>
        {p.center}
      </div>
      {spokes.map((sp, i) => {
        const a = (i / spokes.length) * Math.PI * 2 - Math.PI / 2;
        const k = OUT(Math.max(0, Math.min(1, (time - at[i] - 0.15) / 0.35)));
        return (
          <div key={i} style={{ position: "absolute", left: cx + Math.cos(a) * R, top: cy + Math.sin(a) * R, translate: "-50% -50%", opacity: k, scale: interpolate(k, [0, 1], [0.7, 1]), background: t.surface, border: `1.5px solid ${t.line}`, borderRadius: t.radius, padding: `${16 * s}px ${24 * s}px`, fontFamily: t.sans, fontWeight: 700, fontSize: 40 * s, color: t.ink, whiteSpace: "nowrap" }}>
            {sp}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Old way vs new way. props: left:{title, points[]}, right:{title, points[]} */
export const Versus: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const l = useSpring(0, 15);
  const r = useSpring(Math.min(1.2, dur * 0.4), 15);
  const Col: React.FC<{ d: any; good: boolean; k: number; tag: string }> = ({ d, good, k, tag }) => (
    <div style={{ flex: 1, opacity: k, translate: `0 ${(1 - k) * 40}px`, background: good ? t.surface : "transparent", border: `1.5px solid ${good ? t.accent : t.line}`, borderRadius: t.radius, padding: 30 * s, display: "flex", flexDirection: "column", gap: 20 * s, textAlign: "left" }}>
      <div style={{ fontFamily: t.mono, fontSize: 28 * s, color: good ? t.accent : t.muted, fontWeight: 600 }}>{tag}</div>
      <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, fontSize: 62 * s, color: t.ink, lineHeight: 1.05, textTransform: t.displayCase }}><Rich text={d.title} /></div>
      {(d.points ?? []).map((x: string, i: number) => (
        <div key={i} style={{ fontFamily: t.sans, fontSize: 46 * s, lineHeight: 1.25, color: good ? t.ink : t.muted, display: "flex", gap: 12 }}>
          <span style={{ color: good ? t.good : t.bad, fontWeight: 800 }}>{good ? "✓" : "✗"}</span>
          <span>{x}</span>
        </div>
      ))}
    </div>
  );
  return (
    <Center>
      <div style={{ display: "flex", gap: 26 * s, width: 940 }}>
        <Col d={p.left} good={false} k={l} tag={p.leftTag ?? "OLD"} />
        <Col d={p.right} good k={r} tag={p.rightTag ?? "NEW"} />
      </div>
    </Center>
  );
};

/** Grid of named tiles (tools, logos). props: title?, items:[{label, sub?}], highlight?: number[] */
export const Grid: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const time = useT();
  const items: { label: string; sub?: string }[] = p.items ?? [];
  const cols = p.cols ?? (items.length > 12 ? 5 : items.length > 6 ? 4 : 3);
  const size = (900 - (cols - 1) * 18) / cols;
  const at = stagger(items.length, Math.min(dur, 2.4), 0.2, 0.2);
  const hl: number[] = p.highlight ?? [];
  return (
    <Center gap={36 * s}>
      {p.title && <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, textTransform: t.displayCase, fontSize: 72 * s, color: t.ink, letterSpacing: "-0.02em", lineHeight: 1.05 }}><Rich text={p.title} /></div>}
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, ${size}px)`, gap: 18 }}>
        {items.map((it, i) => {
          const k = OUT(Math.max(0, Math.min(1, (time - at[i]) / 0.3)));
          const on = hl.includes(i);
          return (
            <div key={i} style={{ opacity: k, scale: interpolate(k, [0, 1], [0.6, 1]), display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
              <Tile label={it.label} size={size * 0.78} bg={on ? t.accent : t.surface} fg={on ? t.accentInk : t.ink} />
              <div style={{ fontFamily: t.sans, fontWeight: 600, fontSize: Math.max(20, size * 0.15) * s, color: t.ink, textAlign: "center", lineHeight: 1.1 }}>{it.label}</div>
            </div>
          );
        })}
      </div>
    </Center>
  );
};
