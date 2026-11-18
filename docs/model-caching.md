# Model Caching Guide

## Groq (Cloud API)
No local model storage needed. Groq runs Whisper in the cloud.

## faster-whisper (Local Fallback)
Models cached at: `C:/Users/Davana/.cache/reel-engine/models/`
Default model: `base.en` (74MB)

Change model size in .env:
```
WHISPER_MODEL=base.en   # 74MB, fastest
WHISPER_MODEL=small.en  # 244MB, more accurate  
WHISPER_MODEL=medium.en # 769MB, most accurate
```

## HyperFrames
Font cache: `C:/Users/Davana/.cache/hyperframes/fonts/`
Fonts are auto-downloaded on first render.

## Asset Cache
Logos cached at: `D:/startup/Reel Editor/assets/cache/logos/`
To re-download logos: delete the cache directory.
