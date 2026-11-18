"""
Local Whisper provider — uses faster-whisper for offline transcription.
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import TranscriptionProvider, TranscriptionResult, WordTimestamp

try:
    from faster_whisper import WhisperModel
    _FW_AVAILABLE = True
except ImportError:
    _FW_AVAILABLE = False


class LocalWhisperProvider(TranscriptionProvider):
    """
    Uses faster-whisper (CTranslate2-based) for fast local transcription.
    Default model: base.en (small and fast).
    """

    DEFAULT_MODEL = "base.en"

    def __init__(
        self,
        model_size: str | None = None,
        cache_dir: str | None = None,
        device: str = "auto",
    ):
        if not _FW_AVAILABLE:
            raise ImportError(
                "faster-whisper not installed. Run: pip install faster-whisper>=1.0.0"
            )
        self._model_size = model_size or os.environ.get("WHISPER_MODEL", self.DEFAULT_MODEL)
        self._cache_dir = cache_dir or os.environ.get(
            "MODEL_CACHE_DIR",
            str(Path.home() / ".cache" / "reel-engine" / "models"),
        )
        Path(self._cache_dir).mkdir(parents=True, exist_ok=True)

        # Determine compute type based on device
        compute_type = "int8"
        if device == "auto":
            device = "cpu"  # Safe default; faster-whisper auto-detects CUDA
        self._model = WhisperModel(
            self._model_size,
            device=device,
            compute_type=compute_type,
            download_root=self._cache_dir,
        )

    @property
    def name(self) -> str:
        return f"Local Whisper ({self._model_size})"

    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        import asyncio

        audio_path = str(audio_path)
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Run synchronous faster-whisper in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._transcribe_sync, audio_path)
        return result

    def _transcribe_sync(self, audio_path: str) -> TranscriptionResult:
        segments, info = self._model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            language="en",
            vad_filter=True,
        )

        full_text_parts: list[str] = []
        words: list[WordTimestamp] = []

        for segment in segments:
            full_text_parts.append(segment.text.strip())
            if segment.words:
                for w in segment.words:
                    words.append(WordTimestamp(
                        word=w.word.strip(),
                        start=float(w.start),
                        end=float(w.end),
                    ))

        return TranscriptionResult(
            text=" ".join(full_text_parts),
            words=words,
            language=info.language or "en",
            duration=float(info.duration or 0.0),
        )
