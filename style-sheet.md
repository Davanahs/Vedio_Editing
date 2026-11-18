# Reel Editor Style Sheet & Production Guide
> **Master Reference Spec** distilled from empirical analysis of reference reels in `Style Reference/` (framing, typography, colorimetry, cut pace, transitions, captions, and acoustic mastering).

---

## 1. Canvas & Framing Specifications

| Property | Value | Notes |
| :--- | :--- | :--- |
| **Aspect Ratio** | `9:16` (Vertical) | Native short-form format |
| **Base Resolution** | `1080 × 1920 px` | 720p minimum preview (`720 × 1280 px`) |
| **Frame Rate** | `30 fps` (or `29.97 fps`) | Standard delivery |
| **Top Safe Zone** | `15%` (`~288 px`) | Avoid app top bars (search, audio attribution) |
| **Bottom Safe Zone** | `20%` (`~384 px`) | Avoid handle, caption, music tag |
| **Right Safe Zone** | `18%` (`~195 px`) | Avoid Like, Comment, Share, Bookmark pill column |
| **Action & Text Safe Area** | **Center 60% box** | Primary focal zone for talking head & captions |

---

## 2. Typography Hierarchy & Font System

The reference edits use a signature **High-Low Contrast System**: pairing ultra-bold condensed sans-serifs with clean grotesks and editorial italics.

```
+------------------------------------------------------------------------+
| 1. HOOK / POWER WORDS  -> Ultra-Bold Condensed Sans (All-Caps)         |
| 2. CONTEXT / LEAD-IN   -> Geometric Grotesk (Title Case / Lowercase)   |
| 3. EDITORIAL ACCENTS   -> High-Contrast Elegant Serif (Italic)         |
| 4. UI & TERMINAL CARDS -> Clean Monospace                             |
+------------------------------------------------------------------------+
```

### Font Pairings & Roles

1. **Power Headline / Big Spoken Punch**:
   - **Primary Fonts**: `Bebas Neue`, `Anton`, `Impact`, `Oswald (Heavy)`, `The Bold Font`
   - **Styling**: `font-weight: 900`, `text-transform: uppercase`, `letter-spacing: -0.02em` to `0em`, tight line-height (`0.95`).
   - **Usage**: Behind-head kinetic typography, 1–2 word impact punches ("**LIVE STREAM**", "**TUMHARE PAS**", "**CLAUDE**", "**DEPTH**").

2. **Subtitles & Word-Level Captions**:
   - **Primary Fonts**: `Inter (Bold/ExtraBold)`, `Montserrat (Bold)`, `SF Pro Display (Heavy)`
   - **Styling**: `font-weight: 700 - 800`, tracking `tight`, centered, with 1–3 words per burst.
   - **Dual-size hierarchy**: Small lead word on top (`font-size: 28-36px`), massive keyword below (`font-size: 64-96px`).

3. **Editorial Contrast & Brand Accents**:
   - **Primary Fonts**: `Playfair Display (Italic)`, `Instrument Serif (Italic)`, `Bodoni MT (Italic)`
   - **Styling**: `font-style: italic`, `font-weight: 400 - 600`.
   - **Usage**: Sub-hooks, rhetorical questions, luxury/aesthetic accents (e.g., "*edited this?*", "*I ran out of*").

4. **Developer / Terminal UI / System Badges**:
   - **Primary Fonts**: `JetBrains Mono`, `SF Mono`, `Fira Code`
   - **Styling**: `font-size: 14-18px`, `font-weight: 500`.
   - **Usage**: macOS terminal prompt cards, interactive code blocks, parameter badges.

---

## 3. Colour Palette & Design Tokens

Empirically extracted color swatches from reference footage:

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ #E2F542 / #FFE600│     #FFFFFF     │     #111315     │ #381464 / #6C2BD9│
│  Electric Lime  │   Clean White   │  Obsidian Slate │  Creator Purple │
│ (Primary Accent)│  (Primary Text) │  (Dark UI BG)   │  (Badges / Acc) │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│     #FF007A     │     #F7F7F8     │     #2D7355     │ #FF5F56 #27C93F │
│   Neon Magenta  │  Paper Canvas   │  Organic Green  │  Traffic Lights │
│  (Aura / Glow)  │  (Light BG/Grid)│  (Eco / Health) │ (Red / Grn UI)  │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### Color Token Reference

| Token Name | Hex Code | Role & Practical Application |
| :--- | :--- | :--- |
| `--accent-lime` | `#E2F542` / `#FFE600` | Spoken keyword highlight, subject outline sticker stroke, primary kinetic text |
| `--text-primary` | `#FFFFFF` | Base caption text, titles, contrast against dark backgrounds |
| `--bg-dark-slate` | `#111315` / `#16171D` | Terminal UI background, 3D card backs, letterbox containers |
| `--brand-purple` | `#381464` / `#6C2BD9` | CTA pill buttons ("▶ Render", "Claude Skill"), UI folder accents |
| `--aura-magenta` | `#FF007A` | Glowing neon halo rings around circular creator avatars |
| `--paper-canvas` | `#F7F7F8` / `#F0EFEA` | Lined notebook paper texture background with `#E2E8F0` rule lines |
| `--glass-bg` | `rgba(255,255,255,0.8)` | Frosted glassmorphism name badges (`backdrop-filter: blur(12px)`) |
| `--shadow-text` | `rgba(0, 0, 0, 0.85)` | Text drop shadow (`2px 4px 12px rgba(0,0,0,0.85)`) for legibility |

---

## 4. Cut Pace & Rhythm Architecture

Analysis across the 7 reference reels revealed strict rhythm brackets:

```
[0.0s - 3.0s] HOOK PHASE      -> Cut / visual event every 0.5s - 1.0s (Fastest)
[3.0s - 30.0s] BODY & NARRATIVE -> Cut / angle / punch-in every 1.2s - 2.2s
[CALL TO ACTION] OUTRO          -> Stabilized UI badge + Single direct CTA
```

### Cutting Rules

1. **Zero Dead-Air (Breath Trimming)**:
   - Cut every inhalation and silence > 100 ms.
   - Pacing: **160 to 190 words per minute**.
2. **Visual Reset Interval (The 2-Second Rule)**:
   - Never leave a single shot static for longer than **2.0 seconds**.
   - Alternate between:
     - **Angle A**: Wide / Mid-shot (`scale: 1.0`).
     - **Angle B (Punch-in)**: Tight facial crop (`scale: 1.20 - 1.25`) on punch words.
     - **Angle C (B-roll / UI Overlay)**: Terminal card, screen recording, or 3D mockups.
3. **Beat Synchronization**:
   - Major cuts and text reveals must hit **exactly on the snare, clap, or kick transient** of the background track.

---

## 5. Transitions & Motion Design

### Core Transition Styles
1. **The Scale Jump-Cut (Punch-in / Punch-out)**:
   - Instant 1-frame cut from 1.0x to 1.25x centered on the eyes.
   - Combined with subtle directional camera shake or bass thud.
2. **Spring Physics UI Pop-in**:
   - Floating elements (macOS windows, comment stickers, pill badges) enter using spring overshoot:
   - `scale: 0.8 -> 1.08 -> 1.0` (duration: `300ms`, ease: `cubic-bezier(0.34, 1.56, 0.64, 1)`).
3. **Depth Stacking ("Behind-the-Head" Layering)**:
   - **Layer 1 (Bottom)**: Background video or textured wall.
   - **Layer 2 (Middle)**: Kinetic typography (huge neon yellow Bebas Neue).
   - **Layer 3 (Foreground)**: Rotoscoped cutout of the creator / speaker.
   - Result: Words appear physically trapped in 3D space behind the talent.
4. **Sticker Outline Stroke**:
   - 4px to 6px solid `#FFE600` or `#FFFFFF` border around the talent cutout with subtle jitter/stop-motion styling (2-frame cycle).
5. **Film Burn & Warm Light Leak**:
   - 4–8 frame additive blend (`mix-blend-mode: screen`) orange/golden light leak on chapter turns.

---

## 6. Caption & Subtitle Specifications

```
                       [    Top Hook Banner    ] (Optional)
                              
                              [ TALENT HEAD ]
                                     |
                               [ TALENT CHEST ]
                                     |
                       +-------------------------------+
                       |           agar                |  <- Small White
                       |        TUMHARE PAS            |  <- Huge Neon Yellow
                       +-------------------------------+
                                (Bottom 28%-32%)
```

### Caption Rules
- **Word Count**: **1 to 3 words maximum** visible at any given millisecond.
- **Position**: Horizontal center, vertical anchor at **`bottom: 28% to 32%`** (clears TikTok/Reels UI without obstructing the face).
- **Two-Tone Color Dynamics**:
  - Inactive words: Clean White (`#FFFFFF`).
  - Active spoken keyword: Electric Neon Yellow (`#E2F542` or `#FFE600`).
- **Motion Blur / Kinetic Pop**:
  - Scale punch `1.15x -> 1.0x` on the newly spoken word.
  - Optional motion blur / depth-of-field blur on past words (`filter: blur(2px)`).
- **Legibility Insurance**:
  - `text-shadow: 0px 4px 14px rgba(0, 0, 0, 0.9), 0px 2px 4px rgba(0, 0, 0, 0.9)`.
  - Alternatively, a subtle black pill badge (`background: rgba(0,0,0,0.65)`, `border-radius: 8px`, `padding: 4px 12px`).

---

## 7. Sound Design & Audio Engineering Matrix

All reference videos were mastered to exact short-form streaming standards:

```
[VOICEOVER: -14.0 LUFS] ──┐
[SFX: -14 to -18 dB]   ───┼──> MASTER BUS [Target: -14.0 to -14.5 LUFS | -1.0 dBTP Peak]
[BGM: -22 to -26 dB]   ───┘       (Sidechain ducked by -4 dB during speech)
```

### Audio Channel Standards

| Channel | Target Level | Processing & Plugins |
| :--- | :--- | :--- |
| **Dialogue (Voiceover)** | `-14.0 LUFS` (Peaks: `-3.0 dB`) | High-pass filter at 80 Hz, vocal warmth at 200 Hz, clarity presence boost at 3.5–5 kHz. 3:1 ratio fast compressor. De-esser at 6.5 kHz. |
| **Background Music (BGM)** | `-22 dB to -26 dB` | Lo-fi trap, energetic boom-bap, synth groove, or acoustic indie. **Sidechain ducking: -4 dB gain reduction** triggered by dialogue. |
| **Sound Effects (SFX)** | `-12 dB to -16 dB` | Timed to visual hit-frames (see sound palette below). |
| **Master Bus** | **`-14.0 to -14.5 LUFS`** | True Peak limit: `-1.0 dBTP`. Loudness Range (LRA): `< 3.5 LU`. |

### Standard SFX Repertoire
1. **Whoosh / Fast Swish**: Triggers on punch-ins, whip cuts, sliding UI cards.
2. **UI Pop / Bubble Blip**: Triggers on comment cards, pill badges, and app icon appearances.
3. **Sub Bass Impact / Thud**: Triggers at second 0.0 (Hook entry) and major chapter shifts.
4. **Paper Rip / Page Turn**: Triggers on notebook or collage texture reveals.
5. **Mouse Click / Keyboard Clack**: Triggers on terminal UI commands and computer mockups.
6. **Bell Chime / Cash Register Ding**: Triggers on call to action ("Comment LIVE", "Comment EDIT").

---

## 8. Reusable Template Blueprints (Code Tokens)

### CSS Preset for HyperFrames / HTML Compositions
```css
:root {
  --font-impact: "Bebas Neue", "Impact", "Oswald", sans-serif;
  --font-body: "Inter", "Montserrat", -apple-system, sans-serif;
  --font-editorial: "Playfair Display", "Georgia", serif;
  --font-mono: "JetBrains Mono", "SF Mono", monospace;

  --accent-lime: #E2F542;
  --accent-yellow: #FFE600;
  --accent-purple: #381464;
  --dark-slate: #111315;
  --white: #FFFFFF;
}

/* Dynamic Active Subtitle */
.caption-box {
  position: absolute;
  bottom: 30%;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  width: 90%;
  pointer-events: none;
}

.caption-lead {
  font-family: var(--font-body);
  font-size: 32px;
  font-weight: 700;
  color: var(--white);
  text-shadow: 0 4px 12px rgba(0,0,0,0.9);
  text-transform: lowercase;
}

.caption-keyword {
  font-family: var(--font-impact);
  font-size: 84px;
  line-height: 0.95;
  font-weight: 900;
  color: var(--accent-lime);
  text-transform: uppercase;
  text-shadow: 0 6px 16px rgba(0,0,0,0.95);
  letter-spacing: 0.01em;
}

/* Floating Glassmorphism Badge */
.glass-badge {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(14px);
  border-radius: 9999px;
  padding: 8px 22px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
  font-family: var(--font-body);
  font-weight: 700;
  color: var(--accent-purple);
}
```

### FFmpeg Quick Audio Mastering Chain
```bash
# Normalize voiceover and mix with sidechain ducked music to -14 LUFS target:
ffmpeg -i voice.wav -i bgm.mp3 \
  -filter_complex "[1:a]volume=0.12[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:LRA=3:TP=-1" \
  -c:a aac -b:a 192k mastered_audio.mp4
```
