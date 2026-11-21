"""
Multimodal Synthesis Engine.
Combines Audio Analysis + Visual Frame Analysis + Creative Template + Additional User Instructions
into an intelligent, context-aware editing plan with strict relevance validation and density rules.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from engine.analysis.audio_segmenter import AudioSegment
from engine.analysis.frame_analyzer import VisualFrameAnalysis
from engine.assets.registry import AssetRegistry
from engine.assets.semantic_ranker import score_asset_descriptions
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
    placement: Dict[str, Any]  # output-canvas bounds, rotation, and layer
    duration_s: float
    animation: str
    sound_effect: Optional[str]
    selection_score: float = 0.0
    selection_evidence: Dict[str, Any] = field(default_factory=dict)
    composition_layers: List[Dict[str, Any]] = field(default_factory=list)

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
            "selection_score": round(self.selection_score, 3),
            "selection_evidence": self.selection_evidence,
            "composition_layers": self.composition_layers,
        }


def synthesize_multimodal_plan(
    audio_segments: List[AudioSegment],
    visual_frames: List[VisualFrameAnalysis],
    video_metadata: Dict[str, Any],
    template_id: str = "auto_creative",
    main_prompt: str = "",
    additional_instructions: str = "",
    asset_registry: Optional[AssetRegistry] = None,
    available_resources: Optional[List[str]] = None,
    resource_evidence: Optional[List[Dict[str, Any]]] = None,
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
            scale_x = width / max(1, vf.width)
            scale_y = height / max(1, vf.height)
            all_face_boxes.extend({
                **face,
                "x": round(face.get("x", 0) * scale_x),
                "y": round(face.get("y", 0) * scale_y),
                "w": round(face.get("w", 0) * scale_x),
                "h": round(face.get("h", 0) * scale_y),
                "timestamp": vf.timestamp,
                "start": max(0.0, vf.timestamp - 3.0),
                "end": vf.timestamp + 3.0,
            } for face in vf.faces)
    collision_engine = SafeZoneCollisionEngine(canvas_w=width, canvas_h=height, face_boxes=all_face_boxes)

    # 2. Evaluate User Explicit Instructions (Priority 1)
    selection_instructions = " ".join(part.strip() for part in [main_prompt or "", additional_instructions or ""] if part.strip())
    instr_low = selection_instructions.lower()
    prompt_low = (main_prompt or "").lower()
    resource_names = " ".join(
        str(resource).replace("_", " ").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        for resource in (available_resources or [])
    )
    resource_text = " ".join(str(item.get("evidence", "")) for item in (resource_evidence or []))
    resource_context = " ".join(part for part in (resource_names, resource_text) if part).strip()
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
    asset_history: list[str] = []
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
        visual_desc = " | ".join(part for part in [
            matching_frame.visual_summary if matching_frame else "",
            f"Activity: {matching_frame.subject_activity if matching_frame else 'speaker'}",
            f"Setting: {matching_frame.setting_environment}" if matching_frame else "",
            f"Objects: {', '.join(objects)}" if objects else "",
        ] if part)
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
        composition_state = {
            "placed_count": len(used_asset_ids),
            "recent_asset_ids": asset_history[-4:],
            "recent_categories": [
                (asset_registry.get_asset_metadata(asset_id) or {}).get("category", "")
                for asset_id in asset_history[-4:]
            ],
            "last_element_end": round(last_element_end, 2),
            "template_density_limit": max_elements,
        }
        chosen_id, badge_title, badge_sub, selection_ranking = _select_contextual_element(
            speech_low=speech_low,
            topic=topic,
            used_assets=used_asset_ids,
            template=active_template,
            is_cta=seg.is_cta,
            asset_reg=asset_registry,
            additional_instructions=selection_instructions,
            scene_context=visual_desc,
            resource_context=resource_context,
            composition_state=composition_state,
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
        element_width, element_height = _asset_composition_size(chosen_id, asset_registry, width, height)
        visible_faces = matching_frame.faces if matching_frame else []
        face_on_right = any(face.get("x", 0) + face.get("w", 0) / 2 > (matching_frame.width if matching_frame else width) * 0.5 for face in visible_faces)
        preferred_side = "left" if face_on_right else "right" if visible_faces else _template_preferred_side(active_template.id)
        safe_coord = collision_engine.find_safe_placement(
            element_id=f"el_{seg.segment_id}_{chosen_id}",
            start_t=seg.start,
            end_t=seg.start + dur,
            width=element_width,
            height=element_height,
            preferred_side=preferred_side,
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

        placement = {
            "x": safe_coord[0], "y": safe_coord[1], "scale": 1.0,
            "width": element_width, "height": element_height,
            "rotation": _template_rotation(active_template.id, chosen_id),
            "z_index": 50,
        }
        composition_layers = _build_composition_layers(
            active_template.id, chosen_id, placement, width, height,
            topic, visual_desc, selection_instructions, asset_registry,
        )
        anim = active_template.preferred_animations[0] if active_template.preferred_animations else "pop_in"
        selection_evidence = _selection_evidence(
            chosen_id, speech, topic, visual_desc, active_template.id, asset_registry,
            resource_context, selection_ranking, composition_state,
        )
        selection_evidence["composition_layer_count"] = len(composition_layers)
        
        # Audio SFX
        sfx = "bubble_pop" if "minimal" in active_template.id else "pop"

        used_asset_ids.add(chosen_id)
        asset_history.append(chosen_id)
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
                selection_score=selection_evidence["score"],
                selection_evidence=selection_evidence,
                composition_layers=composition_layers,
            )
        )

    # Generate Dynamic Hook Title & Grounded Social Question (NO invented handles/products)
    combined_topics_low = (" ".join([d.spoken_topic for d in decisions]) + " " + " ".join([seg.text for seg in audio_segments])).lower()
    if any(k in combined_topics_low for k in ["gta", "gts", "gta6", "gts6", "gaming", "game", "clipping", "clips", "earn money"]):
        hook_title = "⚡ GTA 6 CLIPS • EARN MONEY 💰"
        social_q = "💬 What clipping platform do you use to monetize videos?"
    elif any(k in combined_topics_low for k in ["notebooklm", "notebook alum", "gemini"]):
        hook_title = "⚡ GEMINI NOTEBOOKLM • AI TOOLS 🤖"
        social_q = "💬 What is your favorite feature in Google Gemini NotebookLM?"
    elif any(k in combined_topics_low for k in ["fashion", "lifestyle", "outfit", "aesthetic"]):
        hook_title = "✨ AESTHETIC LIFESTYLE • DAILY VIBES 🌸"
        social_q = "💬 Which detail do you love most from this look?"
    elif any(k in combined_topics_low for k in ["recipe", "cooking", "food", "dish"]):
        hook_title = "🍲 MASTER RECIPE • QUICK PREP 👨‍🍳"
        social_q = "💬 Have you tried cooking this dish before?"
    else:
        hook_title = "✨ CREATIVE HIGHLIGHTS • AI STUDIO 🚀"
        social_q = "💬 What are your thoughts? Drop a comment below!"

    topic_parts = [decision.spoken_topic.strip() for decision in decisions if decision.spoken_topic.strip()]
    title_source = topic_parts[0] if topic_parts else (audio_segments[0].text.strip() if audio_segments else "")
    hook_title = re.sub(r"\s+", " ", title_source).strip(" .,!?:;")[:64].upper()
    social_q = "What stood out to you in this video?"

    # Dynamic Visual FX intent detection (Disco Ball & Lights, Kinetic Lines, Glitter Sparkles)
    dynamic_vfx = None
    prompt_combo = f"{main_prompt} {additional_instructions} {combined_topics_low}".lower()
    if any(k in prompt_combo for k in ["disco", "party", "club", "dance", "nightclub", "dj", "celebrat"]):
        dynamic_vfx = "disco_ball_lights"
    elif any(k in prompt_combo for k in ["glitter", "sparkle", "stars", "twinkle", "shimmer", "magic"]):
        dynamic_vfx = "glitter_sparkle"
    elif any(k in prompt_combo for k in ["lines", "speed", "kinetic", "fast", "trail", "pulse", "action"]):
        dynamic_vfx = "kinetic_lines"
    elif active_template.id == "pinterest_scrapbook":
        dynamic_vfx = "glitter_sparkle"
    elif active_template.id == "glassmorphism":
        dynamic_vfx = "kinetic_lines"

    return {
        "applied_template": active_template.to_dict(),
        "auto_detected_style": auto_detected_style,
        "hook_title": hook_title,
        "social_question": social_q,
        "dynamic_vfx": dynamic_vfx,
        "decisions": [d.to_dict() for d in decisions],
        "resource_evidence": resource_evidence or [],
        "asset_ranking_method": "offline semantic embeddings with relevance validation and local lexical fallback",
        "total_segments": len(audio_segments),
        "visual_elements_placed": len(used_asset_ids),
        "clean_segments_preserved": sum(1 for d in decisions if not d.needs_visual_element),
    }


def _find_closest_frame(timestamp: float, frames: List[VisualFrameAnalysis]) -> Optional[VisualFrameAnalysis]:
    if not frames:
        return None
    return min(frames, key=lambda f: abs(f.timestamp - timestamp))


def _asset_composition_size(asset_id: str, registry: AssetRegistry, canvas_w: int, canvas_h: int) -> tuple[int, int]:
    """Choose a readable, asset-aware footprint in the output coordinate plane."""
    metadata = registry.get_asset_metadata(asset_id) or {}
    category = metadata.get("category", "")
    if asset_id in {"polaroid_frame", "torn_paper_frame"}:
        base = (280, 340)
    elif asset_id in {"music_player_card", "tech_interface_card", "glass_pill"}:
        base = (360, 190)
    elif asset_id in {"retro_camera_overlay", "film_frame", "viewfinder"}:
        base = (360, 220)
    elif category in {"scrapbook_decorative", "music_audio", "ai_technology"}:
        base = (220, 180)
    else:
        base = (180, 180)
    # Preserve a familiar visual scale across the supported 9:16, 16:9 and 1:1 canvases.
    scale = min(canvas_w / 1080, canvas_h / 1080, 1.0)
    return max(72, round(base[0] * scale)), max(72, round(base[1] * scale))


def _template_preferred_side(template_id: str) -> str:
    return {
        "pinterest_scrapbook": "left",
        "aesthetic_lifestyle": "left",
        "floating_music_player": "right",
        "glassmorphism": "right",
        "retro_camera": "left",
        "creative_minimal": "left",
    }.get(template_id, "auto")


def _template_rotation(template_id: str, asset_id: str) -> float:
    if template_id != "pinterest_scrapbook":
        return 0.0
    # A repeatable, restrained tilt gives paper elements hierarchy without jitter.
    return -3.0 if sum(asset_id.encode("utf-8")) % 2 else 3.0


def _build_composition_layers(
    template_id: str,
    primary_asset: str,
    placement: Dict[str, Any],
    canvas_w: int,
    canvas_h: int,
    topic: str,
    scene_context: str,
    instructions: str,
    registry: AssetRegistry,
) -> List[Dict[str, Any]]:
    """Add one intentional template accent as a grouped, higher layer."""
    template_accents = {
        "pinterest_scrapbook": ("sparkle_stars" if primary_asset == "scrapbook_tape" else "scrapbook_tape"),
        "glassmorphism": "glass_pill",
        "retro_camera": "viewfinder",
        "aesthetic_lifestyle": "sparkle_stars",
        "floating_music_player": "sound_wave",
    }
    accent_id = template_accents.get(template_id)
    if not accent_id or accent_id == primary_asset:
        return []
    primary_meta = registry.get_asset_metadata(primary_asset) or {}
    primary_category = primary_meta.get("category", "")
    if template_id == "aesthetic_lifestyle" and primary_category not in {"fashion_lifestyle", "scrapbook_decorative"}:
        return []
    if template_id == "floating_music_player" and primary_category != "music_audio":
        return []
    validation = registry.validate_asset_relevance(
        accent_id,
        topic=topic,
        scene_visuals=scene_context,
        template_id=template_id,
        additional_instructions=instructions,
    )
    if not validation.get("relevant"):
        return []
    width, height = (104, 64) if accent_id == "scrapbook_tape" else (96, 96)
    x = min(max(0, int(placement["x"] + placement["width"] - 72)), max(0, canvas_w - width))
    y = min(max(0, int(placement["y"] + 10)), max(0, canvas_h - height))
    return [{
        "asset_id": accent_id,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "z_index": 60,
        "rotation": -2.0 if template_id == "pinterest_scrapbook" else 0.0,
        "animation": "pop_fade",
        "reason": f"{template_id} accent layered over the primary, topic-relevant element",
    }]


def _selection_evidence(
    asset_id: str,
    speech: str,
    topic: str,
    scene_context: str,
    template_id: str,
    asset_registry: AssetRegistry,
    resource_context: str = "",
    ranking: Optional[Dict[str, Any]] = None,
    composition_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = asset_registry.get_asset_metadata(asset_id) or {}
    source = f"{speech} {topic} {scene_context} {resource_context}".lower()
    matched = [
        keyword for keyword in metadata.get("keywords", [])
        if re.search(r"\b" + re.escape(keyword.lower()) + r"\b", source)
    ]
    style_fit = {
        "pinterest_scrapbook": {"scrapbook", "pastel"},
        "aesthetic_lifestyle": {"scrapbook", "pastel", "warm"},
        "floating_music_player": {"glass_music"},
        "glassmorphism": {"glass", "tech"},
        "retro_camera": {"retro"},
        "creative_minimal": {"clean"},
    }.get(template_id, set())
    fits_template = metadata.get("style") in style_fit
    score = float((ranking or {}).get("final_score", min(0.95, 0.55 + min(0.3, len(matched) * 0.08) + (0.1 if fits_template else 0.0))))
    return {
        "score": round(score, 3),
        "matched_keywords": matched,
        "template_style_match": fits_template,
        "visual_evidence": scene_context[:240],
        "resource_name_evidence": resource_context[:240],
        "semantic_similarity": round(float((ranking or {}).get("semantic_similarity", 0.0)), 3),
        "ranking_method": (ranking or {}).get("ranking_method", "local_keyword_fallback"),
        "matched_resource_terms": (ranking or {}).get("matched_resource_terms", [])[:8],
        "composition_context": composition_state or {},
    }


def _select_contextual_element(
    speech_low: str,
    topic: str,
    used_assets: set,
    template: CreativeTemplate,
    is_cta: bool,
    asset_reg: AssetRegistry,
    additional_instructions: str = "",
    scene_context: str = "",
    resource_context: str = "",
    composition_state: Optional[Dict[str, Any]] = None,
) -> tuple[Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
    """Selects a semantically relevant asset matching speech topic and template."""
    candidates = []
    evidence_low = f"{speech_low} {topic or ''} {scene_context or ''} {additional_instructions or ''} {resource_context or ''}".lower()

    # 1. CTA check
    if is_cta:
        if "like" in speech_low or "follow" in speech_low:
            candidates.append(("heart", "LIKE & FOLLOW", "Tap the heart for more!"))
        if "comment" in speech_low or "reply" in speech_low or "tell" in speech_low or "link" in speech_low:
            candidates.append(("comment", "COMMENT FOR LINK", "Get the Platform Link"))

    # 2. Gaming / GTA / Clipping / Monetization checks
    if any(k in evidence_low for k in ["gta", "gts", "game", "gaming", "gamer", "stream", "play"]):
        candidates.append(("gamepad", "GAMEPLAY", "Gaming"))
    if any(k in evidence_low for k in ["money", "earn", "cash", "views", "monetize", "revenue", "income", "paid"]):
        candidates.append(("money", "MONETIZATION", "Revenue"))
    if any(k in evidence_low for k in ["youtube", "yt", "link", "video link", "copy"]):
        candidates.append(("youtube", "YOUTUBE CLIPS", "Automated Clip Creator"))
    if any(k in evidence_low for k in ["clip", "clipping", "platform", "creator", "content creator"]):
        candidates.append(("chip", "SMART CLIPPING", "Instant Viral Highlights"))

    # 3. Tech / Gemini / Education checks
    if any(k in evidence_low for k in ["gemini", "notebooklm", "notebook alum", "google ai"]):
        candidates.append(("gemini", "AI TOOL", "Artificial intelligence"))
    if any(k in evidence_low for k in ["exam", "exams", "research", "interview", "test"]) or ("academic" in topic.lower() and any(k in evidence_low for k in ["study", "learn"])):
        candidates.append(("book", "EXAMS & STUDY", "Research & Preparation"))
    if any(k in evidence_low for k in ["mcq", "mcqs", "quiz", "questions"]):
        candidates.append(("quiz", "GENERATE MCQS", "Instant Quiz Prep"))
    if any(k in evidence_low for k in ["ppt", "presentation", "slides"]):
        candidates.append(("presentation", "CREATE PPT", "Automated Slide Decks"))
    if any(k in evidence_low for k in ["audio", "podcast", "conversation", "listen"]):
        candidates.append(("audio_mic", "AUDIO PODCAST", "Two-Way Conversation"))
    if any(k in evidence_low for k in ["laptop", "computer", "software", "tool"]):
        candidates.append(("laptop", "DESKTOP STUDIO", "Web App Workflow"))

    # 4. Lifestyle / Aesthetic checks
    if any(k in evidence_low for k in ["outfit", "style", "dress", "fashion", "aesthetic", "flower", "garden"]):
        candidates.append(("polaroid_frame", "DAILY OOTD", "Aesthetic Look"))
        candidates.append(("flower_blossom", "FLORAL ACCENT", "Dreamy Mood"))
    if any(k in evidence_low for k in ["food", "recipe", "cook", "dish", "meal", "kitchen", "ingredient"]):
        candidates.append(("recipe_dish", "CHEF SPECIAL", "Quick Recipe"))
        candidates.append(("chef_hat", "CULINARY TIP", "Chef Technique"))
    if any(k in evidence_low for k in ["music", "song", "track", "playlist", "podcast"]):
        candidates.append(("music_player_card", "NOW PLAYING", "Audio segment"))
    if template.id == "retro_camera" and any(k in evidence_low for k in ["camera", "recording", "film", "camcorder", "vlog"]):
        candidates.append(("retro_recording_hud", "REC", "Camera overlay"))
    if template.id == "pinterest_scrapbook" and any(k in evidence_low for k in ["photo", "paper", "memory", "scrapbook", "travel"]):
        candidates.append(("scrapbook_tape", "PAPER LAYER", "Scrapbook detail"))
        candidates.append(("torn_paper_frame", "PHOTO FRAME", "Paper collage"))
    if template.id == "pinterest_scrapbook" and any(k in evidence_low for k in ["portrait", "subject", "outline", "fashion", "outfit"]):
        candidates.append(("subject_outline", "PORTRAIT DETAIL", "Hand-drawn outline accent"))
    if any(k in evidence_low for k in ["point", "focus", "look here", "highlight this"]):
        candidates.append(("doodle_arrow", "LOOK HERE", "Visual pointer"))
    if any(k in evidence_low for k in ["headline", "title card", "key point", "takeaway", "main idea"]):
        candidates.append(("kinetic_title_card", "KEY TAKEAWAY", "Title plate"))
    if template.id == "retro_camera" and any(k in evidence_low for k in ["film", "cinema", "movie"]):
        candidates.append(("film_frame", "FILM FRAME", "Cinematic border"))
    if any(k in evidence_low for k in ["ai", "code", "software", "technology", "interface", "data", "developer"]):
        candidates.append(("tech_interface_card", "TECH DETAIL", "Software interface"))

    # Add all catalog concepts to semantic retrieval so new artwork does not
    # require another hand-written trigger branch to become selectable.
    candidate_by_id = {asset_id: (title, subtitle) for asset_id, title, subtitle in candidates}
    catalog_ids = [asset_id for asset_id in asset_reg.list_available_stickers() if asset_id != "subject_cutout"]
    catalog_metadata = [asset_reg.get_asset_metadata(asset_id) or {"id": asset_id} for asset_id in catalog_ids]
    # Rank the subject of the footage independently from a style-only prompt.
    # The selected template is scored below, so phrases like "scrapbook style"
    # cannot outrank the actual spoken topic (for example, an AI tutorial).
    style_only_terms = {
        "style", "scrapbook", "aesthetic", "creative", "minimal", "retro",
        "glassmorphism", "pinterest", "cinematic", "vintage", "cute",
    }
    instruction_context = " ".join(
        token for token in re.findall(r"[a-z0-9_]+", additional_instructions.lower())
        if token not in style_only_terms
    )
    semantic_query = " ".join(part for part in (
        speech_low, topic, scene_context, resource_context, instruction_context,
    ) if part).strip()
    semantic_scores, ranking_method = score_asset_descriptions(semantic_query, catalog_metadata)
    threshold = 0.14 if ranking_method == "local_keyword_fallback" else 0.24
    for asset_id, metadata, semantic_score in zip(catalog_ids, catalog_metadata, semantic_scores):
        if semantic_score < threshold or asset_id in candidate_by_id:
            continue
        if metadata.get("category") == "social_engagement" and not is_cta:
            continue
        candidate_by_id[asset_id] = (asset_id.replace("_", " ").upper(), metadata.get("visual_description", ""))

    # Rank with local semantic similarity, explicit relevance validation,
    # keyword evidence, template fit, and recent composition density.
    ranked = []
    style_by_template = {
        "pinterest_scrapbook": {"scrapbook", "pastel"},
        "aesthetic_lifestyle": {"scrapbook", "pastel", "warm"},
        "floating_music_player": {"glass_music"},
        "glassmorphism": {"glass", "tech"},
        "retro_camera": {"retro"},
        "creative_minimal": {"clean"},
    }
    evidence = semantic_query.lower()
    semantic_by_id = dict(zip(catalog_ids, semantic_scores))
    resource_terms = set(re.findall(r"[a-z0-9]{3,}", resource_context.lower()))
    recent_categories = set((composition_state or {}).get("recent_categories", []))
    for order, (asset_id, (title, sub)) in enumerate(candidate_by_id.items()):
        if asset_id in used_assets:
            continue
        val = asset_reg.validate_asset_relevance(
            asset_id=asset_id,
            topic=topic,
            scene_visuals=f"{scene_context} {resource_context}",
            template_id=template.id,
            additional_instructions=additional_instructions,
        )
        if not val.get("relevant", False):
            continue
        metadata = asset_reg.get_asset_metadata(asset_id) or {}
        # Display labels are derived from the catalog. Old cue-specific copy
        # made unsupported claims such as "instant viral highlights".
        title = asset_id.replace("_", " ").title()
        sub = str(metadata.get("visual_description") or metadata.get("intended_purpose") or "")[:120]
        keywords = metadata.get("keywords", [])
        keyword_hits = sum(1 for keyword in keywords if re.search(r"\b" + re.escape(keyword.lower()) + r"\b", evidence))
        template_bonus = 0.12 if metadata.get("style") in style_by_template.get(template.id, set()) else 0.0
        if template.id == "pinterest_scrapbook" and metadata.get("category") == "scrapbook_decorative":
            template_bonus += 0.24
        semantic_score = float(semantic_by_id.get(asset_id, 0.0))
        category = metadata.get("category", "")
        composition_penalty = 0.12 if category and category in recent_categories else 0.0
        final_score = (
            0.18 * float(val.get("score", 0.5))
            + 0.55 * max(0.0, semantic_score)
            + min(0.25, keyword_hits * 0.06)
            + template_bonus
            - composition_penalty
        )
        final_score = max(0.0, min(1.0, final_score))
        matched_resource_terms = sorted(
            term for term in resource_terms
            if term in set(re.findall(r"[a-z0-9]{3,}", " ".join(keywords).lower()))
        )
        ranking_evidence = {
            "final_score": round(final_score, 3),
            "semantic_similarity": round(semantic_score, 3),
            "ranking_method": ranking_method,
            "matched_resource_terms": matched_resource_terms[:8],
            "relevance_validation": val.get("reason", "catalog relevance rules passed"),
            "composition_penalty": round(composition_penalty, 3),
        }
        ranked.append((final_score, -order, asset_id, title, sub, ranking_evidence))

    if ranked:
        _, _, asset_id, title, sub, ranking_evidence = max(ranked)
        return asset_id, title, sub, ranking_evidence

    return None, None, None, {"ranking_method": ranking_method}


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
