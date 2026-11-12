---
description: First-run onboarding and maintenance for reel-factory — probe this machine, install/repair the runtime, choose free vs premium services, set brand and preferences
argument-hint: "[set <key> <value> | probe | reset-onboarding]"
---

`RF` = `python "${CLAUDE_PLUGIN_ROOT}/scripts/rf.py"`

- `$ARGUMENTS` starts with `set` → `RF config $ARGUMENTS`, show the changed key, stop.
- `$ARGUMENTS` is `probe` → `RF probe`, summarise, stop.
- `$ARGUMENTS` is `reset-onboarding` → `RF config set onboarded false`, then continue below.

## 1. Probe
`RF probe`. Summarise in a short table: system (OS, GPU, RAM, disk), required tools (OK/missing), the per-stage plan (voice, music, images, whisper, render) and the asks.

## 2. Blockers first
For each blocker, show the install command the probe printed for this OS and offer to run it (system installs need the user's explicit yes; never use sudo without it). Re-probe after each install. Stop if a blocker can't be fixed and say what remains.

## 3. Runtime
If the runtime is missing or outdated: `RF setup` (5–10 min first time, ~1.5 GB). Then `RF doctor`.

## 4. Onboarding questions (only if `config.onboarded` is not true)
Ask with one `AskUserQuestion` call (up to 4 questions), each only if relevant:
1. **Services** (header "Services"), only if ElevenLabs isn't logged in: "Free only (edge-tts voice, CC music, no generated images)" · "Log in to ElevenLabs" (then run `elevenlabs auth login`; install the CLI first with `npm i -g @elevenlabs/cli` if missing) · "I have an API key" (tell them to set `ELEVENLABS_API_KEY` and re-run `/reel-setup`; never ask them to paste the key into chat).
2. **Brand** (header "Brand"): "Set handle and accent" (then ask for the handle in plain text and pick or accept a hex accent) · "No branding".
3. **Language** (header "Language"): English · Hindi/Hinglish · Spanish · Other. (ElevenLabs v3 and edge-tts both cover them; set `language` and a matching `voice.edge_voice`.)
4. **Mode question** (header "Modes"): "Ask me each time (Recommended)" · "Always AI Select".
Save each answer with `RF config set <key> <value>`, then `RF config set onboarded true`.

## 5. Show the result
Current config as a compact table with the keys that matter: `voice.provider`/`voice.voice_id` (list voices with `elevenlabs voices search --format json` if asked), `music.provider`, `images.max_per_reel`, `video_gen.enabled`, `avatar.enabled`/`avatar.image`, `brand.*`, `language`, `modes.ask`, `whisper.model`, `output_dir`, `browser_capture`. End with: "Run `/reel` for a trending topic or `/reel <topic>`."
