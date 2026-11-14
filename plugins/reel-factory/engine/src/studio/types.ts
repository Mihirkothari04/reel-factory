import type { SfxCue, Word } from "../types";

/** Presenter framings. The presenter performs continuously; the edit only changes how much of the frame he gets. */
export type LayoutName = "off" | "full" | "close" | "split" | "card" | "corner" | "corner-left";

export type LookName = "studio" | "intel" | "cutout";

export type Mark = { rects: { x: number; y: number; w: number; h: number }[]; at: number; style?: "marker" | "box" | "underline" | "strike"; color?: string };
export type CamKey = { t: number; x: number; y: number; z: number }; // t = s from shot start; x,y = focus 0..1 of the media; z = zoom over fit

export type Shot = {
  id: string;
  from: number; // s (absolute)
  to: number;
  kind: "scene" | "image" | "video" | "color";
  enter?: "cut" | "blur" | "zoom" | "whip" | "slide" | "flash";
  // scene: any legacy scene component rendered inside the content box
  type?: string;
  props?: Record<string, any>;
  // image / video
  src?: string;
  aspect?: number; // w/h of the media
  fit?: "cover" | "width" | "contain" | "blurfill";
  cam?: CamKey[];
  marks?: Mark[];
  trim?: number; // video: start offset (s)
  bg?: string; // color shot / letterbox colour
  label?: string; // small source chip, e.g. "WIRED · Nov 12"
};

export type Gfx = {
  id: string;
  from: number;
  to: number;
  kind: "sticker" | "label" | "slam" | "scene" | "counter";
  src?: string; // sticker image (cutout png)
  text?: string;
  sub?: string;
  x?: number; y?: number; w?: number; h?: number; // frame px (1080x1920)
  rot?: number;
  color?: string;
  type?: string; // scene component for kind "scene"
  props?: Record<string, any>;
  value?: number; prefix?: string; suffix?: string; decimals?: number; fromValue?: number; // counter
};

export type LayoutEvent = { t: number; layout: LayoutName };
export type PresenterWindow = { start: number; end: number; src: string };

export type StudioProps = {
  meta: { title: string; look: LookName; accent?: string; captionStyle?: "word" | "bold" | "box" | "none"; handle?: string; grain?: number };
  durationSec: number;
  fps: number;
  audio: { vo?: string; music?: string; musicVolume?: number; duckTo?: number; sfx: SfxCue[] };
  words: Word[];
  emphasis: string[];
  layouts: LayoutEvent[];
  shots: Shot[];
  gfx: Gfx[];
  presenter?: { windows: PresenterWindow[]; set?: string };
};
