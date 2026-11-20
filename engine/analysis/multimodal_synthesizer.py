"""
Multimodal Synthesis Engine.
Combines Audio Analysis + Visual Frame Analysis + Creative Template + Additional User Instructions
into an intelligent, context-aware editing plan with strict relevance validation and density rules.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from engine.analysis.audio_segmenter import AudioSegment
from engine.analysis.frame_analyzer import VisualFrameAnalysis
from engine.assets.registry import AssetRegistry
from engine.templates.definitions import CreativeTemplate, get_template
from engine.composer.collision_detector import SafeZoneCollisionEngine, BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class SegmentDecision:
    segment_id: str
    time_range: str
    start: float
    end: float
    spoken_topic: str
    visual_context: str
    mood: str
    needs_visual_element: bool
    clean_reason: Optional[str]
    chosen_asset_id: Optional[str]
    asset_badge_title: Optional[str]
    asset_badge_subtitle: Optional[str]
    placement: Dict[str, int]  # {'x': int, 'y': int, 'scale': float}
    duration_s: float
    animation: str
    sound_effect: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "time_range": self.time_range,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "spoken_topic": self.spoken_topic,
            "visual_context": self.visual_context,
            "mood": self.mood,
            "needs_visual_element": self.needs_visual_element,
            "clean_reason": self.clean_reason,
            "chosen_asset_id": self.chosen_asset_id,
            "asset_badge_title": self.asset_badge_title,
            "asset_badge_subtitle": self.asset_badge_subtitle,
            "placement": self.placement,
            "duration_s": round(self.duration_s, 2),
            "animation": self.animation,
            "sound_effect": self.sound_effect,
        }


def synthesize_multimodal_plan(
    audio_segments: List[AudioSegment],
    visual_frames: List[VisualFrameAnalysis],
    video_metadata: Dict[str, Any],
    template_id: str = "auto_creative",
    main_prompt: str = "",
    additional_instructions: str = "",
    asset_registry: Optional[AssetRegistry] = None,
) -> Dict[str, Any]:
    """
    Executes the multimodal reasoning loop combining audio, frames, template, and instructions.
    """
    if asset_registry is None:
        asset_registry = AssetRegistry()

    template = get_template(template_id)
    width = int(video_metadata.get("width", 1080))
    height = int(video_metadata.get("height", 1920))
    is_landscape = width > height

    # 1. Initialize SafeZoneCollisionEngine with all detected faces
    all_face_boxes = []
    for vf in visual_frames:
        if vf.faces:
            all_face_boxes.extend(vf.faces)
    collision_engine = SafeZoneCollisionEngine(canvas_w=width, canvas_h=height, face_boxes=all_face_boxes)

    # 2. Evaluate User Explicit Instructions (Priority 1)
    instr_low = (additional_instructions or "").lower()
    prompt_low = (main_prompt or "").lower()
    force_minimal = "minimal" in instr_low or template_id == "creative_minimal"
    no_stickers = "no sticker" in instr_low or "clean video" in instr_low
    avoid_face = "face" in instr_low or True  # Always avoid face by default

    # 3. Determine Auto-Creative Template if requested
    active_template = template
    auto_detected_style = None
    if template_id == "auto_creative":
        # Inspect dominant speech topic and visual aesthetics
        combined_text = " ".join([seg.text for seg in audio_segments]).lower()
        if any(w in combined_text for w in ["gemini", "code", "ai", "software", "tech", "data"]):
            active_template = get_template("glassmorphism")
            auto_detected_style = "Glassmorphism (AI & Tech detected)"
        elif any(w in combined_text for w in ["outfit", "aesthetic", "vlog", "coffee", "cozy"]):
            active_template = get_template("pinterest_scrapbook")
            auto_detected_style = "Pinterest Scrapbook (Lifestyle aesthetic detected)"
        elif any(w in combined_text for w in ["music", "track", "song", "beat", "playlist"]):
            active_template = get_template("floating_music_player")
            auto_detected_style = "Floating Music Player (Music audio detected)"
        else:
            active_template = get_template("aesthetic_lifestyle")
            auto_detected_style = "Aesthetic Lifestyle (Adaptive balance)"

    decisions: List[SegmentDecision] = []
    used_asset_ids = set()
    last_element_end = -10.0

    # Max elements calculation from template and instructions
    max_elements = active_template.max_elements_per_minute
    if force_minimal:
        max_elements = min(max_elements, 3)

    for seg in audio_segments:
        # Match the closest visual frame to this segment
        matching_frame = _find_closest_frame(seg.start, visual_frames)

        # Segment context
        topic = seg.topic_summary
        speech = seg.text
        speech_low = speech.lower()
        objects = matching_frame.objects_detected if matching_frame else []
        visual_desc = f"Activity: {matching_frame.subject_activity if matching_frame else 'speaker'} | Objects: {', '.join(objects) if objects else 'none'}"
        mood = seg.tone

        # Check spacing and density rules
        time_since_last = seg.start - last_element_end
        is_clean_scene = False
        clean_reason = None

        if no_stickers:
            is_clean_scene = True
            clean_reason = "User instruction: No stickers requested"
        elif matching_frame and matching_frame.clean_scene_recommended and not seg.is_cta:
            is_clean_scene = True
            clean_reason = "Clean scene preserved at visual transition point"
        elif time_since_last < active_template.min_element_gap_s and not seg.is_cta:
            is_clean_scene = True
            clean_reason = f"Preserving visual breathing room (gap {time_since_last:.1f}s < {active_template.min_element_gap_s}s)"
        elif len(used_asset_ids) >= max_elements and not seg.is_cta:
            is_clean_scene = True
            clean_reason = f"Template density limit reached ({len(used_asset_ids)}/{max_elements})"

        if is_clean_scene:
            decisions.append(
                SegmentDecision(
                    segment_id=seg.segment_id,
                    time_range=f"{seg.start:.1f}s - {seg.end:.1f}s",
                    start=seg.start,
                    end=seg.end,
                    spoken_topic=topic,
                    visual_context=visual_desc,
                    mood=mood,
                    needs_visual_element=False,
                    clean_reason=clean_reason,
                    chosen_asset_id=None,
                    asset_badge_title=None,
                    asset_badge_subtitle=None,
                    placement={},
                    duration_s=0.0,
                    animation="none",
                    sound_effect=None,
                )
            )
            continue

        # Select Semantically Relevant Asset
        chosen_id, badge_title, badge_sub = _select_contextual_element(
            speech_low=speech_low,
            topic=topic,
            used_assets=used_asset_ids,
            template=active_template,
            is_cta=seg.is_cta,
            asset_reg=asset_registry,
            additional_instructions=additional_instructions
        )

        if not chosen_id:
            decisions.append(
                SegmentDecision(
                    segment_id=seg.segment_id,
                    time_range=f"{seg.start:.1f}s - {seg.end:.1f}s",
                    start=seg.start,
                    end=seg.end,
                    spoken_topic=topic,
                    visual_context=visual_desc,
                    mood=mood,
                    needs_visual_element=False,
                    clean_reason="No high-confidence contextual asset required for this moment",
                    chosen_asset_id=None,
                    asset_badge_title=None,
                    asset_badge_subtitle=None,
                    placement={},
                    duration_s=0.0,
                    animation="none",
                    sound_effect=None,
                )
            )
            continue

        # Compute Non-Colliding Safe Placement using Collision Engine
        dur = min(3.2, max(2.0, seg.duration * 0.6))
        safe_coord = collision_engine.find_safe_placement(
            element_id=f"el_{seg.segment_id}_{chosen_id}",
            start_t=seg.start,
            end_t=seg.start + dur,
            width=320,
            height=80,
            preferred_side="right" if is_landscape else "auto"
        )

        if not safe_coord:
            # Collision detected against face or caption safe zones -> preserve clean footage!
            decisions.append(
                SegmentDecision(
                    segment_id=seg.segment_id,
                    time_range=f"{seg.start:.1f}s - {seg.end:.1f}s",
                    start=seg.start,
                    end=seg.end,
                    spoken_topic=topic,
                    visual_context=visual_desc,
                    mood=mood,
                    needs_visual_element=False,
                    clean_reason="Preserving clean footage: candidate placement would collide with face or captions",
                    chosen_asset_id=None,
                    asset_badge_title=None,
                    asset_badge_subtitle=None,
                    placement={},
                    duration_s=0.0,
                    animation="none",
                    sound_effect=None,
                )
            )
            continue

        placement = {"x": safe_coord[0], "y": safe_coord[1], "scale": 1.0}
        anim = active_template.preferred_animations[0] if active_template.preferred_animations else "pop_in"
        
        # Audio SFX
        sfx = "bubble_pop" if "minimal" in active_template.id else "pop"

        used_asset_ids.add(chosen_id)
        last_element_end = seg.start + dur

        decisions.append(
            SegmentDecision(
                segment_id=seg.segment_id,
                time_range=f"{seg.start:.1f}s - {seg.end:.1f}s",
                start=seg.start,
                end=seg.start + dur,
                spoken_topic=topic,
                visual_context=visual_desc,
                mood=mood,
                needs_visual_element=True,
                clean_reason=None,
                chosen_asset_id=chosen_id,
                asset_badge_title=badge_title,
                asset_badge_subtitle=badge_sub,
                placement=placement,
                duration_s=dur,
                animation=anim,
                sound_effect=sfx,
            )
        )

    # Generate Dynamic Hook Title & Grounded Social Question (NO invented handles/products)
    combined_topics = " ".join([d.spoken_topic for d in decisions])
    if "NotebookLM" in combined_topics or "Gemini" in combined_topics:
        hook_title = "⚡ GEMINI NOTEBOOKLM • AI TOOLS 🤖"
        social_q = "💬 What is your favorite feature in Google Gemini NotebookLM?"
    elif "Fashion" in combined_topics or "Lifestyle" in combined_topics or "aesthetic" in prompt_low:
        hook_title = "✨ AESTHETIC LIFESTYLE • DAILY VIBES 🌸"
        social_q = "💬 Which detail do you love most from this look?"
    elif "Recipe" in combined_topics or "Cooking" in combined_topics:
        hook_title = "🍲 MASTER RECIPE • QUICK PREP 👨‍🍳"
        social_q = "💬 Have you tried cooking this dish before?"
    else:
        hook_title = "✨ CREATIVE HIGHLIGHTS • AI STUDIO 🚀"
        social_q = "💬 What are your thoughts? Drop a comment below!"

    return {
        "applied_template": active_template.to_dict(),
        "auto_detected_style": auto_detected_style,
        "hook_title": hook_title,
        "social_question": social_q,
        "decisions": [d.to_dict() for d in decisions],
        "total_segments": len(audio_segments),
        "visual_elements_placed": len(used_asset_ids),
        "clean_segments_preserved": sum(1 for d in decisions if not d.needs_visual_element),
    }


def _find_closest_frame(timestamp: float, frames: List[VisualFrameAnalysis]) -> Optional[VisualFrameAnalysis]:
    if not frames:
        return None
    return min(frames, key=lambda f: abs(f.timestamp - timestamp))


def _select_contextual_element(
    speech_low: str,
    topic: str,
    used_assets: set,
    template: CreativeTemplate,
    is_cta: bool,
    asset_reg: AssetRegistry,
    additional_instructions: str = ""
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Selects a semantically relevant asset matching speech topic and template."""
    candidates = []

    # 1. CTA check
    if is_cta:
        if "like" in speech_low or "follow" in speech_low:
            candidates.append(("heart", "LIKE & FOLLOW", "Tap the heart for more!"))
        if "comment" in speech_low or "reply" in speech_low or "tell" in speech_low:
            candidates.append(("comment", "COMMENT BELOW", "Share your thoughts!"))

    # 2. Tech / Gemini / Education checks
    if any(k in speech_low for k in ["gemini", "notebooklm", "notebook alum", "google ai"]):
        candidates.append(("gemini", "GEMINI NOTEBOOKLM", "Smart AI Assistant"))
    if any(k in speech_low for k in ["exam", "exams", "study", "research", "learn", "lesson"]):
        candidates.append(("book", "EXAMS & STUDY", "Research & Preparation"))
    if any(k in speech_low for k in ["mcq", "mcqs", "quiz", "questions"]):
        candidates.append(("quiz", "GENERATE MCQS", "Instant Quiz Prep"))
    if any(k in speech_low for k in ["ppt", "presentation", "slides"]):
        candidates.append(("presentation", "CREATE PPT", "Automated Slide Decks"))
    if any(k in speech_low for k in ["audio", "podcast", "conversation", "listen"]):
        candidates.append(("audio_mic", "AUDIO PODCAST", "Two-Way Conversation"))
    if any(k in speech_low for k in ["laptop", "computer", "software", "tool"]):
        candidates.append(("laptop", "DESKTOP STUDIO", "Web App Workflow"))

    # 3. Lifestyle / Aesthetic checks
    if any(k in speech_low for k in ["outfit", "style", "dress", "fashion", "aesthetic"]):
        candidates.append(("polaroid_frame", "DAILY OOTD", "Aesthetic Look"))
        candidates.append(("flower_blossom", "FLORAL ACCENT", "Dreamy Mood"))
    if any(k in speech_low for k in ["food", "recipe", "cook", "dish", "meal"]):
        candidates.append(("recipe_dish", "CHEF SPECIAL", "Quick Recipe"))
        candidates.append(("chef_hat", "CULINARY TIP", "Chef Technique"))

    # Filter out already used assets to avoid repetition
    for asset_id, title, sub in candidates:
        if asset_id not in used_assets:
            # Validate relevance
            val = asset_reg.validate_asset_relevance(
                asset_id=asset_id,
                topic=topic,
                scene_visuals=speech_low,
                template_id=template.id,
                additional_instructions=additional_instructions
            )
            if val.get("relevant", False):
                return asset_id, title, sub

    return None, None, None


def _calculate_safe_placement(
    matching_frame: Optional[VisualFrameAnalysis],
    canvas_w: int,
    canvas_h: int,
    is_landscape: bool
) -> Dict[str, Any]:
    """
    Calculates (x, y) coordinates ensuring the graphic DOES NOT cover faces
    or bottom caption areas.
    """
    scale = 1.0

    if is_landscape:
        # 16:9 Landscape (e.g. 1920x1080 or 848x474)
        # Default top-right quadrant safe zone
        safe_x = int(canvas_w * 0.65)
        safe_y = int(canvas_h * 0.15)

        # Check if face is in top-right
        if matching_frame and matching_frame.faces:
            face = matching_frame.faces[0]
            face_center_x = face["x"] + face["w"] / 2
            # If face is on right half, move badge to top-left
            if face_center_x > canvas_w * 0.5:
                safe_x = int(canvas_w * 0.08)
                safe_y = int(canvas_h * 0.15)
    else:
        # 9:16 Vertical Reel (e.g. 1080x1920)
        # Default top-right floating badge
        safe_x = int(canvas_w * 0.55)
        safe_y = int(canvas_h * 0.18)

        # Check face position
        if matching_frame and matching_frame.faces:
            face = matching_frame.faces[0]
            face_center_x = face["x"] + face["w"] / 2
            face_top_y = face["y"]
            # If face is centered/high, position above face or top-left
            if face_center_x > canvas_w * 0.4:
                safe_x = int(canvas_w * 0.08)
            if face_top_y < canvas_h * 0.25:
                safe_y = int(canvas_h * 0.08)

    return {"x": safe_x, "y": safe_y, "scale": scale}
