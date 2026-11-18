"""
Groq provider — Whisper transcription + (optional) director via groq LLM.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from .base import TranscriptionProvider, TranscriptionResult, WordTimestamp

try:
    from groq import AsyncGroq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False


class GroqTranscriptionProvider(TranscriptionProvider):
    """
    Uses Groq Whisper API for fast cloud transcription with word-level timestamps.
    Model: whisper-large-v3-turbo
    """

    MODEL = "whisper-large-v3-turbo"

    def __init__(self, api_key: str | None = None):
        if not _GROQ_AVAILABLE:
            raise ImportError("groq package not installed. Run: pip install groq>=1.0.0")
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Get your key at https://console.groq.com"
            )
        self._client = AsyncGroq(api_key=self._api_key)

    @property
    def name(self) -> str:
        return "Groq Whisper (cloud)"

    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        audio_path = str(audio_path)
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        file_size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(
                f"Audio file is {file_size_mb:.1f} MB — Groq limit is 25 MB. "
                "Split the audio or use local Whisper instead."
            )

        with open(audio_path, "rb") as f:
            try:
                response = await self._client.audio.transcriptions.create(
                    file=(Path(audio_path).name, f),
                    model=self.MODEL,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                    language="en",
                )
            except Exception as e:
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str:
                    raise RuntimeError(
                        "Groq rate limit hit. Wait a moment then retry, "
                        "or switch to local Whisper."
                    ) from e
                if "401" in err_str or "unauthorized" in err_str:
                    raise RuntimeError(
                        "Groq API key invalid. Check GROQ_API_KEY in your .env file."
                    ) from e
                raise RuntimeError(f"Groq transcription failed: {e}") from e

        words: list[WordTimestamp] = []
        if isinstance(response, dict):
            raw_words = response.get("words", [])
            text_str = response.get("text", "")
            duration = float(response.get("duration", 0.0))
            language = response.get("language", "en") or "en"
        else:
            raw_words = getattr(response, "words", None) or []
            text_str = getattr(response, "text", "")
            duration = float(getattr(response, "duration", 0.0))
            language = getattr(response, "language", "en") or "en"

        for w in raw_words:
            if isinstance(w, dict):
                w_str = w.get("word", "")
                s = float(w.get("start", 0.0))
                e = float(w.get("end", 0.0))
            else:
                w_str = getattr(w, "word", "")
                s = float(getattr(w, "start", 0.0))
                e = float(getattr(w, "end", 0.0))

            clean = w_str.strip()
            if clean:
                words.append(WordTimestamp(word=clean, start=s, end=e))

        return TranscriptionResult(
            text=text_str.strip(),
            words=words,
            language=language,
            duration=duration,
        )
