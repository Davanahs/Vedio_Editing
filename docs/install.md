# Reel Editor — Installation Guide

## Prerequisites
- Python 3.11+
- Node.js 18+
- FFmpeg (must be in PATH)
- Docker Desktop (for PostgreSQL + Redis, optional for quick start)

## Quick Start

1. Clone/open the project
2. Run the setup wizard:
   ```bash
   cd "d:\startup\Reel Editor"
   python engine/cli.py setup
   ```
3. Add your API keys when prompted (or edit .env manually)
4. Process a video:
   ```bash
   python engine/cli.py edit "Raw Footage/your_video.mp4"
   ```

## Manual Setup

### Python Dependencies
```bash
pip install -r engine/requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:
- `GROQ_API_KEY`: Get from https://console.groq.com (free tier: 14,400 req/day)
- `GEMINI_API_KEY`: Get from https://aistudio.google.com (free tier)
- `OPENROUTER_API_KEY`: Get from https://openrouter.ai (free models available)

### Docker Services (optional but recommended)
```bash
docker-compose up -d postgres redis
```

### Generate SFX Assets
```bash
python engine/assets/generate_sfx.py
```

## Directory Structure
```
Reel Editor/
├── engine/           # Python AI engine
├── my-video/         # HyperFrames project
├── Raw Footage/      # Input videos
├── Export/           # Output videos  
├── assets/
│   ├── sfx/         # Sound effect files
│   └── cache/logos/ # Cached SVG logos
├── docs/            # Documentation
├── .env             # Your API keys (never commit!)
└── docker-compose.yml
```
