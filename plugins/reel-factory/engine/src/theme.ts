import { createContext, useContext } from "react";
import { loadFont as instrument } from "@remotion/google-fonts/InstrumentSerif";
import { loadFont as geist } from "@remotion/google-fonts/Geist";
import { loadFont as geistMono } from "@remotion/google-fonts/GeistMono";
import { loadFont as interTight } from "@remotion/google-fonts/InterTight";
import { loadFont as fraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as jetbrains } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as archivo } from "@remotion/google-fonts/Archivo";
import { loadFont as plexMono } from "@remotion/google-fonts/IBMPlexMono";
import { loadFont as barlowC } from "@remotion/google-fonts/BarlowCondensed";
import { loadFont as sourceSerif } from "@remotion/google-fonts/SourceSerif4";
import { loadFont as newsreader } from "@remotion/google-fonts/Newsreader";
import type { ThemeName } from "./types";

const latin = { subsets: ["latin" as const] };
const F = {
  instrument: instrument("italic", { weights: ["400"], ...latin }).fontFamily,
  geist: geist("normal", { weights: ["400", "500", "700", "800"], ...latin }).fontFamily,
  geistMono: geistMono("normal", { weights: ["400", "600"], ...latin }).fontFamily,
  interTight: interTight("normal", { weights: ["400", "500", "700", "800"], ...latin }).fontFamily,
  fraunces: fraunces("italic", { weights: ["400", "600"], ...latin }).fontFamily,
  jetbrains: jetbrains("normal", { weights: ["400", "700"], ...latin }).fontFamily,
  archivo: archivo("normal", { weights: ["400", "600", "800", "900"], ...latin }).fontFamily,
  plexMono: plexMono("normal", { weights: ["400", "600"], ...latin }).fontFamily,
  barlowC: barlowC("normal", { weights: ["600", "800"], ...latin }).fontFamily,
  sourceSerif: sourceSerif("italic", { weights: ["400", "600"], ...latin }).fontFamily,
  newsreader: newsreader("italic", { weights: ["400", "600"], ...latin }).fontFamily,
};

export type Theme = {
  name: ThemeName;
  dark: boolean;
  bg: string; // page
  surface: string; // cards / windows
  ink: string; // primary text
  muted: string; // secondary text (kept >= 4.5:1 on bg)
  line: string; // hairlines
  accent: string; // single brand accent
  accentInk: string; // text color on accent
  good: string;
  bad: string;
  display: string; // headline face
  displayWeight: number;
  displayCase: "none" | "uppercase";
  serif: string; // italic emphasis face
  sans: string;
  mono: string;
  radius: number;
};

// Each theme = one neutral + one accent, two-face pairing (sans + italic serif emphasis),
// mirroring the top creators' systems (see analysis/REEL_ANALYSIS.md §5).
export const THEMES: Record<ThemeName, Theme> = {
  paper: {
    name: "paper", dark: false, bg: "#F3EFE6", surface: "#FFFDF8", ink: "#1A1712", muted: "#5F584C", line: "#DDD5C4",
    accent: "#D4502A", accentInk: "#FFFFFF", good: "#2F7D5B", bad: "#C2362B",
    display: F.geist, displayWeight: 800, displayCase: "none", serif: F.instrument, sans: F.geist, mono: F.geistMono, radius: 14,
  },
  night: {
    name: "night", dark: true, bg: "#0E0E10", surface: "#18181C", ink: "#F1EFEA", muted: "#A8A49B", line: "#2B2B31",
    accent: "#F2A93B", accentInk: "#141414", good: "#5DBB8A", bad: "#E5604D",
    display: F.interTight, displayWeight: 800, displayCase: "none", serif: F.fraunces, sans: F.interTight, mono: F.jetbrains, radius: 12,
  },
  swiss: {
    name: "swiss", dark: false, bg: "#F6F5F1", surface: "#FFFFFF", ink: "#0F0F0F", muted: "#5E5E5A", line: "#E0DED7",
    accent: "#1F5BD6", accentInk: "#FFFFFF", good: "#1E8A4C", bad: "#D23C24",
    display: F.archivo, displayWeight: 900, displayCase: "none", serif: F.sourceSerif, sans: F.archivo, mono: F.plexMono, radius: 10,
  },
  signal: {
    name: "signal", dark: false, bg: "#E7E4DE", surface: "#FBFAF7", ink: "#1B1817", muted: "#5D5651", line: "#CFC9C0",
    accent: "#B0242D", accentInk: "#FFFFFF", good: "#2D6F4E", bad: "#B0242D",
    display: F.barlowC, displayWeight: 800, displayCase: "uppercase", serif: F.sourceSerif, sans: F.interTight, mono: F.jetbrains, radius: 8,
  },
  noir: {
    name: "noir", dark: true, bg: "#0D0C0B", surface: "#181614", ink: "#F3EDE3", muted: "#A79F93", line: "#2C2925",
    accent: "#FF5A1F", accentInk: "#140A05", good: "#7BC48F", bad: "#FF5A1F",
    display: F.barlowC, displayWeight: 800, displayCase: "uppercase", serif: F.instrument, sans: F.interTight, mono: F.geistMono, radius: 6,
  },
  frost: {
    name: "frost", dark: false, bg: "#EEF1F5", surface: "#FFFFFF", ink: "#0F1720", muted: "#526070", line: "#D5DCE5",
    accent: "#2453FF", accentInk: "#FFFFFF", good: "#12915A", bad: "#D62839",
    display: F.interTight, displayWeight: 800, displayCase: "none", serif: F.newsreader, sans: F.interTight, mono: F.geistMono, radius: 10,
  },
  ink: {
    name: "ink", dark: true, bg: "#0B0F14", surface: "#141B24", ink: "#EAF0F6", muted: "#8E9BAB", line: "#243040",
    accent: "#3DA5FF", accentInk: "#06121F", good: "#3DDC97", bad: "#FF5C6C",
    display: F.barlowC, displayWeight: 800, displayCase: "uppercase", serif: F.newsreader, sans: F.interTight, mono: F.jetbrains, radius: 8,
  },
  terminal: {
    name: "terminal", dark: true, bg: "#0A0F0C", surface: "#111915", ink: "#E4F1E8", muted: "#8FA597", line: "#20302A",
    accent: "#3DDC97", accentInk: "#06130D", good: "#3DDC97", bad: "#FF6B5B",
    display: F.interTight, displayWeight: 800, displayCase: "none", serif: F.newsreader, sans: F.interTight, mono: F.jetbrains, radius: 10,
  },
};

export const resolveTheme = (name: ThemeName, accent?: string): Theme => {
  const t = THEMES[name] ?? THEMES.paper;
  return accent ? { ...t, accent } : t;
};

export const ThemeCtx = createContext<Theme>(THEMES.paper);
export const useTheme = () => useContext(ThemeCtx);

// Stage = drawable area for scenes (full frame when faceless, top part when split with avatar).
export type Stage = { w: number; h: number; s: number; first?: boolean };
export const StageCtx = createContext<Stage>({ w: 1080, h: 1920, s: 1 });
export const useStage = () => useContext(StageCtx);
