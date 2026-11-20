# Aura ✦ AI Creative Video Studio — Comprehensive Project Specification

> **Document Version:** 3.0.0 (Aesthetic Studio Edition)  
> **Last Updated:** November 2026  
> **Repository:** `Davanahs/Vedio_Editing`  
> **Target Platform:** Web (Desktop & Mobile Studio), CLI (Headless Automation), Docker  

---

## Table of Contents

1. [Executive Summary & Primary Objective](#1-executive-summary--primary-objective)
2. [Complete Technology Stack](#2-complete-technology-stack)
3. [Design System & CSS Architecture](#3-design-system--css-architecture)
4. [Visual Elements & UI Component Breakdown](#4-visual-elements--ui-component-breakdown)
5. [Master Style Sheet Specifications (Empirical Viral Standard)](#5-master-style-sheet-specifications)
6. [AI Pipeline & Director Architecture](#6-ai-pipeline--director-architecture)
7. [FFmpeg Multi-Layer Rendering & Audio Mastering Engine](#7-ffmpeg-multi-layer-rendering--audio-mastering-engine)
8. [REST API Reference & Data Models](#8-rest-api-reference--data-models)
9. [Web Audio Architecture & Playback Security](#9-web-audio-architecture--playback-security)
10. [File Structure & Module Responsibilities](#10-file-structure--module-responsibilities)

---

## 1. Executive Summary & Primary Objective

**Aura AI Creative Studio** is a prompt-based, autonomous short-form creative video editing suite. It transforms raw spoken video footage (horizontal landscape `16:9`, vertical mobile `9:16`, or square `1:1`) and additional uploaded user resources (photographs, audio tracks, brand graphics, and logos) into Pinterest-inspired scrapbook compositions, floating music player cards, and glassmorphic video reels in under 30 seconds.

### Core Benchmarks & Standards
- **Speed Objective:** Ingest, transcribe, direct, and render a 48-second raw video in **under 30 seconds** on standard modern hardware.
- **Auditory Objective:** Master speech audio to the short-form streaming broadcast standard of **`-14.0 LUFS`** with True Peak limited to **`-1.0 dBTP`**, integrating synchronized sound effects (SFX) on visual and semantic transients.
- **Visual Retention Objective:** Apply the empirical **2-Second Rule** (never leave a talking-head shot static for longer than 2.0s) by introducing camera angle punch-ins, top hook banners, floating social question cards, spoken keyword badges, and high-contrast two-tone kinetic typography.
- **Canvas Flexibility:** Native multi-aspect ratio rendering support for `9:16` (Vertical TikTok/Reels/Shorts), `16:9` (YouTube/Landscape), and `1:1` (Square Feed).

---

## 2. Complete Technology Stack

```
+─────────────────────────────────────────────────────────────────────────────+
|                             USER INTERFACE                                  |
|   ClipForge Studio Web UI (HTML5, Modern CSS3, Web Audio API, Vanilla ES6+) |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │ HTTP / REST & WebSockets
+──────────────────────────────────────▼──────────────────────────────────────+
|                           BACKEND API SERVER                                |
|   FastAPI (Python 3.12), Uvicorn ASGI, Pydantic V2 Models, AsyncIO Tasks   |
+──────────────────┬───────────────────┬───────────────────┬──────────────────+
                   │                   │                   │
+──────────────────▼─────+ +───────────▼────────+ +────────▼──────────────────+
|  ANALYSIS & INGESTION  | |  AI DIRECTOR CHAIN | |    HIGH-SPEED RENDERER    |
|  - FFprobe Metadata    | |  - Groq Whisper Tx | |  - FFmpeg (libx264/AAC)   |
|  - 16kHz WAV Extractor | |  - OpenRouter LLM  | |  - ASS Substation Alpha   |
|  - Pause & Scene Detect| |  - Google Gemini   | |  - Audio Loudnorm Filter  |
|  - MediaPipe / OpenCV  | |  - Dynamic Director| |  - Multi-Input amix Graph |
+────────────────────────+ +────────────────────+ +───────────────────────────+
```

### 1. Backend Runtime & Frameworks
- **Python 3.12:** Primary language environment leveraging typed asynchronous coroutines (`asyncio`).
- **FastAPI (>= 0.110.0):** Asynchronous ASGI web framework serving REST endpoints for uploads, chat editing, asset resolution, and video rendering.
- **Uvicorn (>= 0.27.0):** Lightning-fast ASGI web server hosting the FastAPI application.
- **Pydantic V2 (>= 2.5.0):** Strict schema definition and validation for Edit Decision Lists (EDLs), graphic triggers, and request payloads.
- **python-multipart (>= 0.0.9):** Streaming multipart/form-data handler for chunked raw video uploads.

### 2. AI & Cloud Intelligence
- **Groq Cloud API (`whisper-large-v3-turbo`):** Primary transcription engine delivering full word-level timestamps in **~4.8 seconds** for a 48s audio file.
- **OpenRouter API (`nvidia/nemotron-3.5-lightning`, `google/gemma-4-31b-it`, `meta-llama`):** Secondary LLM reasoning layer parsing video transcripts and generating dynamic visual cue timings.
- **Google Generative AI (`gemini-2.0-flash`, `gemini-1.5-flash`):** Alternative cloud director reasoning engine.
- **Local Dynamic Semantic Director:** Zero-latency, zero-cost, deterministic fallback director utilizing semantic regex burst parsing to ensure 100% offline availability.

### 3. Audio & Video Processing
- **FFmpeg (>= 6.0):** Native multimedia workhorse compiling unified multi-input filtergraphs.
  - Video Codec: `libx264` (`-preset faster`, `-crf 18`, `-pix_fmt yuv420p`).
  - Audio Codec: `aac` (`-b:a 192k`, `-ar 48000`).
  - Audio Normalization: `loudnorm=I=-14:TP=-1.0:LRA=7`.
  - Audio Mixing: `amix=inputs=N:dropout_transition=2:normalize=0`.
- **Advanced SubStation Alpha (`.ass`):** High-precision vector typography and overlay rendering directly compiled into video streams via FFmpeg's `subtitles` filter.
- **OpenCV (`opencv-python-headless >= 4.9.0`):** Frame-level dimension analysis, edge detection, and facial feature coordinates.
- **faster-whisper (>= 1.0.0):** Local on-device fallback Whisper engine running quantized CTranslate2 models.

### 4. Frontend & Browser Layer
- **Vanilla ES6+ JavaScript:** Zero external JavaScript dependencies (no heavy React/Vue runtime overhead) ensuring instant load times and deterministic execution.
- **HTML5 `<video>` & Web Audio API:** Low-latency playback, interactive multi-track playhead synchronization, and real-time SFX auditioning.
- **Modern CSS3:** CSS Custom Properties (Variables), Flexbox, CSS Grid, Glassmorphism (`backdrop-filter`), and hardware-accelerated transforms (`transform: scale(...) translate3d(...)`).

---

## 3. Design System & CSS Architecture

The interface follows the **ClipForge AI Studio** target design reference: a dark-themed, studio-grade digital audio/video workstation (DAW/NLE) aesthetic with high-contrast accenting.

### 1. Global CSS Design Tokens

```css
:root {
  /* Application Surface Colors */
  --bg-app: #0B0D14;            /* Canvas background (deep obsidian) */
  --bg-panel: #111420;          /* Sidebar & header background */
  --bg-card: #171B2B;           /* Primary interactive card background */
  --bg-card-hover: #1E2338;     /* Hover state card background */

  /* Borders & Dividers */
  --border-subtle: #1F2539;     /* Standard panel divider */
  --border-active: #7C3AED;     /* Focus / active border */

  /* Primary Brand Palettes */
  --primary-purple: #7C3AED;        /* Primary CTA gradient base */
  --primary-purple-hover: #6D28D9;  /* CTA hover state */
  --primary-purple-glow: rgba(124, 58, 237, 0.4);

  /* Functional & Accent Tokens */
  --accent-yellow: #FFE600;     /* Electric neon yellow (keywords, hook banner) */
  --accent-yellow-hover: #EAB308;
  --accent-cyan: #06B6D4;       /* Secondary badges */
  --accent-pink: #EC4899;       /* SFX badges */
  --accent-emerald: #10B981;    /* Online status, success states */

  /* Text & Typography Hierarchy */
  --text-main: #F8FAFC;         /* High-contrast primary text */
  --text-muted: #94A3B8;        /* Secondary labels & timestamps */
  --text-dim: #64748B;          /* Muted metadata */
}
```

### 2. Typography Stack
1. **Power Headlines & Kinetic Bursts:** `'Bebas Neue', 'Impact', 'Arial Black', sans-serif`
   - Weight: `900`
   - Letter-spacing: `0.8px` to `1.2px`
   - Line-height: `0.95` to `1.0`
   - Role: Spoken punchlines, hook pills, and kinetic title cards.
2. **Body, Subtitles & Lead-in Text:** `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`
   - Weight: `500` (normal), `700` (bold), `800` (extrabold)
   - Tracking: `tight`
   - Role: UI controls, script descriptions, dual-size subtitle lead words.
3. **Monospace & Timecodes:** `'JetBrains Mono', 'SF Mono', monospace`
   - Role: Millisecond timecode display (`00:02.8 / 00:46.5`), ruler markers (`0s`, `5s`, `10s`).

### 3. Keyframe Animations

```css
/* Spring-physics overshoot for popping cards and comment bubbles */
@keyframes springIn {
  0% { transform: scale(0.6) translateY(20px); opacity: 0; }
  100% { transform: scale(1) translateY(0); opacity: 1; }
}

/* Bouncy hook reveal */
@keyframes popInBounce {
  0% { transform: translateX(-50%) scale(0.7); opacity: 0; }
  100% { transform: translateX(-50%) scale(1); opacity: 1; }
}

/* Subtle floating badge hover effect */
@keyframes floatBadge {
  0% { transform: translateY(0px) scale(1); }
  100% { transform: translateY(-6px) scale(1.05); }
}

/* Dynamic mini-waveform pulsing bars */
@keyframes pulseWave {
  0% { transform: scaleY(0.4); opacity: 0.6; }
  100% { transform: scaleY(1.1); opacity: 1; }
}
```

---

## 4. Visual Elements & UI Component Breakdown

The workspace layout is partitioned into five distinct regions matching `reference-ui.png`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOP HEADER BAR                                 │
├────┬──────────────────────┬──────────────────────────┬──────────────────────┤
│    │  LEFT WORKSPACE      │   CENTER STAGE           │  RIGHT SETTINGS      │
│ N  │  - Script & Edits    │   - Video Canvas         │  - Theme Presets     │
│ A  │  - Active Video Card │   - Live Overlays        │  - Feature Toggles   │
│ V  │  - AI Chat Drawer    │   - Subject Glow Outline │  - Glow Color Swatch │
│    │  - AI Suggestions    │   - Punch-in Zooms       │  - SFX Soundboard    │
│ R  │  - Generate Action   │   - Transport Controls   │                      │
│ A  │                      │   - Aspect Selector      │                      │
│ I  │                      │                          │                      │
│ L  │                      │                          │                      │
├────┴──────────────────────┴──────────────────────────┴──────────────────────┤
│                       BOTTOM MULTI-TRACK TIMELINE                           │
│  [Time Ruler: 0s...45s] [Playhead] [Captions] [Graphics] [SFX] [Music]      │
│  [Actions: ▶ Preview | 🚀 Export Reel | ⬇ Download MP4]                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Top Header Bar (`<header>`)
- **Brand Logo:** Yellow rounded play button icon + bold white **`ClipForge`** title.
- **AI Studio Pill:** Lavender badge (`✦ AI Video Studio`) indicating engine readiness.
- **Center Prompt Search Bar:** Expansive `580px` prompt field (`#globalPromptInput`) with purple star icon (`✦`) and enter-key trigger. Enables typing high-level styling instructions directly from anywhere.
- **Actions:**
  - `Project ⌵` dropdown button: Opens upload modal or switches active project.
  - `🔊 Test Audio` button: Instantly plays a confirmation sound effect (`cash_register.wav`) to verify speaker output.
  - User Avatar (`D`): Styled gradient circle (`linear-gradient(135deg, #7C3AED, #A855F7)`).

### 2. Left Icon Rail (`<nav class="nav-rail">`)
- Vertical icon strip (`width: 68px`) with high-contrast SVG icons:
  - **Home:** Active state highlighted with purple glow (`rgba(124, 58, 237, 0.25)`).
  - **Templates:** Navigates directly to theme preset selection.
  - **SFX:** Directly switches right sidebar to the SFX soundboard.
  - **History:** Opens project drawer.
- Footer Tagline: *"⚡ Fast. Smart. Creative. Powered by AI"*.

### 3. Left Workspace Panel (`<aside class="left-panel">`)
- **Panel Tabs:** Toggle between `✏️ Script & Edits` and `🎨 Style Guide`.
- **Input Video Card:** Displays active filename, duration, resolution (`46.5s • 848 × 478`), online status dot, and `⇄ Change` button.
- **AI Director Chat Drawer:** Spacious textarea (`#leftPromptBox`) accompanied by quick-prompt chips:
  - `🎮 GTA / Gaming`: Inserts game controller popup and level-up sound.
  - `💰 Earn Money`: Inserts cash sticker and cash-register sound.
  - `✨ White Outline`: Activates clean white subject outline glow.
  - `🔥 Viral Style`: Configures viral TikTok kinetic captioning.
- **AI Editor Suggestions:** Transcript-derived recommendations with iOS-style toggle switches:
  1. *Add kinetic title:* Spoken headline at `0.8s - 2.8s`.
  2. *Show platform logo:* YouTube/OpenAI graphic popup at `5.4s - 7.5s`.
  3. *Add reaction sticker:* Cash/gaming badge at `12.0s - 14.5s`.
- **Generate Reel Button:** High-visibility gradient CTA (`linear-gradient(135deg, #7C3AED, #9333EA)`) with drop shadow.

### 4. Center Player Stage (`<main class="center-stage">`)
- **Video Canvas Wrapper (`#videoCanvasWrapper`):**
  - Dimensions dynamically adjust via CSS classes:
    - `.canvas-9-16`: `290px × 515px` (Reels/Shorts/TikTok).
    - `.canvas-16-9`: `680px × 382px` (Landscape/YouTube).
    - `.canvas-1-1`: `440px × 440px` (Square).
  - **Subject Outline Glow:** Hardware-accelerated CSS filter applied to `<video id="mainVideo">`:
    - `.glow-yellow`: `drop-shadow(0 0 10px rgba(255, 230, 0, 0.8)) drop-shadow(0 0 20px rgba(124, 58, 237, 0.4))`
    - `.glow-white`: `drop-shadow(0 0 10px rgba(255, 255, 255, 0.9)) drop-shadow(0 0 20px rgba(124, 58, 237, 0.4))`
  - **Camera Angle Punch-In:** Class `.punch-zoom` scales video to `1.18x` centered on the talent's face on punch moments.
- **Overlaid Live Visual Elements:**
  - **Top Hook Pill (`#topHookPill`):** Visible from `0.0s` to `4.5s` (`⚡ GTA 6 CLIPS • EARN MONEY 💰`).
  - **Social Comment Card (`#socialCommentPopup`):** Floating glassmorphism card from `3.5s` to `8.2s` (`💬 @alex_clips: "Wait, can you actually make money from GTA 6 clips?"`).
  - **Spoken Pop-Up Badges:** Floating badges popping in on spoken keywords (`🎮 PS5 / GTA 6`, `💰 EARN $1,000+ CASH`, `🔴 YOUTUBE LINK`, `💬 COMMENT 'LINK' BELOW`).
  - **Signature Dual-Size Captions (`#captionsBox`):** White lead word above a massive electric yellow (`#FFE600`) Bebas Neue keyword.
- **Player Controls Bar (`.player-controls-bar`):**
  - Transport buttons: `⏮` (-5s), `▶` (Play/Pause), `⏭` (+5s).
  - Timecode readout: Millisecond-accurate formatted `00:02.8 / 00:46.5`.
  - Audio Volume Slider & Mute Toggle: Live percentage display (`AUDIO 100%`).
  - Aspect Ratio Dropdown Selector: Instant canvas ratio switching.

### 5. Right Customization Panel (`<aside class="right-panel">`)
- **Theme Presets:** Four curated visual identities:
  - *👑 Creator Style:* High-energy yellow/purple branding with active crown badge.
  - *🎬 Cinematic:* High dynamic range, widescreen contrast, cinematic font sizing.
  - *⚡ Tech:* Monospace overlays, cyber cyan accents, terminal badges.
  - *😎 Fun Vibes:* Vibrant pop art colors and playful reaction stickers.
- **Feature Toggles:**
  - `Subject Outline Glow` (ON/OFF).
  - `Dynamic Punch-In Zooms` (ON/OFF).
  - `Animated Pop-Up Messages` (ON/OFF).
- **SFX Soundboard:** Audition library sounds on demand (`vine_boom`, `cash_register`, `level_up`, `bell_chime`, `whoosh`, `pop`).

### 6. Bottom Multi-Track Timeline (`<footer class="timeline-container">`)
- **Time Ruler:** Millisecond-accurate horizontal ruler marked at 5-second intervals with `40px/sec` scaling.
- **Synchronized Tracks:**
  - `👁 Captions`: Real transcript bursts as colored interactive clips (alternating yellow and purple). Clicking any block seeks directly to that word.
  - `🖼 Graphics`: Pop-up message cards and graphic overlay triggers.
  - `🔊 SFX`: Sound effect markers indicating exact audio hit points.
  - `🎵 Music`: Full-width waveform track representing background audio.
- **Playhead Needle:** Purple vertical line (`#A855F7`) with top pointer arrow tracking video progress and supporting direct drag/click seeking.
- **Action Dock:**
  - `▶ Preview`: Synchronously plays or pauses video, SFX, and playhead.
  - `🚀 Export Reel`: Initiates background FFmpeg export.
  - `⬇ Download MP4`: Appears automatically once render finishes.

---

## 5. Master Style Sheet Specifications

The editing engine strictly adheres to the production rules codified in `style-sheet.md`, which were extracted from empirical frame-by-frame analysis of high-performing short-form reels:

### 1. Canvas Framing & Safe Zones
```
┌─────────────────────────────────────────────────────────┐ 0%
│  TOP SAFE ZONE (15% / ~288px) — App UI, Audio Tags      │
│  [Top Hook Banner Lives Here]                           │
├─────────────────────────────────────────────────────────┤ 15%
│                                                         │
│                                                         │
│               ACTION & TEXT SAFE ZONE                   │
│                    (Center 60%)                         │
│             - Talent Face & Eyes                        │
│             - Social Comment Cards                      │
│             - Spoken Badges                             │
│                                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤ 75%
│  CAPTIONS ZONE (Bottom 25% - 32%)                       │
│  [Two-Tone Dynamic Kinetic Subtitles]                   │
├─────────────────────────────────────────────────────────┤ 80%
│  BOTTOM SAFE ZONE (20% / ~384px) — Username, Bio, Tags  │
└─────────────────────────────────────────────────────────┘ 100%
```

### 2. Cut Rhythm & The 2-Second Rule
- **Zero Dead-Air:** All silent pauses and breath intakes exceeding `100ms` are excised. Pacing target is **160 to 190 words per minute**.
- **Visual Reset Interval:** A shot must never remain static for more than **2.0 seconds**. The engine alternates between:
  - *Angle A (Wide):* Default full frame (`scale: 1.0`).
  - *Angle B (Punch-in):* Tight facial crop (`scale: 1.18x - 1.25x`) centered on the talent's eyes during power words.
  - *Angle C (Overlay):* Spoken graphics and social cards entering with spring physics (`scale: 0.8 -> 1.08 -> 1.0`).

### 3. Audio Channel Standards
All exported media is mastered to the following broadcast specification:
- **Dialogue Channel:** Mastered to **`-14.0 LUFS`** with True Peak limited to **`-1.0 dBTP`**. High-pass filtered at 80 Hz with vocal presence boosted between 3.5 kHz and 5 kHz.
- **Sound Effects (SFX):** Mastered between **`-12 dB and -16 dB`**, mixed on exact transient frames.
- **Background Music (BGM):** Mastered between **`-22 dB and -26 dB`** with automatic ducking during active speech.

---

## 6. AI Pipeline & Director Architecture

```
                       RAW VIDEO INPUT
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       FFprobe Video Probe           Audio Extractor
    (Dims, FPS, Duration)          (16kHz Mono WAV)
               │                             │
               │                             ▼
               │                    Groq Whisper Turbo
               │               (Word-Level Timestamps ~4.8s)
               │                             │
               ▼                             ▼
     Group Words into Dynamic Bursts (1-3 words/burst)
                              │
                              ▼
                 AI DIRECTOR REASONING CHAIN
         1. OpenRouter (Nemotron / Gemma / Llama)
         2. Google Gemini (Flash 2.0 / 1.5)
         3. Local Dynamic Semantic Director (Fallback)
                              │
                              ▼
                VALIDATED EDIT DECISION LIST (EDL)
          ├── Captions (Lead text + Keyword + Timestamps)
          ├── Graphics (Top Hook, Comment Card, Badges)
          ├── Sound Effects (Hits, Chimes, Booms)
          └── Zoom Events (Angle Punch-Ins)
```

### Dynamic Burst Grouping Algorithm
Rather than displaying cumbersome multi-sentence subtitle blocks, the pipeline groups words into **high-retention bursts** (1 to 3 words each) based on natural acoustic pauses:
- A burst ends whenever a punctuation mark (`.`, `!`, `?`, `,`) occurs or an acoustic gap greater than `250ms` is detected.
- Each burst is partitioned into a **lead-in phrase** (neutral context) and a **keyword** (the high-impact punch word).

### The 3-Tier Resilient Director Chain
1. **Tier 1 — OpenRouter API:** Prompts state-of-the-art models (`nvidia/nemotron-3.5-lightning`, `google/gemma-4-31b-it`) with strict JSON schema instructions and a 10-second timeout.
2. **Tier 2 — Google Gemini API:** Fallback to `gemini-2.0-flash` or `gemini-1.5-flash` using native JSON mode.
3. **Tier 3 — Local Dynamic Semantic Director:** Deterministic Python provider that scans the transcript bursts for key domain topics:
   - *Gaming/PS5:* Triggers `gamepad` badge + `level_up.wav` SFX + zoom punch-in.
   - *Money/Earning:* Triggers `money` badge + `cash_register.wav` SFX + zoom punch-in.
   - *YouTube/Links:* Triggers `youtube` badge + `pop.wav` SFX.
   - *Platforms/AI:* Triggers `chatgpt` badge + `whoosh.wav` SFX.
   - *Comments/Calls to Action:* Triggers `comment` card + `bell_chime.wav` SFX.

---

## 7. FFmpeg Multi-Layer Rendering & Audio Mastering Engine

Rendering is executed in `engine/render/ffmpeg_reel_builder.py` through a single unified FFmpeg execution graph, avoiding costly intermediate transcoding passes.

### 1. Vector Substation Alpha (.ass) Generation
All visual titles, banners, question cards, and subtitles are written to a temporary `.ass` script styled for the target canvas:

```ass
[Script Info]
Title: Style-Sheet Master Reel
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopHook,Bebas Neue,36,&H000D0E13,&H000000FF,&H0000E6FF,&H0000E6FF,1,0,0,0,100,100,2,0,1,12,3,8,40,40,50,1
Style: CommentCard,Inter,24,&H00111111,&H000000FF,&H00FFFFFF,&H00FFFFFF,1,0,0,0,100,100,0,0,1,10,3,5,60,60,0,1
Style: PopUpBadge,Arial Black,32,&H0000E6FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,6,3,5,40,40,0,1
Style: Lead,Inter,28,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,60,60,140,1
Style: Keyword,Arial Black,56,&H0000E6FF,&H000000FF,&H00000000,&HB0000000,1,0,0,0,100,100,2,0,1,6,3,2,50,50,70,1
```

### 2. Unified Filtergraph Specification
The execution command builds both video scaling/subtitling and audio mixing within `-filter_complex`:

```bash
ffmpeg -y \
  -i "Raw Footage/input_video.mp4" \
  -i "assets/sfx/level_up.wav" \
  -i "assets/sfx/cash_register.wav" \
  -filter_complex "\
    [0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,subtitles='master.ass'[vout];\
    [0:a]loudnorm=I=-14:TP=-1.0:LRA=7,volume=1.4[main_a];\
    [1:a]adelay=800|800,volume=0.9[sfx_1];\
    [2:a]adelay=3500|3500,volume=0.9[sfx_2];\
    [main_a][sfx_1][sfx_2]amix=inputs=3:dropout_transition=2:normalize=0[aout]" \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -preset faster -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -shortest \
  "Export/output_reel.mp4"
```

---

## 8. REST API Reference & Data Models

### 1. `GET /api/status`
Returns service availability, connected API providers, and discovered raw footage.
```json
{
  "status": "ready",
  "groq_connected": true,
  "openrouter_connected": true,
  "gemini_connected": false,
  "raw_videos": [
    {
      "name": "my_video.mp4",
      "size_mb": 10.29,
      "url": "/media/raw/my_video.mp4"
    }
  ]
}
```

### 2. `POST /api/upload`
Uploads a new video file, probes metadata, and returns recommended aspect ratio.
- **Request:** `multipart/form-data` with `file: UploadFile`.
- **Response:**
```json
{
  "success": true,
  "filename": "my_video.mp4",
  "url": "/media/raw/my_video.mp4",
  "duration": 46.49,
  "width": 848,
  "height": 478,
  "fps": 24.63,
  "recommended_aspect": "16:9"
}
```

### 3. `POST /api/chat-edit`
Generates an AI Edit Decision List (EDL) based on transcript bursts and optional prompt instructions.
- **Request:**
```json
{
  "filename": "my_video.mp4",
  "prompt": "Add PS5 game popup and white outline glow",
  "aspect_ratio": "16:9"
}
```
- **Response:**
```json
{
  "success": true,
  "caption_count": 59,
  "graphics_count": 7,
  "sfx_count": 7,
  "ai_response": "I've tailored your edit for 16:9 format...",
  "edl": {
    "video_duration": 46.49,
    "captions": [...],
    "graphics": [...],
    "sound_effects": [...],
    "zoom_events": [...]
  }
}
```

### 4. `POST /api/render`
Renders the final Full HD MP4 video file.
- **Request:**
```json
{
  "filename": "my_video.mp4",
  "edl": { ... },
  "aspect_ratio": "16:9"
}
```
- **Response:**
```json
{
  "success": true,
  "export_filename": "reel_my_video_16x9_1794986495.mp4",
  "download_url": "/media/export/reel_my_video_16x9_1794986495.mp4",
  "file_size_mb": 42.52,
  "aspect_ratio": "16:9"
}
```

---

## 9. Web Audio Architecture & Playback Security

Modern web browsers enforce strict autoplay policies that mute `<video>` and `<audio>` elements unless a direct user gesture has taken place. ClipForge implements a multi-tiered audio unlocking architecture:

```
[User Loads Page] ──> Video Preloads Muted (Safe from Browser Block)
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
[User Clicks Anywhere]                  [User Clicks "▶ Play"]
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
              unmuteAudioNow() Triggered
        ├── 1. video.muted = false
        ├── 2. video.volume = 1.0 (or slider value)
        ├── 3. Pre-unlock SFX Pool (.play() -> .pause())
        └── 4. Hide "Click to Enable Audio" Banner
```

### Audio Safeguards
1. **Fallback Unmute Callout:** If a browser unexpectedly blocks sound, a purple banner (`#unmuteCallout`) appears over the player: *"🔊 Click to Enable Audio"*.
2. **Instant Audio Test Button:** Top header includes a dedicated `🔊 Test Audio` button that plays `cash_register.wav` to verify system output.
3. **SFX Pool Pre-buffering:** All sound effects (`sfxList`) are preloaded into HTML5 `Audio` objects and primed on the first user interaction, ensuring millisecond-accurate sync during playback.

---

## 10. File Structure & Module Responsibilities

```
Reel Editor/
├── assets/
│   ├── cache/logos/                    # Brand SVG vector graphics
│   │   ├── chatgpt.svg, instagram.svg, nodejs.svg,
│   │   └── python.svg, react.svg, tiktok.svg, youtube.svg
│   └── sfx/                            # Core sound effect library (.wav)
│       ├── bell_chime.wav, bruh.wav, bubble_pop.wav, cash_register.wav,
│       └── ding.wav, level_up.wav, pop.wav, vine_boom.wav, whoosh.wav
├── engine/
│   ├── analysis/
│   │   ├── audio_extractor.py          # Extracts 16kHz mono WAV from source video
│   │   ├── video_probe.py              # FFprobe wrapper querying resolution, fps, duration
│   │   ├── pause_detector.py           # Detects speech pauses > 100ms
│   │   └── face_tracker.py             # OpenCV/MediaPipe facial bounding box tracker
│   ├── assets/
│   │   ├── manifest.json               # Asset catalogue (stickers, logos, sfx metadata)
│   │   └── registry.py                 # AssetRegistry class managing local asset paths
│   ├── director/
│   │   ├── director.py                 # Core generate_edl orchestrator
│   │   ├── edl_schema.py               # Pydantic schema for EditDecisionList & cues
│   │   └── validator.py                # Validates timestamps, coordinates, and asset keys
│   ├── providers/
│   │   ├── groq_provider.py            # Groq Whisper API client with word timestamps
│   │   ├── openrouter_provider.py      # OpenRouter multi-model LLM director client
│   │   ├── gemini_provider.py          # Google Gemini AI director client
│   │   └── registry.py                 # Provider chain & LocalHeuristicDirectorProvider
│   ├── render/
│   │   └── ffmpeg_reel_builder.py      # ASS generator and unified FFmpeg renderer
│   ├── web/
│   │   └── index.html                  # ClipForge AI Video Studio single-page application
│   ├── cli.py                          # Headless CLI entry point
│   ├── pipeline.py                     # Synchronous end-to-end pipeline runner
│   └── server.py                       # FastAPI application mounting static routes and APIs
├── Export/                             # Destination directory for rendered MP4 reels
├── Raw Footage/                        # Ingestion directory for input video files
├── Dockerfile                          # Containerization configuration
├── docker-compose.yml                  # Multi-service stack (PostgreSQL, Redis, Ollama)
├── requirements.txt                    # Project Python package dependencies
├── .env.example                        # Template for environment variables and API keys
├── style-sheet.md                      # Empirical viral reel production specification
├── README.md                           # Quickstart and project overview
└── PROJECT_DETAILS.md                  # This master specification document
```
