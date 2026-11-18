"""
EDL (Edit Decision List) Pydantic v2 schema for Reel Editor.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CaptionBurst(BaseModel):
    id: str
    start: float
    end: float
    lead: str = ""
    keyword: str
    style: Literal["default", "power", "whisper", "hype"] = "default"
    highlight_color: str = "#FFE600"


class ZoomEvent(BaseModel):
    id: str
    start: float
    end: float
    scale: float = 1.15
    target: Literal["face", "center", "text"] = "face"
    ease: str = "power2.inOut"

    @field_validator("scale")
    @classmethod
    def clamp_scale(cls, v: float) -> float:
        return max(1.0, min(1.4, v))


class GraphicElement(BaseModel):
    id: str
    asset_id: str
    start: float
    end: float
    x: int = Field(ge=0, le=1080)
    y: int = Field(ge=0, le=1920)
    width: int
    height: int
    animation: Literal["spring_in", "bounce_in", "slide_up", "fade_in"] = "spring_in"
    trigger_word: str = ""


class SoundEffect(BaseModel):
    id: str
    asset_id: str
    start: float
    volume: float = Field(default=0.8, ge=0.0, le=1.0)


class MusicTrack(BaseModel):
    asset_id: str
    start: float = 0.0
    volume: float = Field(default=0.15, ge=0.0, le=1.0)
    duck_during_speech: bool = True


class EditDecisionList(BaseModel):
    version: str = "1.0"
    video_duration: float
    captions: list[CaptionBurst] = Field(default_factory=list)
    zoom_events: list[ZoomEvent] = Field(default_factory=list)
    graphics: list[GraphicElement] = Field(default_factory=list)
    sound_effects: list[SoundEffect] = Field(default_factory=list)
    music: MusicTrack | None = None
    color_grade: Literal["dark_moody", "warm_cinematic", "cool_editorial"] = "dark_moody"
