import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fmtNum, OUT } from "../anim";
import { src } from "../scenes/ui";
import { StageCtx, ThemeCtx } from "../theme";
import type { Look } from "./looks";
import type { Gfx } from "./types";

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** Overlay graphics on top of shots and presenter: cut-out stickers, mono labels, display-type slams, counters, boxed scenes. */
export const GfxView: React.FC<{ g: Gfx; look: Look; registry: Record<string, React.FC<{ p: any; dur: number }>> }> = ({ g, look, registry }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const dur = g.to - g.from;
  const pop = spring({ frame, fps, config: { damping: 13, mass: 0.6 } });
  const out = clamp01((dur - t) / 0.2); // quick exit
  const th = look.theme;
  const x = g.x ?? 540, y = g.y ?? 600;

  if (g.kind === "sticker" && g.src) {
    const w = g.w ?? 520;
    return (
      <div style={{ position: "absolute", left: x - w / 2, top: y, width: w, opacity: out, transform: `rotate(${g.rot ?? 0}deg) scale(${interpolate(pop, [0, 1], [0.6, 1])})`, transformOrigin: "50% 80%" }}>
        <Img src={src(g.src)} style={{ width: "100%", display: "block", filter: "drop-shadow(0 18px 30px rgba(0,0,0,.45))" }} />
        {g.strike && (
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: "-6%", width: "112%", height: "112%", overflow: "visible" }}>
            <line x1="6" y1="94" x2={6 + 88 * OUT(clamp01((t - 0.35) / 0.25))} y2={94 - 88 * OUT(clamp01((t - 0.35) / 0.25))} stroke={g.color ?? "#E5322D"} strokeWidth={22} strokeLinecap="round" vectorEffect="non-scaling-stroke" />
          </svg>
        )}
        {g.text && (
          <div style={{ position: "absolute", left: "50%", bottom: -18, translate: "-50% 0", background: look.labelBg, color: look.labelInk, fontFamily: th.mono, fontSize: 28, fontWeight: 600, padding: "6px 14px", borderRadius: 8, whiteSpace: "nowrap" }}>{g.text}</div>
        )}
      </div>
    );
  }
  if (g.kind === "label") {
    const k = OUT(clamp01(t / 0.25));
    return (
      <div style={{ position: "absolute", left: x, top: y, translate: "-50% 0", opacity: k * out, background: g.color ?? look.labelBg, color: look.labelInk, fontFamily: th.mono, fontSize: 30, fontWeight: 600, padding: "10px 18px", borderRadius: 10, whiteSpace: "nowrap", letterSpacing: "0.02em", display: "flex", alignItems: "center", gap: 12 }}>
        {g.icon && <Img src={src(g.icon)} style={{ height: 40, width: "auto", display: "block" }} />}
        {g.text}
      </div>
    );
  }
  if (g.kind === "callout") {
    // a tag joined to the thing it names by a leader line that draws from the target: flaw autopsies, labelled parts
    const tx = g.tx ?? x, ty = g.ty ?? y;
    const k = OUT(clamp01(t / 0.3));
    const c = g.color ?? "#E5322D";
    return (
      <div style={{ position: "absolute", inset: 0, opacity: out }}>
        <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
          <circle cx={tx} cy={ty} r={11 * Math.min(1, pop * 1.4)} fill={c} />
          <line x1={tx} y1={ty} x2={tx + (x - tx) * k} y2={ty + (y - ty) * k} stroke={c} strokeWidth={5} strokeLinecap="round" />
        </svg>
        <div style={{ position: "absolute", left: x, top: y, translate: "-50% -50%", scale: interpolate(clamp01((t - 0.2) / 0.2), [0, 1], [0.7, 1]), opacity: clamp01((t - 0.2) / 0.15), background: c, color: "#FFFFFF", fontFamily: th.mono, fontSize: 30, fontWeight: 700, padding: "10px 18px", borderRadius: 8, whiteSpace: "nowrap", textTransform: "uppercase", boxShadow: "0 10px 30px rgba(0,0,0,.35)" }}>
          {g.text}
        </div>
      </div>
    );
  }
  if (g.kind === "slam") {
    const s = interpolate(pop, [0, 1], [1.5, 1]);
    return (
      <div style={{ position: "absolute", left: 50, right: 50, top: y, textAlign: "center", opacity: Math.min(1, pop * 2) * out, scale: s }}>
        <div style={{ fontFamily: th.display, fontWeight: 900, fontSize: g.h ?? 150, lineHeight: 0.95, color: g.color ?? "#FFFFFF", letterSpacing: "-0.03em", textTransform: "uppercase", textShadow: "0 8px 30px rgba(0,0,0,.45)" }}>{g.text}</div>
        {g.sub && <div style={{ fontFamily: th.serif, fontStyle: "italic", fontSize: (g.h ?? 150) * 0.45, color: "#FFFFFF", marginTop: 10, textShadow: "0 6px 24px rgba(0,0,0,.5)" }}>{g.sub}</div>}
      </div>
    );
  }
  if (g.kind === "counter") {
    const k = OUT(clamp01(t / Math.min(1.4, dur * 0.7)));
    const v = (g.fromValue ?? 0) + ((g.value ?? 0) - (g.fromValue ?? 0)) * k;
    return (
      <div style={{ position: "absolute", left: 40, right: 40, top: y, textAlign: "center", opacity: Math.min(1, pop * 2) * out }}>
        <div style={{ fontFamily: th.display, fontWeight: 900, fontSize: g.h ?? 210, lineHeight: 1, color: g.color ?? look.capAccent, letterSpacing: "-0.04em", textShadow: "0 10px 40px rgba(0,0,0,.35)" }}>
          {g.prefix ?? ""}{fmtNum(v, g.decimals ?? 0)}{g.suffix ?? ""}
        </div>
        {g.text && <div style={{ fontFamily: th.mono, fontSize: 32, color: "#FFFFFF", marginTop: 12, textShadow: "0 4px 16px rgba(0,0,0,.6)" }}>{g.text}</div>}
      </div>
    );
  }
  if (g.kind === "scene" && g.type && registry[g.type]) {
    const Comp = registry[g.type];
    const w = g.w ?? 980, h = g.h ?? 700;
    return (
      <div style={{ position: "absolute", left: x - w / 2, top: y, width: w, height: h, opacity: out, scale: interpolate(pop, [0, 1], [0.9, 1]) }}>
        <ThemeCtx.Provider value={look.theme}>
          <StageCtx.Provider value={{ w, h, s: Math.min(1, h / 1100), first: false }}>
            <Comp p={g.props ?? {}} dur={dur} />
          </StageCtx.Provider>
        </ThemeCtx.Provider>
      </div>
    );
  }
  return null;
};
