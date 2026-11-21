"""
Distinct Visual Treatments & Cinematic Stylization Engine.
Generates template-specific color grades, film textures, vignettes,
HUD overlays, glowing borders, and lighting effects for FFmpeg compositions.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


def get_template_color_grade(template_id: str, intensity: str = "creative") -> str:
    """
    Returns an aggressive, highly visible cinematic color grading filter string.
    Makes the visual transformation immediately noticeable compared to raw footage.
    """
    if intensity == "subtle":
        if template_id == "pinterest_scrapbook":
            return "eq=contrast=1.06:brightness=0.02:saturation=1.12"
        elif template_id == "glassmorphism":
            return "eq=contrast=1.08:brightness=0.01:saturation=1.18"
        elif template_id == "retro_camera":
            return "eq=contrast=1.05:saturation=0.92"
        elif template_id == "aesthetic_lifestyle":
            return "eq=contrast=1.03:brightness=0.02:saturation=1.10"
        elif template_id == "creative_minimal":
            return "eq=contrast=1.04:saturation=1.02"
        else:
            return "eq=contrast=1.05:saturation=1.10"

    mult = 1.3 if intensity == "high_energy" else (1.0 if intensity == "creative" else 0.7)

    if template_id == "pinterest_scrapbook":
        # Warm golden-hour paper aesthetic with rich contrast and sunny warmth
        contrast = round(1.0 + 0.16 * mult, 2)
        saturation = round(1.0 + 0.28 * mult, 2)
        brightness = 0.03
        return f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation},colorbalance=rs=0.08:gs=0.03:bs=-0.06:rm=0.06:gm=0.02:bm=-0.05"

    elif template_id == "retro_camera":
        # 90s analogue camcorder / VHS with crushed blacks and slight color drift
        contrast = round(1.0 + 0.20 * mult, 2)
        saturation = round(0.88 - 0.05 * mult, 2)
        return f"eq=contrast={contrast}:brightness=-0.02:saturation={saturation},colorbalance=rs=0.04:gs=-0.02:bs=0.08"

    elif template_id == "glassmorphism":
        # High-tech electric cyber-clean with punchy contrast and vibrant cyan/magenta highlights
        contrast = round(1.0 + 0.22 * mult, 2)
        saturation = round(1.0 + 0.32 * mult, 2)
        return f"eq=contrast={contrast}:brightness=0.01:saturation={saturation},colorbalance=rs=-0.04:gs=0.06:bs=0.12:rh=0.05:gh=-0.02:bh=0.08"

    elif template_id == "aesthetic_lifestyle":
        # Dreamy soft pastel film with lifted shadows and creamy tones
        contrast = round(1.0 + 0.12 * mult, 2)
        saturation = round(1.0 + 0.20 * mult, 2)
        brightness = 0.04
        return f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation},colorbalance=rs=0.05:gs=0.02:bs=0.06"

    elif template_id == "floating_music_player":
        # Modern streaming platform mood: deep obsidian blacks with crisp saturation
        contrast = round(1.0 + 0.18 * mult, 2)
        saturation = round(1.0 + 0.24 * mult, 2)
        return f"eq=contrast={contrast}:brightness=-0.01:saturation={saturation}"

    elif template_id == "creative_minimal":
        # Scandinavian high-key studio: crisp, clean, neutral perfection
        contrast = round(1.0 + 0.15 * mult, 2)
        saturation = 1.05
        return f"eq=contrast={contrast}:brightness=0.01:saturation={saturation}"

    else:
        # Auto Creative: balanced punchy modern reel
        contrast = round(1.0 + 0.16 * mult, 2)
        saturation = round(1.0 + 0.22 * mult, 2)
        return f"eq=contrast={contrast}:brightness=0.02:saturation={saturation}"


def get_template_texture_filters(template_id: str, intensity: str = "creative") -> List[str]:
    """
    Returns visual texture filters (film grain, vignette, glow) specific to the template.
    """
    filters = []

    if intensity == "subtle":
        return filters

    if template_id == "retro_camera":
        # Analogue film grain and camera vignette
        noise_amt = 16 if intensity == "high_energy" else 12
        filters.append(f"noise=alls={noise_amt}:allf=t+u")
        filters.append("vignette=PI/4.2:eval=init")

    elif template_id == "pinterest_scrapbook":
        # Soft warm vignette and subtle paper grain
        filters.append("vignette=PI/3.8:eval=init")

    elif template_id == "aesthetic_lifestyle":
        # Soft focus edge vignette
        filters.append("vignette=PI/3.5:eval=init")

    elif template_id == "glassmorphism":
        # Subtle vignette to emphasize glowing center cards
        filters.append("vignette=PI/4.5:eval=init")

    return filters
