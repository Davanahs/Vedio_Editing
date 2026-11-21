"""Shared, named motion presets used by browser preview and FFmpeg rendering."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AnimationDefinition:
    name: str
    kind: str
    entrance_seconds: float = 0.28
    exit_seconds: float = 0.22
    description: str = ""


ANIMATIONS = {
    "fade": AnimationDefinition("fade", "fade", description="Fade in and out"),
    "scale": AnimationDefinition("scale", "scale", description="Scale in and out"),
    "slide": AnimationDefinition("slide", "slide", description="Slide in and out"),
    "rotate": AnimationDefinition("rotate", "rotate", description="Gentle rotation"),
    "float": AnimationDefinition("float", "float", description="Slow floating motion"),
    "pop": AnimationDefinition("pop", "pop", description="Spring-like sticker entrance"),
    "glitter": AnimationDefinition("glitter", "glitter", description="Pulsing glitter highlight"),
    "pop_fade": AnimationDefinition("pop_fade", "pop_fade", description="Pop entrance with fade exit"),
}

ALIASES = {
    "pop_in": "pop", "spring_in": "pop", "bounce_in": "pop", "tilt_pop": "pop_fade",
    "slide_fade": "slide", "glass_slide": "slide", "soft_float": "float",
    "soft_bounce": "pop", "glow_expand": "glitter", "pulse_wave": "glitter",
    "blink_in": "fade", "retro_snap": "pop_fade", "draw_on": "slide",
}


def get_animation(name: str | None) -> AnimationDefinition:
    normalized = (name or "fade").strip().lower()
    normalized = ALIASES.get(normalized, normalized)
    return ANIMATIONS.get(normalized, ANIMATIONS["fade"])


def animation_catalog() -> list[dict]:
    return [asdict(value) for value in ANIMATIONS.values()]
