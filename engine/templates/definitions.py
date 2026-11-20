"""
Creative Templates System for Autonomous Video Editing.
Defines the 7 creative design systems:
1. Pinterest Scrapbook
2. Aesthetic Lifestyle
3. Floating Music Player
4. Glassmorphism
5. Retro Camera
6. Creative Minimal
7. Auto Creative

Core Principle:
- The template controls HOW the video looks (layout, typography, palette, animation, badges).
- The video content controls WHAT elements are appropriate (semantic relevance).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class CreativeTemplate:
    id: str
    name: str
    description: str
    tagline: str
    visual_identity: str
    typography_theme: str
    color_palette: Dict[str, str]
    animation_preference: str
    badge_style: str  # polaroid | music_player | glass_pill | retro_hud | minimal_tag | auto
    max_elements_per_minute: int
    max_simultaneous: int
    min_element_gap_s: float
    preferred_animations: List[str]
    composition_rules: Dict[str, str]
    badge_theme_css: str

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tagline": self.tagline,
            "visual_identity": self.visual_identity,
            "typography_theme": self.typography_theme,
            "color_palette": self.color_palette,
            "animation_preference": self.animation_preference,
            "badge_style": self.badge_style,
            "max_elements_per_minute": self.max_elements_per_minute,
            "max_simultaneous": self.max_simultaneous,
            "preferred_animations": self.preferred_animations,
            "composition_rules": self.composition_rules,
            "badge_theme_css": self.badge_theme_css,
        }


TEMPLATES: Dict[str, CreativeTemplate] = {
    "pinterest_scrapbook": CreativeTemplate(
        id="pinterest_scrapbook",
        name="Pinterest Scrapbook",
        tagline="Handcrafted Polaroid frames, doodles, soft shadows & layered depth",
        description="Scrapbook collage aesthetic with tilted frames, white paper borders, cute pins, and layered textures.",
        visual_identity="Layered polaroids, hand-drawn paper cutouts, soft organic shadows, warm nostalgic charm.",
        typography_theme="Playful Sans & Script accents (Inter Bold + Kalam/Caveat feel)",
        color_palette={
            "primary": "#FFE4E6",       # Soft warm blush
            "accent": "#F43F5E",        # Rose red
            "card_bg": "rgba(255, 255, 255, 0.95)",
            "border": "#FFFFFF",
            "text": "#1E293B",
            "shadow": "rgba(0,0,0,0.25)"
        },
        animation_preference="tilt_pop",
        badge_style="polaroid",
        max_elements_per_minute=6,
        max_simultaneous=1,
        min_element_gap_s=3.0,
        preferred_animations=["tilt_pop", "paper_drop", "soft_bounce"],
        composition_rules={
            "rotation_deg": "-3 to 4",
            "border_width_px": "10",
            "shadow_blur_px": "18",
            "position": "top_right_or_side"
        },
        badge_theme_css="background:#ffffff; color:#18181b; border: 4px solid #ffffff; box-shadow: 0 12px 28px rgba(0,0,0,0.3); border-radius: 8px; transform: rotate(-2deg);"
    ),

    "aesthetic_lifestyle": CreativeTemplate(
        id="aesthetic_lifestyle",
        name="Aesthetic Lifestyle",
        tagline="Gentle pastels, clean floating highlights & serene typography",
        description="Clean, chic, pastel aesthetic with minimal organic stickers, elegant typography, and serene pacing.",
        visual_identity="Pastel tones, floating photographs, soft organic curves, warm sunlight feeling, clean negative space.",
        typography_theme="Modern Editorial Sans (Inter Regular + SemiBold)",
        color_palette={
            "primary": "#FEF3C7",       # Soft pastel amber
            "accent": "#EC4899",        # Soft pink
            "card_bg": "rgba(255, 255, 255, 0.88)",
            "border": "rgba(255, 255, 255, 0.6)",
            "text": "#0F172A",
            "shadow": "rgba(0,0,0,0.15)"
        },
        animation_preference="soft_float",
        badge_style="minimal_tag",
        max_elements_per_minute=5,
        max_simultaneous=1,
        min_element_gap_s=4.0,
        preferred_animations=["soft_float", "fade_up", "gentle_scale"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "2",
            "shadow_blur_px": "14",
            "position": "top_left_or_pill"
        },
        badge_theme_css="background:rgba(255,255,255,0.92); color:#1e293b; border: 1.5px solid rgba(226,232,240,0.8); box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 20px;"
    ),

    "floating_music_player": CreativeTemplate(
        id="floating_music_player",
        name="Floating Music Player",
        tagline="Spotify-inspired translucent cards, playback progress & album art panels",
        description="Modern streaming UI aesthetic with floating track cards, scrub bars, perspective tilt, and music vibes.",
        visual_identity="Floating playback UI, album art thumbnails, scrubbing waveforms, sleek dark glass, Spotify vibes.",
        typography_theme="Clean Geometric Sans (Circular / Inter Bold)",
        color_palette={
            "primary": "#1DB954",       # Spotify green
            "accent": "#38BDF8",        # Electric cyan
            "card_bg": "rgba(18, 18, 18, 0.85)",
            "border": "rgba(255, 255, 255, 0.15)",
            "text": "#FFFFFF",
            "shadow": "rgba(0,0,0,0.5)"
        },
        animation_preference="glass_slide",
        badge_style="music_player",
        max_elements_per_minute=5,
        max_simultaneous=1,
        min_element_gap_s=4.0,
        preferred_animations=["glass_slide", "pulse_wave", "smooth_in"],
        composition_rules={
            "rotation_deg": "1 to 3",
            "border_width_px": "1",
            "shadow_blur_px": "24",
            "position": "top_right_floating"
        },
        badge_theme_css="background:rgba(18,18,18,0.88); backdrop-filter:blur(16px); color:#ffffff; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 16px 36px rgba(0,0,0,0.5); border-radius: 16px;"
    ),

    "glassmorphism": CreativeTemplate(
        id="glassmorphism",
        name="Glassmorphism",
        tagline="Translucent frosted glass, subtle cyan & pink glowing borders",
        description="Futuristic frosted-glass panels with luminous edge lighting, blur reflections, and modern UI pills.",
        visual_identity="Frosted glass blur, luminous rim lighting (cyan/magenta), sleek pill badges, high-tech modern aesthetic.",
        typography_theme="Futuristic Ultra-Clean Sans (Inter / Space Grotesk)",
        color_palette={
            "primary": "#06B6D4",       # Electric Cyan
            "accent": "#EC4899",        # Neon Magenta
            "card_bg": "rgba(15, 23, 42, 0.75)",
            "border": "rgba(6, 182, 212, 0.4)",
            "text": "#F8FAFC",
            "shadow": "0 0 25px rgba(6, 182, 212, 0.3)"
        },
        animation_preference="glow_expand",
        badge_style="glass_pill",
        max_elements_per_minute=5,
        max_simultaneous=1,
        min_element_gap_s=3.5,
        preferred_animations=["glow_expand", "slide_fade", "optic_zoom"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "1.5",
            "shadow_blur_px": "25",
            "position": "top_center_or_right"
        },
        badge_theme_css="background:rgba(15,23,42,0.78); backdrop-filter:blur(20px); color:#38bdf8; border: 1.5px solid rgba(56,189,248,0.5); box-shadow: 0 0 20px rgba(56,189,248,0.25); border-radius: 24px;"
    ),

    "retro_camera": CreativeTemplate(
        id="retro_camera",
        name="Retro Camera",
        tagline="Viewfinder HUD, blinking REC badge, VHS digital timestamp & film borders",
        description="Vintage camcorder interface with corner viewfinder brackets, digital clock stamps, and retro camera overlays.",
        visual_identity="Camcorder viewfinder HUD, digital 7-segment/pixel font accents, red REC indicator, film framing.",
        typography_theme="Monospace / Digital Camera LCD (JetBrains Mono / Courier / Impact)",
        color_palette={
            "primary": "#EF4444",       # Recording Red
            "accent": "#F59E0B",        # Amber Warning
            "card_bg": "rgba(0, 0, 0, 0.8)",
            "border": "rgba(255, 255, 255, 0.3)",
            "text": "#FFFFFF",
            "shadow": "none"
        },
        animation_preference="retro_snap",
        badge_style="retro_hud",
        max_elements_per_minute=4,
        max_simultaneous=1,
        min_element_gap_s=4.5,
        preferred_animations=["retro_snap", "blink_in", "glitch_cut"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "2",
            "shadow_blur_px": "0",
            "position": "top_left_hud"
        },
        badge_theme_css="background:rgba(0,0,0,0.85); color:#ffffff; border: 1.5px solid rgba(255,255,255,0.4); font-family:monospace; border-radius: 4px; letter-spacing: 1px;"
    ),

    "creative_minimal": CreativeTemplate(
        id="creative_minimal",
        name="Creative Minimal",
        tagline="Deliberate restraint: 2-3 maximum high-impact highlights, clean negative space",
        description="Ultra-clean, distraction-free aesthetic with only the most essential visual callouts and clean typography.",
        visual_identity="Supreme simplicity, generous negative space, refined micro-badges, zero visual clutter.",
        typography_theme="Minimalist Modern Sans (Inter Medium / Light)",
        color_palette={
            "primary": "#FFFFFF",
            "accent": "#94A3B8",
            "card_bg": "rgba(24, 24, 27, 0.8)",
            "border": "rgba(255, 255, 255, 0.12)",
            "text": "#F4F4F5",
            "shadow": "rgba(0,0,0,0.2)"
        },
        animation_preference="minimal_fade",
        badge_style="minimal_tag",
        max_elements_per_minute=3,
        max_simultaneous=1,
        min_element_gap_s=6.0,
        preferred_animations=["minimal_fade", "subtle_slide"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "1",
            "shadow_blur_px": "10",
            "position": "top_left"
        },
        badge_theme_css="background:rgba(24,24,27,0.75); backdrop-filter:blur(12px); color:#f4f4f5; border: 1px solid rgba(255,255,255,0.15); border-radius: 12px;"
    ),

    "auto_creative": CreativeTemplate(
        id="auto_creative",
        name="Auto Creative",
        tagline="AI intelligently determines the optimal visual style from audio & frame analysis",
        description="Autonomous mode: The AI analyzes speech semantics and visual frames to dynamically select the best matching template.",
        visual_identity="Dynamic contextual adaptation based on video content.",
        typography_theme="Dynamic / Adaptive",
        color_palette={
            "primary": "#6366F1",
            "accent": "#A855F7",
            "card_bg": "rgba(15, 23, 42, 0.85)",
            "border": "rgba(99, 102, 241, 0.4)",
            "text": "#FFFFFF",
            "shadow": "rgba(0,0,0,0.3)"
        },
        animation_preference="adaptive",
        badge_style="auto",
        max_elements_per_minute=5,
        max_simultaneous=1,
        min_element_gap_s=3.5,
        preferred_animations=["pop_in", "soft_float", "glass_slide"],
        composition_rules={
            "rotation_deg": "adaptive",
            "border_width_px": "adaptive",
            "shadow_blur_px": "adaptive",
            "position": "adaptive"
        },
        badge_theme_css="background:rgba(15,23,42,0.85); backdrop-filter:blur(16px); color:#ffffff; border: 1.5px solid rgba(99,102,241,0.4); border-radius: 14px;"
    ),
}


def get_template(template_id: Optional[str]) -> CreativeTemplate:
    """Retrieve template by id, falling back to auto_creative."""
    if not template_id or template_id not in TEMPLATES:
        return TEMPLATES["auto_creative"]
    return TEMPLATES[template_id]


def list_templates() -> List[Dict]:
    """Return all templates serialized for the UI."""
    return [t.to_dict() for t in TEMPLATES.values()]
