import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const OUT = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0→1 over [startSec, startSec+durSec] relative to the current Sequence */
export const useProgress = (startSec: number, durSec: number, easing = OUT) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return interpolate(frame, [startSec * fps, (startSec + durSec) * fps], [0, 1], { ...clamp, easing });
};

/** spring 0→1 starting at delaySec */
export const useSpring = (delaySec = 0, damping = 14, mass = 0.6) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delaySec * fps, fps, config: { damping, mass } });
};

/** seconds elapsed in current Sequence */
export const useT = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return frame / fps;
};

export const lerp = (p: number, a: number, b: number) => a + (b - a) * p;

/** evenly staggered reveal times for n items inside a scene of length dur (seconds) */
export const stagger = (n: number, dur: number, lead = 0.25, tail = 0.6) => {
  const span = Math.max(0.1, dur - lead - tail);
  return Array.from({ length: n }, (_, i) => lead + (n <= 1 ? 0 : (span * i) / (n - 1)) * 0.92);
};

export const fmtNum = (v: number, decimals = 0) =>
  v.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
