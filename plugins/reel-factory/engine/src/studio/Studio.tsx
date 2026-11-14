import React, { useMemo } from "react";
import { AbsoluteFill, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { OUT } from "../anim";
import { chunkWords } from "../overlays";
import { Carousel, Headline, Sheet, Source, Walkthrough } from "../scenes/modes";
import { Bars, Flow, Grid, Hub, Item, Versus } from "../scenes/diagram";
import { List, Punch, Quote, Stat, Title } from "../scenes/text";
import { Chat, Code, Cta, ImageScene, Repo, src, Terminal, VideoScene } from "../scenes/ui";
import { ThemeCtx } from "../theme";
import type { Word } from "../types";
import { GfxView } from "./gfx";
import { geoAt } from "./layout";
import { lookFor, type Look } from "./looks";
import { ShotView } from "./shots";
import type { StudioProps } from "./types";

const REGISTRY: Record<string, React.FC<{ p: any; dur: number }>> = {
  title: Title, punch: Punch, stat: Stat, list: List, quote: Quote,
  repo: Repo, terminal: Terminal, code: Code, chat: Chat, image: ImageScene, video: VideoScene, cta: Cta,
  item: Item, bars: Bars, flow: Flow, hub: Hub, versus: Versus, grid: Grid,
  walkthrough: Walkthrough, headline: Headline, carousel: Carousel, sheet: Sheet, source: Source,
};

const clean = (w: string) => w.toLowerCase().replace(/[^a-z0-9$%+.#-]/g, "");

/** Captions over moving pictures: white type with a soft shadow, sized for a phone, synced per word. */
const StudioCaptions: React.FC<{ words: Word[]; emphasis: string[]; style: string; y: number; look: Look }> = ({ words, emphasis, style, y, look }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  const chunks = useMemo(() => chunkWords(words, style === "word" ? 1 : 3, style === "word" ? 30 : 20), [words, style]);
  const em = useMemo(() => new Set(emphasis.map(clean)), [emphasis]);
  if (style === "none") return null;
  const c = chunks.find((x) => now >= x.s - 0.04 && now < x.e);
  if (!c) return null;
  const pop = OUT(Math.min(1, (now - c.s + 0.04) / 0.12));
  const th = look.theme;
  const shadow = "0 4px 22px rgba(0,0,0,.6), 0 2px 6px rgba(0,0,0,.55)";
  // a dark outline keeps white captions legible on white documents and bright footage alike
  const stroke: React.CSSProperties = { WebkitTextStroke: "7px rgba(10,12,16,.82)", paintOrder: "stroke fill" };
  const wrap: React.CSSProperties = { position: "absolute", left: 60, right: 60, top: y, translate: "0 -50%", display: "flex", justifyContent: "center", textAlign: "center", pointerEvents: "none" };
  if (style === "word") {
    const w = c.words[0];
    const isEm = em.has(clean(w.w));
    return (
      <div style={wrap}>
        <div style={{ fontFamily: th.serif, fontStyle: "italic", fontSize: isEm ? 112 : 96, lineHeight: 1, color: isEm ? look.capAccent : look.capColor, textShadow: shadow, ...stroke, scale: interpolate(pop, [0, 1], [0.86, 1]), letterSpacing: "-0.01em" }}>
          {w.w.replace(/[,;:]$/, "")}
        </div>
      </div>
    );
  }
  if (style === "box") {
    return (
      <div style={wrap}>
        <div style={{ fontFamily: th.sans, fontWeight: 800, fontSize: 60, lineHeight: 1.2, scale: interpolate(pop, [0, 1], [0.94, 1]) }}>
          {c.words.map((w, i) => (
            <span key={i} style={{ background: "#0E0F12", color: em.has(clean(w.w)) ? look.capAccent : "#FFFFFF", padding: "2px 12px", boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone", opacity: now >= w.s - 0.02 ? 1 : 0.55 }}>{w.w} </span>
          ))}
        </div>
      </div>
    );
  }
  return (
    <div style={wrap}>
      <div style={{ fontFamily: th.sans, fontWeight: 800, fontSize: 66, lineHeight: 1.15, letterSpacing: "-0.015em", textShadow: shadow, ...stroke, scale: interpolate(pop, [0, 1], [0.92, 1]) }}>
        {c.words.map((w, i) => (
          <span key={i} style={{ color: em.has(clean(w.w)) ? look.capAccent : look.capColor, opacity: now >= w.s - 0.02 ? 1 : 0.6 }}>{w.w} </span>
        ))}
      </div>
    </div>
  );
};

/** procedural film grain + vignette: ties generated, captured and rendered layers into one picture */
const Grade: React.FC<{ grain: number; vignette: number }> = ({ grain, vignette }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {vignette > 0 && <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 70% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,${vignette}) 100%)` }} />}
      {grain > 0 && (
        <svg width="1080" height="1920" style={{ position: "absolute", inset: 0, opacity: grain, mixBlendMode: "overlay" }}>
          <filter id="g">
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={frame % 12} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="1080" height="1920" filter="url(#g)" />
        </svg>
      )}
    </AbsoluteFill>
  );
};

export const Studio: React.FC<StudioProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const look = lookFor(props.meta.look, props.meta.accent);
  const { g } = geoAt(props.layouts, t);
  const windows = props.presenter?.windows ?? [];

  const musicCurve = useMemo(() => {
    const n = Math.ceil(props.durationSec * fps) + 1;
    const hi = props.audio.musicVolume ?? 0.3, lo = props.audio.duckTo ?? 0.1;
    const raw = new Float32Array(n).fill(hi);
    props.words.forEach((w) => {
      for (let f = Math.floor((w.s - 0.15) * fps); f <= Math.ceil((w.e + 0.25) * fps); f++) if (f >= 0 && f < n) raw[f] = lo;
    });
    const sm = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      let a = 0, c = 0;
      for (let j = i - 5; j <= i + 5; j++) if (j >= 0 && j < n) { a += raw[j]; c++; }
      sm[i] = a / c;
    }
    const fo = Math.round(1.2 * fps);
    for (let i = 0; i < fo; i++) sm[n - 1 - i] *= i / fo;
    return sm;
  }, [props.words, props.durationSec, fps, props.audio.musicVolume, props.audio.duckTo]);

  const fieldFor = (i: number) => (look.fields ? look.fields[i % look.fields.length] : undefined);
  const presOn = g.pa > 0.01;

  return (
    <ThemeCtx.Provider value={look.theme}>
      <AbsoluteFill style={{ background: look.fields ? fieldFor(0) : look.backdrop }}>
        {/* content track: shots inside the layout's content box */}
        <div style={{ position: "absolute", left: g.bx, top: g.by, width: g.bw, height: g.bh, overflow: "hidden", borderRadius: g.br, opacity: g.ba, background: look.fields ? fieldFor(0) : look.backdrop, boxShadow: g.card > 0.5 ? "0 30px 70px rgba(0,0,0,.45)" : undefined }}>
          {props.shots.map((s, i) => (
            <Sequence key={s.id} from={Math.round(s.from * fps)} durationInFrames={Math.max(1, Math.round((s.to - s.from) * fps))} name={`shot:${s.id}`}>
              <ShotView shot={s} w={g.bw} h={g.bh} look={look} registry={REGISTRY} field={fieldFor(i)} />
            </Sequence>
          ))}
        </div>

        {/* presenter track: studio set + alpha performance, clipped to the layout band */}
        {presOn && (
          <div style={{ position: "absolute", left: 0, top: g.clipTop, width: 1080, height: Math.max(0, g.clipBot - g.clipTop), overflow: "hidden", opacity: g.pa }}>
            {props.presenter?.set && g.set > 0.01 && (
              <Img src={src(props.presenter.set)} style={{ position: "absolute", left: 0, top: -g.clipTop, width: 1080, height: 1920, objectFit: "cover", opacity: g.set, scale: 1.04 + 0.01 * Math.sin(t / 3) }} />
            )}
            <div style={{ position: "absolute", left: g.px + 5 * Math.sin(t * 0.63), top: g.py - g.clipTop + 4 * Math.sin(t * 0.47 + 1.3), width: 1080, height: 1920, transform: `scale(${g.ps * (1 + 0.008 * Math.sin(t * 0.31))})`, transformOrigin: "0 0", filter: g.shadow > 0.5 ? "drop-shadow(0 20px 40px rgba(0,0,0,.45))" : undefined }}>
              {windows.map((w, i) => (
                <Sequence key={`pw${i}`} from={Math.round(w.start * fps)} durationInFrames={Math.max(1, Math.round((w.end - w.start) * fps))} name={`presenter:${i}`}>
                  <OffthreadVideo src={src(w.src)} transparent muted style={{ width: 1080, height: 1920 }} />
                </Sequence>
              ))}
            </div>
          </div>
        )}
        {/* card layout draws the content box over the presenter */}
        {g.card > 0.01 && (
          <div style={{ position: "absolute", left: g.bx, top: g.by, width: g.bw, height: g.bh, overflow: "hidden", borderRadius: g.br, opacity: g.card, background: "#fff", boxShadow: "0 30px 70px rgba(0,0,0,.45)" }}>
            {props.shots.map((s, i) => (
              <Sequence key={`c${s.id}`} from={Math.round(s.from * fps)} durationInFrames={Math.max(1, Math.round((s.to - s.from) * fps))} name={`card:${s.id}`}>
                <ShotView shot={s} w={g.bw} h={g.bh} look={look} registry={REGISTRY} field={fieldFor(i)} />
              </Sequence>
            ))}
          </div>
        )}

        {/* graphics track */}
        {props.gfx.map((x) => (
          <Sequence key={x.id} from={Math.round(x.from * fps)} durationInFrames={Math.max(1, Math.round((x.to - x.from) * fps))} name={`gfx:${x.id}`}>
            <GfxView g={x} look={look} registry={REGISTRY} />
          </Sequence>
        ))}

        <Grade grain={props.meta.grain ?? look.grain} vignette={look.vignette} />
        <StudioCaptions words={props.words} emphasis={props.emphasis} style={props.meta.captionStyle ?? look.caption} y={g.capY} look={look} />

        {props.audio.vo && <Audio src={staticFile(props.audio.vo)} />}
        {props.audio.music && <Audio src={staticFile(props.audio.music)} loop volume={(f) => musicCurve[Math.min(f, musicCurve.length - 1)] ?? 0} />}
        {props.audio.sfx.map((c, i) => (
          <Sequence key={`sfx${i}`} from={Math.max(0, Math.round(c.t * fps))} durationInFrames={Math.round(2 * fps)} layout="none">
            <Audio src={staticFile(`sfx/${c.name}.wav`)} volume={c.vol ?? 0.5} />
          </Sequence>
        ))}
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
