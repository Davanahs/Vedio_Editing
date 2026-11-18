# Reel Editor AI Studio — User Guide

## Quick Start (Web Studio)

1. Open your browser and navigate to:
   **http://localhost:5050**

2. Features:
   - **Drag & Drop**: Drop any video (`.mp4`, `.mov`) directly onto the browser window.
   - **AI Chatbot**: Tell the AI how you want the video edited:
     - *"Add energetic zoom transitions on keywords"*
     - *"Make it a funny meme edit with vine-boom and bruh SFX"*
     - *"This is silent b-roll, add fast cuts and subtle chimes"*
   - **Live 9:16 Interactive Canvas**: Watch the real video playing with synchronized animated captions, popups, and sound effects.
   - **Full HD 1080×1920 Export**: Click **Render Full HD** to produce an export in `Export/` and download it directly.

## Command Line Alternative

```bash
python engine/cli.py edit "Raw Footage/my_vid.mp4"
```
