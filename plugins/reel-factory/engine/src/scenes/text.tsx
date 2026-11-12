import React from "react";
import { AbsoluteFill, interpolate } from "remotion";
import { fmtNum, OUT, stagger, useProgress, useSpring, useT } from "../anim";
import { Rich, stripRich } from "../rich";
import { useStage, useTheme } from "../theme";

export const Center: React.FC<{ children: React.ReactNode; gap?: number; align?: "center" | "left"; pad?: number }> = ({
  children,
  gap = 36,
  align = "center",
  pad = 88,
}) => (
  <AbsoluteFill
    style={{
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: align === "center" ? "center" : "flex-start",
      textAlign: align,
      padding: align === "left" ? `0 120px 0 ${pad}px` : `0 ${pad}px`,
      gap,
    }}
  >
    {children}
  </AbsoluteFill>
);

/** Kinetic headline: lines build word-by-word. props: lines[], kicker?, sub?, size?, align? */
export const Title: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const lines: string[] = p.lines ?? [p.text ?? ""];
  const buildDur = Math.min(dur * 0.55, 0.28 * lines.join(" ").split(/\s+/).length + 0.2);
  const total0 = lines.join(" ").split(/\s+/).length;
  const first = lines[0].split(/\s+/).length / total0;
  const reveal = Math.max(p.instantFirst === false ? 1 / total0 : first, useProgress(0, buildDur, (x) => x));
  const subIn = useProgress(buildDur * 0.8, 0.4);
  const size = (p.size ?? 104) * s;
  const total = lines.reduce((a, l) => a + l.split(/\s+/).length, 0);
  let acc = 0;
  // typewriter: characters type in over ~0.045 s each (capped at 60% of the scene), underscore cursor on the active line
  const lens = lines.map((l) => stripRich(l).length);
  // the first line is on screen from frame 0 (an informative hook frame) unless instantFirst === false
  const tFloor = p.instantFirst === false ? 0 : lens[0];
  const tTotal = lens.reduce((a, b) => a + b, 0);
  const typed = tFloor + useProgress(0, Math.min(dur * 0.6, (tTotal - tFloor) * 0.045 + 0.01), (x) => x) * (tTotal - tFloor);
  const blink = Math.floor(useT() * 2.4) % 2 === 0;
  let cacc = 0;
  return (
    <Center align={p.align ?? "center"} gap={20 * s}>
      {p.kicker && (
        <div style={{ fontFamily: t.mono, fontSize: 30 * s, color: t.muted, letterSpacing: "0.02em" }}>{p.kicker}</div>
      )}
      {lines.map((line, i) => {
        const n = line.split(/\s+/).length;
        const local = Math.max(0, Math.min(1, (reveal * total - acc) / n));
        acc += n;
        return (
          <div
            key={i}
            style={{
              fontFamily: t.display,
              fontWeight: t.displayWeight,
              textTransform: t.displayCase,
              fontSize: size * (t.displayCase === "uppercase" ? 1.12 : 1),
              lineHeight: 1.04,
              letterSpacing: "-0.025em",
              color: t.ink,
            }}
          >
            {p.typewriter ? (
              (() => {
                const n = Math.max(0, Math.min(lens[i], typed - cacc));
                const active = typed >= cacc && typed < cacc + lens[i] + 0.5;
                cacc += lens[i];
                return (
                  <>
                    <Rich text={line} chars={Math.floor(n)} />
                    {active && <span style={{ color: t.accent, opacity: blink ? 1 : 0 }}>_</span>}
                  </>
                );
              })()
            ) : (
              <Rich text={line} reveal={local} />
            )}
          </div>
        );
      })}
      {p.sub && (
        <div style={{ fontFamily: t.sans, fontSize: 42 * s, color: t.muted, opacity: subIn, translate: `0 ${(1 - subIn) * 20}px`, maxWidth: 860 }}>
          <Rich text={p.sub} />
        </div>
      )}
    </Center>
  );
};

/** Full-screen pattern interrupt: one big phrase, optional stamp style. props: text, style: big|stamp */
export const Punch: React.FC<{ p: any; dur: number }> = ({ p }) => {
  const t = useTheme();
  const { s } = useStage();
  const k = useSpring(0, 11, 0.5);
  const stamp = p.style === "stamp";
  return (
    <Center>
      <div
        style={{
          fontFamily: t.display,
          fontWeight: t.displayWeight,
          textTransform: t.displayCase,
          fontSize: (p.size ?? 150) * s,
          lineHeight: 0.98,
          letterSpacing: "-0.035em",
          // tone "accent": stamps take the accent colour; big text becomes an accent slab (cinematic signature)
          color: p.tone === "accent" ? (stamp ? t.accent : t.accentInk) : stamp ? t.bad : t.ink,
          background: p.tone === "accent" && !stamp ? t.accent : undefined,
          border: stamp ? `10px solid ${p.tone === "accent" ? t.accent : t.bad}` : undefined,
          padding: stamp ? "10px 34px" : p.tone === "accent" ? "6px 30px 14px" : undefined,
          rotate: stamp ? "-6deg" : "0deg",
          scale: interpolate(k, [0, 1], [stamp ? 1.6 : 0.86, 1]),
          opacity: Math.min(1, k * 1.6),
        }}
      >
        <Rich text={p.text} />
      </div>
      {p.sub && <div style={{ fontFamily: t.sans, fontSize: 44 * s, color: t.muted, opacity: k }}><Rich text={p.sub} /></div>}
    </Center>
  );
};

/** Big number with count-up. props: value, from?, prefix?, suffix?, decimals?, label, sub?, source? */
export const Stat: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const prog = useProgress(0.1, Math.min(1.4, dur * 0.5));
  const lab = useProgress(0.3, 0.5);
  const v = (p.from ?? 0) + (p.value - (p.from ?? 0)) * prog;
  return (
    <Center gap={18 * s}>
      <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, fontSize: (p.size ?? 220) * s, lineHeight: 1, letterSpacing: "-0.05em", color: t.ink, fontVariantNumeric: "tabular-nums" }}>
        {p.prefix ?? ""}
        {fmtNum(v, p.decimals ?? 0)}
        <span style={{ color: t.accent }}>{p.suffix ?? ""}</span>
      </div>
      <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 52 * s, color: t.ink, opacity: lab, maxWidth: 880 }}>
        <Rich text={p.label} />
      </div>
      {p.sub && <div style={{ fontFamily: t.sans, fontSize: 38 * s, color: t.muted, opacity: lab, maxWidth: 860 }}><Rich text={p.sub} /></div>}
      {p.source && <div style={{ fontFamily: t.mono, fontSize: 26 * s, color: t.muted, opacity: lab, marginTop: 12 }}>source: {p.source}</div>}
    </Center>
  );
};

/** Progressive numbered list / checklist. props: title?, items[], numbered?, check?, active? (highlight index) */
export const List: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const time = useT();
  const items: string[] = p.items ?? [];
  const at: number[] = p.revealAt ?? stagger(items.length, dur);
  const titleIn = useProgress(0, 0.4);
  const fs = (items.length > 6 ? 44 : 54) * s;
  return (
    <Center align="left" gap={22 * s} pad={96}>
      {p.title && (
        <div style={{ fontFamily: t.display, fontWeight: t.displayWeight, textTransform: t.displayCase, fontSize: 76 * s, lineHeight: 1.05, letterSpacing: "-0.02em", color: t.ink, opacity: titleIn, marginBottom: 18 * s }}>
          <Rich text={p.title} />
        </div>
      )}
      {items.map((it, i) => {
        const k = Math.max(0, Math.min(1, (time - at[i]) / 0.35));
        const e = OUT(k);
        const done = p.check && time > at[i] + 0.3;
        return (
          <div key={i} style={{ display: "flex", alignItems: "baseline", gap: 26 * s, opacity: interpolate(e, [0, 1], [0.0, 1]), translate: `${(1 - e) * 50}px 0` }}>
            <span style={{ fontFamily: t.mono, fontSize: fs * 0.62, color: done ? t.good : t.accent, minWidth: 64 * s, fontWeight: 600 }}>
              {p.check ? (done ? "✓" : "○") : String(i + 1).padStart(2, "0")}
            </span>
            <span style={{ fontFamily: t.sans, fontWeight: 700, fontSize: fs, lineHeight: 1.15, color: t.ink, letterSpacing: "-0.01em" }}>
              <Rich text={it} />
            </span>
          </div>
        );
      })}
    </Center>
  );
};

/** Tweet / blog / doc quote with highlighter sweep. props: text, highlight[], author?, handle?, source? */
export const Quote: React.FC<{ p: any; dur: number }> = ({ p, dur }) => {
  const t = useTheme();
  const { s } = useStage();
  const k = useSpring(0, 16);
  const now = useT();
  const sweepAll = useProgress(0.5, Math.min(1.6, dur * 0.5));
  const hl: string[] = p.highlight ?? [];
  const hAt: number[] | undefined = p.highlightAt; // per-phrase start (s), from build.py speech sync
  const sweepOf = (j: number) => (hAt ? OUT(Math.max(0, Math.min(1, (now - hAt[j]) / 0.5))) : sweepAll);
  // split text around highlight phrases
  const parts: { txt: string; hi: boolean; j: number }[] = [];
  let rest: string = p.text;
  hl.forEach((h, j) => {
    const i = rest.indexOf(h);
    if (i < 0) return;
    parts.push({ txt: rest.slice(0, i), hi: false, j }, { txt: h, hi: true, j });
    rest = rest.slice(i + h.length);
  });
  parts.push({ txt: rest, hi: false, j: -1 });
  return (
    <Center>
      <div
        style={{
          background: t.surface,
          border: `1.5px solid ${t.line}`,
          borderRadius: t.radius,
          padding: `${44 * s}px ${48 * s}px`,
          width: 940,
          textAlign: "left",
          scale: interpolate(k, [0, 1], [0.94, 1]),
          opacity: k,
        }}
      >
        {(p.author || p.source) && (
          <div style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 26 * s }}>
            <div style={{ width: 64 * s, height: 64 * s, borderRadius: 999, background: t.accent, color: t.accentInk, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: t.sans, fontWeight: 800, fontSize: 30 * s }}>
              {(p.author ?? p.source ?? "?").slice(0, 1).toUpperCase()}
            </div>
            <div>
              <div style={{ fontFamily: t.sans, fontWeight: 700, fontSize: 34 * s, color: t.ink }}>{p.author ?? p.source}</div>
              {p.handle && <div style={{ fontFamily: t.mono, fontSize: 26 * s, color: t.muted }}>{p.handle}</div>}
            </div>
          </div>
        )}
        <div style={{ fontFamily: t.sans, fontSize: (p.size ?? 50) * s, lineHeight: 1.32, color: t.ink }}>
          {parts.map((x, i) =>
            x.hi ? (
              <span
                key={i}
                style={{
                  backgroundImage: `linear-gradient(${t.accent}, ${t.accent})`,
                  backgroundRepeat: "no-repeat",
                  backgroundSize: `${sweepOf(x.j) * 100}% 100%`,
                  color: sweepOf(x.j) > 0.5 ? t.accentInk : t.ink,
                  padding: "0 4px",
                  fontWeight: 700,
                }}
              >
                {x.txt}
              </span>
            ) : (
              <span key={i}>{x.txt}</span>
            ),
          )}
        </div>
        {p.source && p.author && <div style={{ fontFamily: t.mono, fontSize: 24 * s, color: t.muted, marginTop: 26 * s }}>{p.source}</div>}
      </div>
    </Center>
  );
};
