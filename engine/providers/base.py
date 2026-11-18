"""
Provider abstraction base classes for Reel Editor AI Engine.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float


@dataclass
class TranscriptionResult:
    text: str
    words: list[WordTimestamp] = field(default_factory=list)
    language: str = "en"
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "words": [{"word": w.word, "start": w.start, "end": w.end} for w in self.words],
            "language": self.language,
            "duration": self.duration,
        }


class TranscriptionProvider(abc.ABC):
    """Abstract base for all transcription providers."""

    @abc.abstractmethod
    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio file and return result with word-level timestamps."""
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...


# ---------------------------------------------------------------------------
# Director (EDL generation)
# ---------------------------------------------------------------------------

@dataclass
class DirectorResult:
    edl: dict
    model_used: str
    tokens_used: int = 0
    raw_response: str = ""


class DirectorProvider(abc.ABC):
    """Abstract base for LLM director providers."""

    @abc.abstractmethod
    async def generate_edl(self, prompt: str, context: dict) -> DirectorResult:
        """Generate an EDL from a prompt + context dict."""
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...
