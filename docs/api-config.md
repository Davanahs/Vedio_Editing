# API Configuration Guide

## Groq API (Transcription — RECOMMENDED)
- Sign up: https://console.groq.com
- Free tier: 14,400 requests/day, 7,200 audio minutes/day
- Model used: `whisper-large-v3-turbo`
- Speed: ~0.4 seconds for a 48s video
- Set: `GROQ_API_KEY=gsk_...`

## Google Gemini API (AI Director)
- Sign up: https://aistudio.google.com
- Free tier: 1,500 requests/day (Gemini 1.5 Flash)
- Model used: `gemini-2.0-flash-lite` or `gemini-1.5-flash`
- Set: `GEMINI_API_KEY=AIza...`

## OpenRouter (AI Director — Fallback)
- Sign up: https://openrouter.ai
- Free models: `google/gemma-3-27b-it:free`, `meta-llama/llama-3.3-70b-instruct:free`
- No billing required for free models
- Set: `OPENROUTER_API_KEY=sk-or-...`

## Provider Priority
1. Transcription: Groq Whisper → Local faster-whisper (CPU)
2. Director: Gemini Flash → OpenRouter free models → Error

## Without Any API Keys
The engine will fall back to:
- Local faster-whisper for transcription (slow, ~3-5 min for 48s video)
- No AI Director (captions only, no contextual graphics)
