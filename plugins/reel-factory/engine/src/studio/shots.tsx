import React from "react";
import { AbsoluteFill, Easing, Img, OffthreadVideo, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { OUT } from "../anim";
import { src } from "../scenes/ui";
import { StageCtx, ThemeCtx } from "../theme";
import type { Look } from "./looks";
import type { CamKey, Mark, Shot } from "./types";

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const SMOOTH = Easing.bezier(0.45, 0, 0.2, 1);

/** camera state at shot-time t: eased between keyframes (each move takes up to 0.7 s, then holds and drifts) */
export const camAt = (keys: CamKey[], t: number): CamKey => {
  if (!keys.length) return { t: 0, x: 0.5, y: 0.5, z: 1 };
  let i = 0;
  for (let j = 0; j < keys.length; j++) if (keys[j].t <= t) i = j;
  const a = keys[Math.max(0, i - 1)], b = keys[i];
  if (i === 0 || a === b) {
    const drift = 1 + 0.012 * Math.max(0, t - b.t);
    return { ...b, z: b.z * Math.min(drift, 1.06) };
  }
  const span = Math.min(0.7, Math.max(0.2, b.t - a.t));
  const k = SMOOTH(clamp01((t - b.t) / span));
  const drift = 1 + 0.01 * Math.max(0, t - b.t - span);
  return { t, x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, z: (a.z + (b.z - a.z) * k) * Math.min(drift, 1.05) };
};

/** Media that fills the box and is moved by a virtual camera. Focus point (x,y) is kept as close to centre as the edges allow. */
const CameraMedia: React.FC<{ w: number; h: number; aspect: number; fit: string; cam: CamKey; children: React.ReactNode }> = ({ w, h, aspect, fit, cam, children }) => {
  // base size at z=1
  let W = w, H = w / aspect;
  if (fit === "cover" && H < h) { H = h; W = h * aspect; }
  if (fit === "contain" && H > h) { H = h; W = h * aspect; }
  const z = cam.z;
  const SW = W * z, SH = H * z;
  let tx = w / 2 - cam.x * SW, ty = h / 2 - cam.y * SH;
  tx = SW >= w ? Math.min(0, Math.max(w - SW, tx)) : (w - SW) / 2;
  ty = SH >= h ? Math.min(0, Math.max(h - SH, ty)) : (h - SH) / 2;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transform: `translate(${tx}px, ${ty}px) scale(${z})`, transformOrigin: "0 0" }}>{children}</div>
  );
};

const Marks: React.FC<{ marks: Mark[]; t: number; color: string }> = ({ marks, t, color }) => (
  <>
    {marks.map((m, i) => {
      const total = m.rects.reduce((a, r) => a + r.w, 0) || 1;
      const e = OUT(clamp01((t - m.at) / Math.max(0.35, 0.16 * m.rects.length + 0.3)));
      let done = 0;
      return m.rects.map((r, j) => {
        const share = clamp01((e * total - done) / r.w);
        done += r.w;
        if (share <= 0) return null;
        const col = m.color ?? color;
        const st = m.style ?? "marker";
        const box: React.CSSProperties = { position: "absolute", left: `${r.x * 100}%`, width: `${r.w * share * 100}%` };
        if (st === "strike") return <div key={`${i}-${j}`} style={{ ...box, top: `${(r.y + r.h * 0.48) * 100}%`, height: `${Math.max(0.003, r.h * 0.11) * 100}%`, background: col ?? "#E5484D" }} />;
        if (st === "underline") return <div key={`${i}-${j}`} style={{ ...box, top: `${(r.y + r.h * 0.9) * 100}%`, height: `${Math.max(0.004, r.h * 0.14) * 100}%`, background: col }} />;
        if (st === "box") return <div key={`${i}-${j}`} style={{ ...box, top: `${(r.y - r.h * 0.08) * 100}%`, height: `${r.h * 1.16 * 100}%`, border: `5px solid ${col}`, borderRadius: 8, opacity: share }} />;
        return <div key={`${i}-${j}`} style={{ ...box, top: `${r.y * 100}%`, height: `${r.h * 100}%`, background: col, mixBlendMode: "multiply", borderRadius: 3 }} />;
      });
    })}
  </>
);

// source chip: bottom-left on full-height content, top-left when the box ends at a caption seam (split)
const Label: React.FC<{ text: string; look: Look; top?: boolean }> = ({ text, look, top }) => (
  <div style={{ position: "absolute", left: 40, ...(top ? { top: 40 } : { bottom: 40 }), background: look.labelBg, color: look.labelInk, fontFamily: look.theme.mono, fontSize: 26, fontWeight: 600, padding: "8px 16px", borderRadius: 8, letterSpacing: "0.02em" }}>{text}</div>
);

/** incoming transition of a shot (first ~0.3 s) */
const enterStyle = (enter: string, t: number): React.CSSProperties => {
  const k = OUT(clamp01(t / 0.32));
  if (enter === "blur") return { filter: `blur(${(1 - k) * 22}px)`, opacity: Math.min(1, k * 1.6) };
  if (enter === "zoom") return { scale: interpolate(k, [0, 1], [1.16, 1]), filter: `blur(${(1 - k) * 10}px)`, opacity: Math.min(1, k * 2) };
  if (enter === "whip") return { translate: `${(1 - k) * 420}px 0`, filter: `blur(${(1 - k) * 26}px)` };
  if (enter === "slide") return { translate: `0 ${(1 - k) * 160}px`, opacity: Math.min(1, k * 1.8) };
  return {};
};

export const ShotView: React.FC<{ shot: Shot; w: number; h: number; look: Look; registry: Record<string, React.FC<{ p: any; dur: number }>>; field?: string }> = ({ shot, w, h, look, registry, field }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const dur = shot.to - shot.from;
  const enter = shot.enter ?? "cut";
  let body: React.ReactNode = null;

  if (shot.kind === "scene" && shot.type && registry[shot.type]) {
    const Comp = registry[shot.type];
    const s = Math.min(1.4, Math.max(0.9, h / 800));
    body = (
      <ThemeCtx.Provider value={field ? { ...look.theme, bg: field } : look.theme}>
        <StageCtx.Provider value={{ w, h, s, first: false }}>
          {/* slow camera drift: a graphic card never sits perfectly still once its reveals are done */}
          <AbsoluteFill style={{ scale: interpolate(t, [0, Math.max(1, dur)], [1, 1.045]), translate: `0 ${interpolate(t, [0, Math.max(1, dur)], [0, -14])}px` }}>
            <Comp p={shot.props ?? {}} dur={dur} />
          </AbsoluteFill>
        </StageCtx.Provider>
      </ThemeCtx.Provider>
    );
  } else if (shot.kind === "image" && shot.src) {
    const keys = shot.cam?.length ? shot.cam : [{ t: 0, x: 0.5, y: 0.35, z: 1 }];
    const cam = camAt(keys, t);
    const aspect = shot.aspect ?? 0.75;
    const fit = shot.fit ?? (aspect < w / h ? "width" : "cover");
    body = (
      <>
        {fit === "blurfill" && <Img src={src(shot.src)} style={{ position: "absolute", inset: -60, width: w + 120, height: h + 120, objectFit: "cover", filter: "blur(40px) brightness(.55)" }} />}
        <CameraMedia w={w} h={h} aspect={aspect} fit={fit === "blurfill" ? "contain" : fit} cam={cam}>
          <Img src={src(shot.src)} style={{ width: "100%", height: "100%", display: "block" }} />
          {shot.marks && <Marks marks={shot.marks} t={t} color={look.marker} />}
        </CameraMedia>
      </>
    );
  } else if (shot.kind === "video" && shot.src) {
    const push = interpolate(t, [0, Math.max(1, dur)], [1, 1.06]);
    const startFrom = Math.round((shot.trim ?? 0) * fps);
    const fit = shot.fit ?? "cover";
    body = (
      <>
        {fit === "blurfill" && (
          <OffthreadVideo src={src(shot.src)} startFrom={startFrom} muted style={{ position: "absolute", inset: -60, width: w + 120, height: h + 120, objectFit: "cover", filter: "blur(40px) brightness(.5)" }} />
        )}
        <AbsoluteFill style={{ scale: push }}>
          <OffthreadVideo src={src(shot.src)} startFrom={startFrom} muted style={{ width: w, height: h, objectFit: fit === "blurfill" || fit === "contain" ? "contain" : "cover" }} />
        </AbsoluteFill>
      </>
    );
  } else {
    body = null;
  }
  const flash = enter === "flash" ? clamp01(1 - t / 0.18) : 0;
  return (
    <AbsoluteFill style={{ background: shot.bg ?? field ?? "transparent", overflow: "hidden" }}>
      <AbsoluteFill style={enterStyle(enter, t)}>{body}</AbsoluteFill>
      {shot.label && <Label text={shot.label} look={look} top={h < 1400} />}
      {flash > 0 && <AbsoluteFill style={{ background: "#fff", opacity: flash }} />}
    </AbsoluteFill>
  );
};
