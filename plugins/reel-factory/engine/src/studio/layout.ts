import { Easing } from "remotion";
import type { LayoutEvent, LayoutName } from "./types";

/**
 * Frame geometry for each presenter framing (1080x1920).
 * pres*: transform of the full 1080x1920 presenter plate (alpha video): translate (px, py) then scale ps.
 * clip*: visible band of the presenter (frame y range). box*: where the B-roll content renders.
 * set: opacity of the studio set behind the presenter. capY: caption baseline. shadow: cutout drop shadow.
 */
export type Geo = {
  px: number; py: number; ps: number; pa: number;
  clipTop: number; clipBot: number;
  bx: number; by: number; bw: number; bh: number; br: number; ba: number;
  set: number; capY: number; shadow: number; card: number;
};

const base: Geo = { px: 0, py: 0, ps: 1, pa: 1, clipTop: 0, clipBot: 1920, bx: 0, by: 0, bw: 1080, bh: 1920, br: 0, ba: 1, set: 0, capY: 1480, shadow: 0, card: 0 };

// head top sits ~280 px below the plate's top edge; hands ~1250-1450
export const GEO: Record<LayoutName, Geo> = {
  off: { ...base, pa: 0 },
  full: { ...base, ba: 0, set: 1, capY: 1430 },
  close: { ...base, ps: 1.34, px: -184, py: -120, ba: 0, set: 1, capY: 1460 },
  split: { ...base, py: 1000 + 34 - 280, clipTop: 1000, bh: 1000, set: 1, capY: 925 },
  card: { ...base, bx: 56, by: 1040, bw: 968, bh: 560, br: 26, ba: 0, set: 1, capY: 1715, card: 1 },
  corner: { ...base, ps: 0.62, px: 1080 - 0.62 * 1080 + 70, py: 1920 - 1480 * 0.62, bh: 1300, capY: 1150, shadow: 1 },
  "corner-left": { ...base, ps: 0.62, px: -70, py: 1920 - 1480 * 0.62, bh: 1300, capY: 1150, shadow: 1 },
};

const EASE = Easing.bezier(0.2, 0.9, 0.25, 1);
const TRANS = 0.42; // s

const mix = (a: Geo, b: Geo, k: number): Geo => {
  const o = {} as Geo;
  (Object.keys(a) as (keyof Geo)[]).forEach((key) => (o[key] = a[key] + (b[key] - a[key]) * k));
  return o;
};

/** geometry at time t: the current layout, eased in from the previous one over TRANS seconds */
export const geoAt = (events: LayoutEvent[], t: number): { g: Geo; cur: LayoutName; prev: LayoutName; k: number } => {
  const ev = events.length ? events : [{ t: 0, layout: "off" as LayoutName }];
  let i = 0;
  for (let j = 0; j < ev.length; j++) if (ev[j].t <= t + 1e-6) i = j;
  const cur = ev[i].layout;
  const prev = i > 0 ? ev[i - 1].layout : cur;
  const k = i === 0 ? 1 : EASE(Math.max(0, Math.min(1, (t - ev[i].t) / TRANS)));
  let a = GEO[prev], b = GEO[cur];
  // entering from / leaving to "off": the presenter does not fly across the frame, he fades/wipes in place
  const PRES: (keyof Geo)[] = ["px", "py", "ps", "clipTop", "clipBot", "shadow"];
  if (a.pa === 0) a = { ...a, ...Object.fromEntries(PRES.map((f) => [f, b[f]])) };
  if (b.pa === 0) b = { ...b, ...Object.fromEntries(PRES.map((f) => [f, a[f]])) };
  return { g: mix(a, b, k), cur, prev, k };
};
