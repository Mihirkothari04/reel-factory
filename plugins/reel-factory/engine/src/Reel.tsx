import React, { useMemo } from "react";
import { AbsoluteFill, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio, Video } from "@remotion/media";
import { OUT } from "./anim";
import { Banner, Captions, Handle, HookTitle, HudLabel, Progress, Slate } from "./overlays";
import { Carousel, Headline, Sheet, Walkthrough } from "./scenes/modes";
import { Bars, Flow, Grid, Hub, Item, Versus } from "./scenes/diagram";
import { List, Punch, Quote, Stat, Title } from "./scenes/text";
import { Chat, Code, Cta, ImageScene, Repo, src, Terminal, VideoScene } from "./scenes/ui";
import { resolveTheme, Stage, StageCtx, ThemeCtx } from "./theme";
import type { Enter, ReelProps, Scene } from "./types";

const REGISTRY: Record<string, React.FC<{ p: any; dur: number }>> = {
  title: Title, punch: Punch, stat: Stat, list: List, quote: Quote,
  repo: Repo, terminal: Terminal, code: Code, chat: Chat, image: ImageScene, video: VideoScene, cta: Cta,
  item: Item, bars: Bars, flow: Flow, hub: Hub, versus: Versus, grid: Grid,
  walkthrough: Walkthrough, headline: Headline, carousel: Carousel, sheet: Sheet,
};

const fullBleed = (sc: Scene) => sc.type === "video" || (sc.type === "image" && sc.props.frame === "full");

/** Incoming-cut animation (first ~0.3s): reads as a transition while scene timing stays locked to the VO. */
const EnterWrap: React.FC<{ enter: Enter; children: React.ReactNode }> = ({ enter, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = OUT(Math.min(1, frame / (0.32 * fps)));
  const style: React.CSSProperties =
    enter === "push" ? { translate: `0 ${(1 - k) * 90}px`, opacity: Math.min(1, k * 1.5) }
    : enter === "slide" ? { translate: `${(1 - k) * 160}px 0`, opacity: Math.min(1, k * 1.5) }
    : enter === "pop" ? { scale: interpolate(k, [0, 1], [0.9, 1]), opacity: Math.min(1, k * 2) }
    : enter === "blur" ? { filter: `blur(${(1 - k) * 18}px)`, opacity: k }
    : {};
  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};

const HandleAfter: React.FC<{ until: number; text: string }> = ({ until, text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return frame / fps < until ? null : <Handle text={text} />;
};

export const Reel: React.FC<ReelProps> = (props) => {
  const { fps, width, height } = useVideoConfig();
  const theme = resolveTheme(props.meta.theme, props.meta.accent);
  const split = props.meta.layout === "split-avatar" && !!props.avatar;
  const hook = props.meta.hookTitle;

  // music ducking curve: per-frame target volume from word timing, smoothed
  const musicCurve = useMemo(() => {
    const n = Math.ceil(props.durationSec * fps) + 1;
    const hi = props.audio.musicVolume ?? 0.32;
    const lo = props.audio.duckTo ?? 0.14;
    const raw = new Float32Array(n).fill(hi);
    props.words.forEach((w) => {
      for (let f = Math.floor((w.s - 0.15) * fps); f <= Math.ceil((w.e + 0.25) * fps); f++) if (f >= 0 && f < n) raw[f] = lo;
    });
    const sm = new Float32Array(n);
    const R = 5;
    for (let i = 0; i < n; i++) {
      let a = 0, c = 0;
      for (let j = i - R; j <= i + R; j++) if (j >= 0 && j < n) { a += raw[j]; c++; }
      sm[i] = a / c;
    }
    const fadeOut = Math.round(1.2 * fps);
    for (let i = 0; i < fadeOut; i++) sm[n - 1 - i] *= i / fadeOut;
    return sm;
  }, [props.words, props.durationSec, fps, props.audio.musicVolume, props.audio.duckTo]);

  const stageFor = (sc: Scene): { box: React.CSSProperties; stage: Stage } => {
    if (fullBleed(sc)) return { box: { left: 0, top: 0, width, height: split ? 1037 : height }, stage: { w: width, h: split ? 1037 : height, s: 1 } };
    if (split) return { box: { left: 0, top: 80, width, height: 950 }, stage: { w: width, h: 950, s: 0.8 } };
    const hooked = hook && sc.start < hook.until;
    const top = hooked ? 300 : 200;
    const h = (props.meta.banner ? 1170 : 1290) - top; // banner sits 1190-1290
    return { box: { left: 0, top, width, height: h }, stage: { w: width, h, s: h < 1050 ? 1.02 : 1.15 } };
  };

  return (
    <ThemeCtx.Provider value={theme}>
      <AbsoluteFill style={{ background: theme.bg }}>
        {props.scenes.map((sc) => {
          const Comp = REGISTRY[sc.type];
          if (!Comp) return null;
          const from = Math.round(sc.start * fps);
          const dur = Math.max(1, Math.round((sc.end - sc.start) * fps));
          const { box, stage } = stageFor(sc);
          return (
            <Sequence key={sc.id} from={from} durationInFrames={dur} name={`${sc.id}:${sc.type}`}>
              <StageCtx.Provider value={{ ...stage, first: sc.start < 0.01 }}>
                <div style={{ position: "absolute", ...box, overflow: "hidden" }}>
                  <EnterWrap enter={sc.start < 0.01 ? "cut" : (sc.enter ?? "push")}>
                    <Comp p={sc.props} dur={sc.end - sc.start} />
                  </EnterWrap>
                </div>
              </StageCtx.Provider>
              {sc.label && !fullBleed(sc) && !(hook && sc.start < hook.until) && !split && !props.meta.progress && !props.meta.slate && <HudLabel text={sc.label} />}
            </Sequence>
          );
        })}

        {split && props.avatar && (
          <div style={{ position: "absolute", left: 0, top: 1037, width, height: height - 1037, overflow: "hidden" }}>
            <Video src={src(props.avatar.src)} muted style={{ width, height: height - 1037, objectFit: "cover" }} />
          </div>
        )}

        {props.meta.banner && !split && <Banner text={props.meta.banner.text} kicker={props.meta.banner.kicker} y={1190} />}
        {props.meta.slate && <Slate title={props.meta.slate.title} sceneStarts={props.scenes.map((s) => s.start)} />}
        {props.meta.progress && !split && <Progress items={props.meta.progress.items} at={props.meta.progress.at} style={props.meta.progress.style} />}
        {hook && <HookTitle text={hook.text} until={hook.until} />}
        {props.meta.handle && !split && !props.meta.slate && !props.meta.progress && <HandleAfter until={hook?.until ?? 0} text={props.meta.handle} />}
        <Captions words={props.words} emphasis={props.emphasis} style={props.meta.captionStyle} y={split ? 1010 : 1400} />

        {props.audio.vo && <Audio src={staticFile(props.audio.vo)} />}
        {props.audio.music && (
          <Audio src={staticFile(props.audio.music)} loop volume={(f) => musicCurve[Math.min(f, musicCurve.length - 1)] ?? 0} />
        )}
        {props.audio.sfx.map((c, i) => (
          <Sequence key={`sfx${i}`} from={Math.max(0, Math.round(c.t * fps))} durationInFrames={Math.round(2 * fps)} layout="none">
            <Audio src={staticFile(`sfx/${c.name}.wav`)} volume={c.vol ?? 0.5} />
          </Sequence>
        ))}
      </AbsoluteFill>
    </ThemeCtx.Provider>
  );
};
