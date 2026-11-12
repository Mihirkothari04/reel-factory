import React from "react";
import { useTheme } from "./theme";

/**
 * Inline markup for on-screen text:
 *   *phrase*  → emphasis: italic serif in accent colour (the corpus' signature emphasis)
 *   [phrase]  → selection box: accent fill + corner handles (Figma-style highlight)
 *   _phrase_  → muted
 */
type Tok = { text: string; kind: "plain" | "em" | "box" | "mute" };

export const parseRich = (src: string): Tok[] => {
  const out: Tok[] = [];
  const re = /\*([^*]+)\*|\[([^\]]+)\]|_([^_]+)_/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(src))) {
    if (m.index > last) out.push({ text: src.slice(last, m.index), kind: "plain" });
    out.push({ text: m[1] ?? m[2] ?? m[3], kind: m[1] ? "em" : m[2] ? "box" : "mute" });
    last = re.lastIndex;
  }
  if (last < src.length) out.push({ text: src.slice(last), kind: "plain" });
  return out;
};

export const stripRich = (src: string) => parseRich(src).map((t) => t.text).join("");

const Handles: React.FC<{ color: string }> = ({ color }) => {
  const s: React.CSSProperties = { position: "absolute", width: 10, height: 10, background: "#fff", border: `2px solid ${color}` };
  return (
    <>
      <span style={{ ...s, left: -6, top: -6 }} />
      <span style={{ ...s, right: -6, top: -6 }} />
      <span style={{ ...s, left: -6, bottom: -6 }} />
      <span style={{ ...s, right: -6, bottom: -6 }} />
    </>
  );
};

/** Renders rich text; `reveal` (0..1) reveals words progressively (word-by-word build). */
export const Rich: React.FC<{ text: string; reveal?: number; chars?: number; style?: React.CSSProperties; emColor?: string }> = ({
  text,
  reveal = 1,
  chars,
  style,
  emColor,
}) => {
  const t = useTheme();
  const toks = parseRich(text);
  // split into words keeping token kind, so reveal works per word
  const words: { w: string; kind: Tok["kind"]; group: number }[] = [];
  toks.forEach((tok, gi) => tok.text.split(/(\s+)/).forEach((w) => w && words.push({ w, kind: tok.kind, group: gi })));
  const visible = words.filter((x) => x.w.trim()).length;
  let shown = 0;
  const cut = Math.ceil(reveal * visible - 1e-6);

  // regroup consecutive words of same group for box rendering
  const groups: { kind: Tok["kind"]; parts: { w: string; on: boolean }[] }[] = [];
  let budget = chars ?? Infinity; // typewriter: characters still allowed to show
  words.forEach((x) => {
    if (chars !== undefined) {
      const vis = x.w.slice(0, Math.max(0, budget));
      budget -= x.w.length;
      x = { ...x, w: vis };
      if (!vis) return;
    }
    const on = chars !== undefined ? true : x.w.trim() ? ++shown <= cut : shown <= cut;
    const g = groups[groups.length - 1];
    if (g && (g as any).gi === x.group) g.parts.push({ w: x.w, on });
    else groups.push(Object.assign({ kind: x.kind, parts: [{ w: x.w, on }] }, { gi: x.group }));
  });

  return (
    <span style={style}>
      {groups.map((g, i) => {
        const inner = g.parts.map((p, j) => (
          <span key={j} style={{ opacity: p.on ? 1 : 0, transition: "none" }}>
            {p.w}
          </span>
        ));
        const anyOn = g.parts.some((p) => p.on && p.w.trim());
        if (g.kind === "em")
          return (
            <span key={i} style={{ fontFamily: t.serif, fontStyle: "italic", fontWeight: 400, color: emColor ?? t.accent, letterSpacing: "-0.01em", textTransform: "none" }}>
              {inner}
            </span>
          );
        if (g.kind === "box")
          return (
            <span key={i} style={{ position: "relative", display: "inline-block", padding: "0 0.18em", margin: "0 0.06em", background: anyOn ? t.accent : "transparent", color: t.accentInk, borderRadius: 2 }}>
              {inner}
              {anyOn && <Handles color={t.accent} />}
            </span>
          );
        if (g.kind === "mute") return <span key={i} style={{ color: t.muted }}>{inner}</span>;
        return <span key={i}>{inner}</span>;
      })}
    </span>
  );
};
