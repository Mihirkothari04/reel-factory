import type { ReelProps, Scene, Word } from "./types";

// Engine self-test storyboard: every scene type once, synthetic word timing, no audio.
const text =
  "Someone just open sourced a free tool that attacks your app like a hacker. It already crossed forty five thousand stars on GitHub. Here is how it works.";
const words: Word[] = text.split(" ").map((w, i) => ({ w, s: 0.1 + i * 0.3, e: 0.1 + i * 0.3 + 0.26 }));

const S = (id: string, type: Scene["type"], start: number, end: number, props: any, extra: Partial<Scene> = {}): Scene => ({
  id, type, start, end, props, enter: "push", ...extra,
});

export const demoProps: ReelProps = {
  meta: { title: "engine demo", theme: "paper", captionStyle: "pill", layout: "faceless", handle: "@yourhandle", hookTitle: { text: "This free tool *hacks* your app", until: 2.6 } },
  durationSec: 52,
  fps: 30,
  audio: { sfx: [] },
  words,
  emphasis: ["hacker", "free", "stars"],
  scenes: [
    S("s1", "title", 0, 2.6, { lines: ["Someone just built", "a [free] AI *hacker*"] }),
    S("s2", "repo", 2.6, 6, { owner: "usestrix", name: "strix", description: "Open-source AI agents that *pentest* your app", stars: 45210, language: "Python", license: "Apache-2.0", topics: ["security", "agents", "pentest"] }),
    S("s3", "stat", 6, 8.5, { value: 45210, suffix: "★", label: "GitHub stars in *3 weeks*" }, { label: "01 / 05" }),
    S("s4", "terminal", 8.5, 12, { title: "~/my-app", lines: [{ t: "cmd", text: "strix --target ./my-app" }, { t: "dim", text: "spawning 6 agents…" }, { t: "err", text: "SQL injection in /api/login" }, { t: "ok", text: "proof-of-concept verified" }] }, { label: "02 / 05" }),
    S("s5", "list", 12, 16, { title: "What it *does*", items: ["Runs your app live", "Attacks every endpoint", "Proves each bug is real", "Suggests the fix"], check: true }),
    S("s6", "versus", 16, 19.5, { left: { title: "Scanners", points: ["List of maybes", "False positives"] }, right: { title: "Strix", points: ["Working exploit", "Fix attached"] } }),
    S("s7", "bars", 19.5, 22.5, { title: "Findings per run", unit: "", bars: [{ label: "Static scanner", value: 3 }, { label: "Strix agents", value: 11, highlight: true }] }),
    S("s8", "flow", 22.5, 26.5, { title: "How it *works*", nodes: ["Map the app", "Spawn hacker agents", "Attack + verify", "Report with fixes"] }),
    S("s9", "hub", 26.5, 29.5, { center: "Strix", spokes: ["Logins", "APIs", "Database", "Uploads", "Prompts"] }),
    S("s10", "quote", 29.5, 33, { author: "Security lead", handle: "@example", text: "It found an auth bypass our scanner missed for two years.", highlight: ["auth bypass"] }),
    S("s11", "item", 33, 36.5, { index: 3, total: 5, name: "Strix", desc: "AI agents that *pentest* your app before a real hacker does.", stars: 45210, tag: "free · open source" }),
    S("s12", "grid", 36.5, 39.5, { title: "Works with", items: [{ label: "Claude Code" }, { label: "Codex" }, { label: "Cursor" }, { label: "OpenCode" }, { label: "Gemini CLI" }, { label: "Ollama" }], highlight: [0] }),
    S("s13", "chat", 39.5, 43, { app: "claude", messages: [{ role: "user", text: "Run a security test on my app" }, { role: "ai", text: "Found 3 critical issues. Patches are ready." }] }),
    S("s14", "punch", 43, 45, { text: "Completely *free*", style: "big" }, { enter: "pop" }),
    S("s15", "punch", 45, 47, { text: "VULNERABLE", style: "stamp" }, { enter: "cut" }),
    S("s16", "cta", 47, 52, { kind: "comment", keyword: "CODE", line: "and I'll send you the repo" }, { enter: "pop" }),
  ],
};
