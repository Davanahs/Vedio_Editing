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
from typing import Dict, List, Optional, Set, Any


@dataclass
class CreativeTemplate:
    id: str
    name: str
    description: str
    tagline: str
    preview_image: str
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
    creative_spec: Dict[str, Any]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tagline": self.tagline,
            "preview_image": self.preview_image,
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
            "creative_spec": self.creative_spec,
        }


TEMPLATES: Dict[str, CreativeTemplate] = {
    "pinterest_scrapbook": CreativeTemplate(
        id="pinterest_scrapbook",
        name="Pinterest Scrapbook",
        tagline="Handcrafted Polaroid frames, doodles, soft shadows & layered depth",
        description="Scrapbook collage aesthetic with tilted Polaroid frames, white paper borders, stars, flowers, and handwritten accents.",
        preview_image="/template_previews/pinterest_scrapbook.jpg",
        visual_identity="Layered polaroids, hand-drawn paper cutouts, soft organic shadows, warm nostalgic charm.",
        typography_theme="Playful Sans & Script accents (Inter Bold + Kalam/Caveat feel)",
        color_palette={
            "primary": "#FFE4E6",       # Soft warm blush
            "accent": "#F43F5E",        # Rose red
            "card_bg": "rgba(255, 255, 255, 0.96)",
            "border": "#FFFFFF",
            "text": "#1E293B",
            "shadow": "rgba(0,0,0,0.3)"
        },
        animation_preference="tilt_pop",
        badge_style="polaroid",
        max_elements_per_minute=5,
        max_simultaneous=1,
        min_element_gap_s=3.5,
        preferred_animations=["tilt_pop", "paper_drop", "soft_bounce"],
        composition_rules={
            "rotation_deg": "-3 to 4",
            "border_width_px": "8",
            "shadow_blur_px": "18",
            "position": "safe_quadrant_opposite_face"
        },
        badge_theme_css="background:#ffffff; color:#18181b; border: 4px solid #ffffff; box-shadow: 0 12px 28px rgba(0,0,0,0.3); border-radius: 8px; transform: rotate(-2deg);",
        creative_spec={
            "element_types": ["Polaroid frame cards", "White subject outlines", "Hand-drawn stars", "Floral doodle accents", "Washi tape stickers"],
            "composition_style": "Layered collage with subtle 2 to 4 degree tilt, paper drop shadow, safe corner positioning",
            "animation_behaviour": "Physical paper spring drop in, gentle floating idle, soft pop exit",
            "layering": "Subject cutout in front, polaroid frame behind or beside, doodle accents on outer rim",
            "visual_density": "Maximum 1 active card, minimum 3.5s spacing between appearances",
            "adaptive_rule": "Adapts graphic content to video subject (e.g. tech tutorial shows tech cards in Polaroid frames, NOT makeup/fashion)"
        }
    ),

    "aesthetic_lifestyle": CreativeTemplate(
        id="aesthetic_lifestyle",
        name="Aesthetic Lifestyle",
        tagline="Gentle pastels, clean floating highlights & serene typography",
        description="Clean, chic, pastel aesthetic with minimal organic stickers, elegant typography, and serene pacing.",
        preview_image="/template_previews/aesthetic_lifestyle.jpg",
        visual_identity="Pastel tones, floating photographs, soft organic curves, warm sunlight feeling, clean negative space.",
        typography_theme="Modern Editorial Sans (Inter Regular + SemiBold)",
        color_palette={
            "primary": "#FEF3C7",       # Soft pastel amber
            "accent": "#EC4899",        # Soft pink
            "card_bg": "rgba(255, 255, 255, 0.90)",
            "border": "rgba(255, 255, 255, 0.6)",
            "text": "#0F172A",
            "shadow": "rgba(0,0,0,0.15)"
        },
        animation_preference="soft_float",
        badge_style="minimal_tag",
        max_elements_per_minute=4,
        max_simultaneous=1,
        min_element_gap_s=4.5,
        preferred_animations=["soft_float", "fade_up", "gentle_scale"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "2",
            "shadow_blur_px": "14",
            "position": "top_left_or_pill"
        },
        badge_theme_css="background:rgba(255,255,255,0.92); color:#1e293b; border: 1.5px solid rgba(226,232,240,0.8); box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 20px;",
        creative_spec={
            "element_types": ["Floating clean photo panels", "Chic pastel badges", "Subtle organic sparkles", "Editorial lower thirds"],
            "composition_style": "Generous negative space, perfectly aligned margins, soft ambient shadows",
            "animation_behaviour": "Silky smooth fade up with 0.8s ease, gentle breathing float",
            "layering": "Clean overlays tucked into upper safe margins, never crowding center",
            "visual_density": "Deliberately uncrowded (3-4 elements per minute)",
            "adaptive_rule": "Emphasizes beauty, lifestyle, coffee, or aesthetic workflow moments cleanly"
        }
    ),

    "floating_music_player": CreativeTemplate(
        id="floating_music_player",
        name="Floating Music Player",
        tagline="Streaming UI cards, track scrub bars & perspective ground panels",
        description="Music-streaming inspired UI with floating playback cards, scrub waveforms, perspective tilt, and audio mood.",
        preview_image="/template_previews/floating_music_player.jpg",
        visual_identity="Floating playback UI, album art thumbnails, scrubbing waveforms, sleek dark glass, streaming vibes.",
        typography_theme="Clean Geometric Sans (Circular / Inter Bold)",
        color_palette={
            "primary": "#1DB954",       # Spotify green
            "accent": "#38BDF8",        # Electric cyan
            "card_bg": "rgba(18, 18, 18, 0.88)",
            "border": "rgba(255, 255, 255, 0.18)",
            "text": "#FFFFFF",
            "shadow": "rgba(0,0,0,0.55)"
        },
        animation_preference="glass_slide",
        badge_style="music_player",
        max_elements_per_minute=4,
        max_simultaneous=1,
        min_element_gap_s=4.5,
        preferred_animations=["glass_slide", "pulse_wave", "smooth_in"],
        composition_rules={
            "rotation_deg": "0 to 2",
            "border_width_px": "1",
            "shadow_blur_px": "24",
            "position": "bottom_or_floating_side"
        },
        badge_theme_css="background:rgba(18,18,18,0.88); backdrop-filter:blur(16px); color:#ffffff; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 16px 36px rgba(0,0,0,0.5); border-radius: 16px;",
        creative_spec={
            "element_types": ["Now Playing card", "Audio scrub bar", "Soundwave visualizer", "Album thumbnail"],
            "composition_style": "Perspective floating card positioned at safe margin with realistic ground drop shadow",
            "animation_behaviour": "Smooth slide in from side, pulse on music beats, slide out",
            "layering": "Layered over background video, strictly avoiding presenter face and main captions",
            "visual_density": "Shown only during key musical or audio listening segments",
            "adaptive_rule": "STRICT CONSTRAINT: ONLY used when video is about music/audio or user explicitly requests music theme"
        }
    ),

    "glassmorphism": CreativeTemplate(
        id="glassmorphism",
        name="Glassmorphism",
        tagline="Translucent frosted glass, subtle cyan & pink glowing borders",
        description="Futuristic frosted-glass panels with luminous edge lighting, blur reflections, and modern UI pills.",
        preview_image="/template_previews/glassmorphism.jpg",
        visual_identity="Frosted glass blur, luminous rim lighting (cyan/magenta), sleek pill badges, high-tech modern aesthetic.",
        typography_theme="Futuristic Ultra-Clean Sans (Inter / Space Grotesk)",
        color_palette={
            "primary": "#06B6D4",       # Electric Cyan
            "accent": "#EC4899",        # Neon Magenta
            "card_bg": "rgba(15, 23, 42, 0.78)",
            "border": "rgba(6, 182, 212, 0.45)",
            "text": "#F8FAFC",
            "shadow": "0 0 25px rgba(6, 182, 212, 0.3)"
        },
        animation_preference="glow_expand",
        badge_style="glass_pill",
        max_elements_per_minute=4,
        max_simultaneous=1,
        min_element_gap_s=4.0,
        preferred_animations=["glow_expand", "slide_fade", "optic_zoom"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "1.5",
            "shadow_blur_px": "25",
            "position": "safe_upper_quadrant"
        },
        badge_theme_css="background:rgba(15,23,42,0.78); backdrop-filter:blur(20px); color:#38bdf8; border: 1.5px solid rgba(56,189,248,0.5); box-shadow: 0 0 20px rgba(56,189,248,0.25); border-radius: 24px;",
        creative_spec={
            "element_types": ["Translucent frosted cards", "Cyan/pink neon border pills", "Subtle light trail accents", "Modern UI HUD elements"],
            "composition_style": "Floating glass cards placed in safe corners opposite the presenter's face",
            "animation_behaviour": "Luminous glow expansion on reveal, soft backdrop blur transition",
            "layering": "Translucent glass allows background footage to show through with optical blur",
            "visual_density": "Maximum 4 highlights per minute to maintain cutting-edge tech clarity",
            "adaptive_rule": "Ideal for AI tools, developer tutorials, product walkthroughs, and modern showcases"
        }
    ),

    "retro_camera": CreativeTemplate(
        id="retro_camera",
        name="Retro Camera",
        tagline="Viewfinder HUD, blinking REC badge, VHS digital timestamp & film borders",
        description="Vintage camcorder interface with corner viewfinder brackets, digital clock stamps, and retro camera overlays.",
        preview_image="/template_previews/retro_camera.jpg",
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
        max_elements_per_minute=3,
        max_simultaneous=1,
        min_element_gap_s=5.0,
        preferred_animations=["retro_snap", "blink_in", "glitch_cut"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "2",
            "shadow_blur_px": "0",
            "position": "top_left_hud"
        },
        badge_theme_css="background:rgba(0,0,0,0.85); color:#ffffff; border: 1.5px solid rgba(255,255,255,0.4); font-family:monospace; border-radius: 4px; letter-spacing: 1px;",
        creative_spec={
            "element_types": ["Viewfinder corner brackets [ ]", "Blinking red REC indicator", "Digital timecode stamp", "Camcorder battery status"],
            "composition_style": "Corner HUD overlay framing the subject without obstruction",
            "animation_behaviour": "Sharp snap in, blinking red dot indicator, retro camera shutter effect",
            "layering": "HUD framing elements along borders, leaving center 80% completely clear",
            "visual_density": "Minimal framing HUD with 2-3 key temporal callouts",
            "adaptive_rule": "Adds vintage vlog or indie film camera feel to any footage"
        }
    ),

    "creative_minimal": CreativeTemplate(
        id="creative_minimal",
        name="Creative Minimal",
        tagline="Deliberate restraint: 2-3 maximum high-impact highlights, clean negative space",
        description="Ultra-clean, distraction-free aesthetic with only the most essential visual callouts and clean typography.",
        preview_image="/template_previews/creative_minimal.jpg",
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
        max_elements_per_minute=2,
        max_simultaneous=1,
        min_element_gap_s=7.0,
        preferred_animations=["minimal_fade", "subtle_slide"],
        composition_rules={
            "rotation_deg": "0",
            "border_width_px": "1",
            "shadow_blur_px": "10",
            "position": "top_left"
        },
        badge_theme_css="background:rgba(24,24,27,0.75); backdrop-filter:blur(12px); color:#f4f4f5; border: 1px solid rgba(255,255,255,0.15); border-radius: 12px;",
        creative_spec={
            "element_types": ["Micro highlight pill", "Refined keyword emphasis", "Single line kinetic underline"],
            "composition_style": "Generous negative space, maximum focus on presenter and dialogue",
            "animation_behaviour": "Subtle 0.4s dissolve fade, gentle micro-slide",
            "layering": "Understated corner placement, zero interference with captions or face",
            "visual_density": "Maximum 2-3 elements across the ENTIRE video; clean footage is prioritized",
            "adaptive_rule": "Enforces strict minimalism: removes all decorative stickers and flashy cards"
        }
    ),

    "auto_creative": CreativeTemplate(
        id="auto_creative",
        name="Auto Creative (AI Decides)",
        tagline="AI intelligently determines the optimal visual style from audio & frame analysis",
        description="Autonomous mode: The AI analyzes speech semantics and visual frames to dynamically select the best matching template.",
        preview_image="/template_previews/auto_creative.jpg",
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
        max_elements_per_minute=4,
        max_simultaneous=1,
        min_element_gap_s=4.0,
        preferred_animations=["pop_in", "soft_float", "glass_slide"],
        composition_rules={
            "rotation_deg": "adaptive",
            "border_width_px": "adaptive",
            "shadow_blur_px": "adaptive",
            "position": "adaptive"
        },
        badge_theme_css="background:rgba(15,23,42,0.85); backdrop-filter:blur(16px); color:#ffffff; border: 1.5px solid rgba(99,102,241,0.4); border-radius: 14px;",
        creative_spec={
            "element_types": ["Dynamically selected from verified relevant asset catalog"],
            "composition_style": "Adaptive balance matching content genre (tech -> glassmorphism, lifestyle -> scrapbook)",
            "animation_behaviour": "Coordinated with speech cadence and music energy",
            "layering": "Full collision detection against faces and captions",
            "visual_density": "Balanced (3-4 elements per minute, respecting clean pauses)",
            "adaptive_rule": "Detects video topic and visual aesthetic automatically"
        }
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
