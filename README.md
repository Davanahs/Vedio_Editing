# Aura ✦ AI Creative Video Studio

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-6.0+-007808.svg)
![Groq](https://img.shields.io/badge/Groq%20Whisper-Cloud%20Fast-F55036.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**An autonomous AI short-form creative video studio that transforms raw footage and uploaded resources into Pinterest-inspired scrapbook reels, floating music-player compositions, and aesthetic glassmorphism edits in seconds.**

[Features](#-key-features) • [Quickstart](#-quickstart-guide) • [Architecture](#-architecture--pipeline) • [Style Guide](style-sheet.md) • [Full Specification](PROJECT_DETAILS.md) • [API Reference](#-api-reference)

</div>

---

## 🌟 Overview

**Aura AI Creative Studio** is a prompt-based autonomous video editing studio designed for creators, aesthetic storytellers, and creative agencies. Instead of manual editing timelines, Aura uses an AI Creative Director that analyzes raw video footage alongside user-uploaded photographs, audio, and logos to compose aesthetic, high-retention video compositions:

- **Pinterest-Inspired Scrapbook Compositions**: Layered Polaroid photographs, hand-drawn white outlines around subjects, floating flowers, stars, hearts, and retro camera overlays.
- **Floating Music Player Interfaces**: Large perspective music player cards (Spotify / Apple Music aesthetics), album art panels, playback controls, and realistic drop shadows.
- **Floating Glassmorphism Panels**: Translucent frosted-glass cards orbiting subjects with neon cyan and pink glow trails.
- **Speed Benchmark**: Processes and renders a 48-second video in **under 30 seconds** on standard hardware.
- **Audio Mastering**: Normalizes speech loudness to streaming broadcast standards (**`-14.0 LUFS`**) and synchronizes sound effects to visual transients.
- **Multi-Aspect Ratio Canvas**: Seamlessly switches between `9:16` (Vertical Reels/TikTok/Shorts), `16:9` (YouTube/Landscape), and `1:1` (Square).

---

## 🚀 Key Features

### 1. Aura AI Studio Web Workspace (`localhost:5050`)
- **Three-Panel Creative Layout**:
  - **Left Panel (Resources)**: Source footage management, multi-resource upload (Photos, Audio, Graphics, Logos), category filters, and active asset attachment toggles.
  - **Center Panel (Video Preview Studio)**: Real-time video player with original vs. AI-edited comparison mode, aspect ratio switcher (`9:16`, `16:9`, `1:1`), outline style switcher (white, neon yellow), and live aesthetic overlays.
  - **Right Panel (AI Creative Director)**: Natural-language creative prompt input, 8+ visual style explorer cards, creative elements capability preview, and real-time multi-stage AI processing tracker.
- **Interactive Multi-Track Timeline**: Synchronized tracks for `👁 Captions`, `🖼 Scrapbook / Graphics`, `🔊 SFX Hits`, and `🎵 Music Master` with scrubbing and real-time playhead.
- **Dynamic AI Suggestions**: Transcript-aware edit suggestions with instant toggle switches.
- **Subject Outline Glow**: Dynamic neon yellow or crisp white glowing outline around the talent.
- **Foolproof Audio Playback**: Direct audio unmuting with explicit volume controls and an instant speaker test button.

### 2. Autonomous Multi-Tier Director Pipeline
- **Transcription**: Groq Cloud Whisper with word-level timestamps (~4.8s for 48s audio) with local Whisper fallback.
- **Resilient AI Director**: 3-stage fallback chain:
  1. *Google Gemini* (`gemini-2.0-flash` / `gemini-1.5-flash`)
  2. *OpenRouter* (`nvidia/nemotron-3.5-lightning`, `google/gemma`, `meta-llama`)
  3. *Local Dynamic Semantic Director* (Zero-cost, instant transcript parsing for contextual keywords)

### 3. High-Speed Direct FFmpeg Renderer
- High-efficiency unified filtergraph rendering 1080p Full HD MP4s at **60+ FPS** (~25s render time).
- Direct ASS layer subtitle burning for zero degradation and broadcast-quality font rendering.
- Stereo AAC 192k audio mixing with volume ducking and loudness normalization.

### 4. Strict Project Isolation
- State and timeline tracks are cleanly isolated per video. Switching or uploading a new file completely wipes previous assets to prevent cross-contamination.

---

## 📁 Repository Structure

```
Reel Editor/
├── assets/
│   ├── cache/logos/        # SVG brand logos (YouTube, ChatGPT, TikTok, Python...)
│   └── sfx/                # Core sound effects (vine_boom, cash_register, level_up, ding...)
├── docs/                   # Architecture documentation & diagrams
├── engine/
│   ├── analysis/           # Video probe, audio extractor, pause & face tracking
│   ├── assets/             # Asset registry and manifest.json
│   ├── director/           # EDL generator, schema models, and validator
│   ├── providers/          # Groq, OpenRouter, Gemini, and Local Director providers
│   ├── render/             # Direct FFmpeg reel builder & GPU acceleration detector
│   ├── web/                # ClipForge Web Studio interface (index.html)
│   ├── cli.py              # CLI entry point for headless automation
│   ├── pipeline.py         # End-to-end editing pipeline
│   └── server.py           # FastAPI Web Studio server
├── Export/                 # Generated Full HD MP4 outputs
├── Raw Footage/            # Input video footage
├── Dockerfile              # Containerized deployment definition
├── docker-compose.yml      # Orchestration for PostgreSQL, Redis, and Ollama
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variable template
├── style-sheet.md          # Master reference style sheet & production guidelines
└── README.md               # Project documentation
```

---

## ⚡ Quickstart Guide

### Prerequisites
1. **Python 3.11+** or **3.12**
2. **FFmpeg** installed and accessible on your system `PATH`:
   - **Windows**: `winget install Gyan.FFmpeg` or download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/your-username/reel-editor.git
cd reel-editor

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the `.env.example` template to `.env` and configure your API keys:

```bash
cp .env.example .env
```

Open `.env` and provide your keys:

```ini
# Recommended for fast transcription (~4.8s):
GROQ_API_KEY=gsk_your_groq_api_key_here

# Recommended for AI Director decision making:
OPENROUTER_API_KEY=sk-or-your_openrouter_api_key_here
# or:
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here
```

*(Note: Even without external API keys, the engine automatically falls back to local transcription and the Dynamic Semantic Director).*

---

## 🖥️ Running ClipForge

### Option A: Launch the Web Studio (Interactive UI)

Start the local studio server:

```bash
python -m uvicorn engine.server:app --host 127.0.0.1 --port 5050
```

Open your browser and navigate to:
👉 **[http://localhost:5050](http://localhost:5050)**

1. Drag and drop any raw video file or click **`Project ⌵`** to pick existing footage.
2. Type custom styling prompts in the top prompt bar (e.g., *"Make it horizontal with a white outline glow"*).
3. Switch aspect ratios (`16:9`, `9:16`, `1:1`) dynamically.
4. Click **`🚀 Export Reel`** to render your Full HD MP4 in ~25 seconds.

---

### Option B: Headless Command-Line Interface (CLI)

Run autonomous editing directly from your terminal:

```bash
# Basic autonomous edit
python engine/cli.py edit "Raw Footage/my_vid.mp4"

# Edit with custom preset and aspect ratio
python engine/cli.py edit "Raw Footage/my_vid.mp4" --preset viral --aspect 9:16

# Dry-run analysis (inspect generated EDL without rendering video)
python engine/cli.py edit "Raw Footage/my_vid.mp4" --dry-run
```

---

### Option C: Run via Docker

```bash
# Build the Docker image
docker build -t clipforge .

# Run container on port 5050
docker run -p 5050:5050 --env-file .env clipforge
```

---

## 🎨 Master Style Sheet Integration

ClipForge implements the production rules established in [style-sheet.md](style-sheet.md) based on empirical analysis of viral reference reels:

| Production Rule | Implementation | Style Token |
| :--- | :--- | :--- |
| **Top Hook Pill** | Prominent banner at `0.0s - 4.5s` | `#FFE600` background, `Bebas Neue`, black text |
| **Social Question Card** | Glassmorphism card at `3.5s - 8.2s` | Avatar + `@alex_clips` question with spring physics |
| **Spoken Pop-Up Badges** | Contextual badges on keywords | `🎮 PS5/Gaming`, `💰 Cash`, `🔴 YouTube`, `💬 Comment` |
| **Angle Punch-Ins** | 2-Second rule jump cuts | Camera zooms `1.18x` on power words, then resets |
| **Two-Tone Captions** | High-contrast kinetic typography | White lead word (`Inter`) + Neon Yellow keyword (`Bebas Neue`) |
| **Loudness Standards** | Broadcast audio mastering | Voiceover `-14.0 LUFS`, SFX transients at `-14 dB` |

---

## 📡 API Reference

The FastAPI backend exposes clean REST endpoints:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | Returns system health, connected AI providers, and raw footage files. |
| `GET` | `/api/assets` | Returns available sound effects, logos, and graphic stickers. |
| `POST` | `/api/upload` | Uploads a raw video file, probes dimensions, and returns metadata. |
| `POST` | `/api/chat-edit` | Directs video: transcribes audio, parses instructions, and generates EDL. |
| `POST` | `/api/render` | Executes high-speed FFmpeg render with burned graphics and mastered audio. |

---

## 🛠️ Performance & Troubleshooting

- **No Sound in Browser Preview?**: Click the **`🔊 Test Audio`** button in the header or click anywhere on the video canvas to unlock browser Web Audio.
- **FFmpeg Not Found**: Ensure FFmpeg is added to your system `PATH`. Run `ffmpeg -version` in your terminal to verify.
- **Slow Processing?**: Check that your `GROQ_API_KEY` is configured in `.env`. Groq Whisper processes audio in under 5 seconds compared to 45+ seconds on CPU.
- **Port Conflict**: Change the port by starting uvicorn with `--port 5051` or setting `STUDIO_PORT=5051` in `.env`.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
