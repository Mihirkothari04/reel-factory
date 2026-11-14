import { resolveTheme, type Theme } from "../theme";
import type { LookName } from "./types";

/**
 * Format bibles: one consistent show identity per look (palette, type, caption style, content backdrop, grade).
 * Original combinations — informed by the reference creators, copying none of them.
 */
export type Look = {
  theme: Theme; // used by the reusable scene components
  backdrop: string; // content area background
  fields?: string[]; // per-shot colour fields (cutout look)
  caption: "word" | "bold" | "box";
  capColor: string;
  capAccent: string;
  marker: string; // highlighter colour on documents
  grain: number;
  vignette: number;
  labelBg: string;
  labelInk: string;
};

export const lookFor = (name: LookName, accent?: string): Look => {
  if (name === "intel") {
    const t = resolveTheme("terminal", accent ?? "#B8F34A");
    return {
      theme: { ...t, bg: "#0B0D0C", surface: "#151917", ink: "#F2F5EF", muted: "#9AA59D" },
      backdrop: "radial-gradient(120% 80% at 50% 30%, #18211A 0%, #0B0D0C 62%)",
      caption: "bold", capColor: "#F4F6F1", capAccent: accent ?? "#B8F34A", marker: "#FFD84D",
      grain: 0.07, vignette: 0.45, labelBg: "#1C221E", labelInk: "#B8F34A",
    };
  }
  if (name === "cutout") {
    const t = resolveTheme("swiss", accent ?? "#111111");
    return {
      theme: { ...t, accent: accent ?? "#111111", accentInk: "#FFFFFF" },
      backdrop: "#FFC93C",
      fields: ["#FFC93C", "#FF5A36", "#2E5BFF", "#E83E8C", "#6C3BFF", "#C6F432", "#0F766E", "#141414"],
      caption: "bold", capColor: "#FFFFFF", capAccent: "#FFE14D", marker: "#FFE14D",
      grain: 0.04, vignette: 0.2, labelBg: "#111111", labelInk: "#FFFFFF",
    };
  }
  const t = resolveTheme("swiss", accent ?? "#1F5BD6");
  return {
    theme: { ...t, bg: "#F1F3F6", surface: "#FFFFFF" },
    backdrop: "linear-gradient(180deg, #F4F6F9 0%, #E9EDF2 100%)",
    caption: "word", capColor: "#FFFFFF", capAccent: "#FFE14D", marker: "#FFE14D",
    grain: 0.035, vignette: 0.25, labelBg: "#111317", labelInk: "#FFFFFF",
  };
};
