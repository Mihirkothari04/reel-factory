export type Word = { w: string; s: number; e: number };

export type ThemeName = "paper" | "night" | "swiss" | "signal" | "terminal" | "noir" | "frost" | "ink";
export type CaptionStyle = "pill" | "highlight" | "serif" | "caps" | "none";
export type Enter = "push" | "pop" | "blur" | "slide" | "cut";

export type SceneType =
  | "title" | "punch" | "stat" | "list" | "quote"
  | "repo" | "terminal" | "code" | "chat" | "image" | "video" | "cta"
  | "item" | "bars" | "flow" | "hub" | "versus" | "grid"
  | "walkthrough" | "headline" | "carousel" | "sheet" | "source";

export type Scene = {
  id: string;
  type: SceneType;
  start: number; // seconds
  end: number; // seconds
  enter?: Enter;
  label?: string; // HUD chapter label, e.g. "02 / 05"
  props: Record<string, any>;
};

export type SfxCue = { t: number; name: string; vol?: number };

export type ReelProps = {
  meta: {
    title: string;
    theme: ThemeName;
    accent?: string; // override theme accent
    captionStyle: CaptionStyle;
    layout: "faceless" | "split-avatar";
    handle?: string;
    hookTitle?: { text: string; until: number };
    mode?: string; // creation mode id (modes.json)
    banner?: { text: string; kicker?: string }; // persistent news lower-third (newsroom)
    slate?: { title: string }; // film-slate HUD (cinematic)
    progress?: { items: string[]; at: number[]; style?: "bar" | "chips" }; // persistent tracker; at = time each item is reached (s)
  };
  durationSec: number;
  fps: number;
  audio: {
    vo?: string;
    music?: string;
    musicVolume?: number; // 0..1 when no speech
    duckTo?: number; // 0..1 under speech
    sfx: SfxCue[];
  };
  words: Word[];
  emphasis: string[]; // lowercase words highlighted in captions
  scenes: Scene[];
  avatar?: { src: string };
};
