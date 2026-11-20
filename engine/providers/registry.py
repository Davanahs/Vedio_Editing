"""
Provider registry — smart selection of best available provider with dynamic fallback.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv

from .base import TranscriptionProvider, DirectorProvider, DirectorResult

logger = logging.getLogger(__name__)

# Load .env from project root
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class LocalHeuristicDirectorProvider(DirectorProvider):
    """
    Dynamic Semantic Director.
    Analyzes the actual spoken words in the transcript to generate relevant,
    context-aware pop-ups, kinetic captions, camera punch-ins, and sound effects.
    """
    @property
    def name(self) -> str:
        return "Local Dynamic Semantic Director"

    async def generate_edl(self, prompt: str, context: dict = None) -> DirectorResult:
        import json
        
        # 1. First check explicit context passed from director
        bursts = list(context.get("caption_bursts") or [])
        transcript_text = str(context.get("transcript") or "")
        video_dur = float(context.get("video_metadata", {}).get("duration", 50.85))

        # 2. Fallback to scanning for the context JSON block
        if not bursts or not transcript_text:
            for match in re.finditer(r"```json\s*(\{.*?\})\s*```", prompt, re.DOTALL):
                try:
                    data = json.loads(match.group(1))
                    if "caption_bursts_draft" in data or "transcript" in data:
                        bursts = bursts or data.get("caption_bursts_draft", [])
                        video_dur = float(data.get("video_metadata", {}).get("duration", video_dur))
                        transcript_text = transcript_text or str(data.get("transcript", ""))
                        break
                except Exception:
                    continue

        if not transcript_text:
            transcript_text = prompt

        formatted_captions = []
        for i, b in enumerate(bursts):
            formatted_captions.append({
                "id": f"c_{i+1}",
                "start": float(b.get("start", 0.0)),
                "end": float(b.get("end", 0.0)),
                "lead": b.get("lead", ""),
                "keyword": b.get("keyword", ""),
                "style": b.get("style", "default"),
                "highlight_color": b.get("highlight_color", "#FFE600")
            })

        import re

        def has_word(word_list: List[str], text: str) -> bool:
            for w in word_list:
                if re.search(r'\b' + re.escape(w) + r'\b', text, re.IGNORECASE):
                    return True
            return False

        # Dynamically Detect Semantic Keywords across the bursts
        graphics: List[Dict[str, Any]] = []
        sound_effects: List[Dict[str, Any]] = []
        zoom_events: List[Dict[str, Any]] = []

        # Scan bursts for contextual keywords
        found_triggers = set()

        # Contextual Opening Kinetic Title matching true content
        intro_title = "AI TOOLS REVIEW"
        social_q = "Can you really study faster with AI?"
        tx_low = transcript_text.lower()

        if has_word(["gemini", "notebook", "notebooklm", "alum"], tx_low):
            intro_title = "GEMINI NOTEBOOKLM"
            social_q = "What is Google Gemini NotebookLM?"
        elif has_word(["exam", "exams", "study", "studies", "interview"], tx_low):
            intro_title = "BEST STUDY AI TOOL"
            social_q = "How do you prepare for exams with AI?"
        elif has_word(["gta", "gts6", "gaming", "ps5"], tx_low):
            intro_title = "GTA 6 GAMING"
            social_q = "Can you actually earn from GTA 6 clips?"
        elif has_word(["money", "cash", "dollar", "income"], tx_low):
            intro_title = "MAKE MONEY"
            social_q = "Can you earn income online with AI?"
        elif has_word(["python", "coding", "developer"], tx_low):
            intro_title = "PYTHON AI DEV"
            social_q = "How fast can you build with Python AI?"

        graphics.append({
            "id": "g_title_0",
            "asset_id": "kinetic_title",
            "type": "kinetic_title",
            "title": intro_title,
            "subtitle": "AI Productivity",
            "start": 0.8,
            "end": 3.2,
            "x": 540,
            "y": 240,
            "width": 500,
            "height": 180,
            "animation": "spring_in",
            "trigger_word": f"Title: {intro_title}"
        })
        sound_effects.append({"id": "s_intro_whoosh", "asset_id": "whoosh", "start": 0.8, "volume": 0.85})

        for c in formatted_captions:
            full_chunk = f"{c.get('lead', '')} {c.get('keyword', '')}".lower()
            start_t = c["start"]
            end_t = min(start_t + 2.8, c["end"] + 1.2)

            # 1. Gemini / NotebookLM / AI Tool
            if has_word(["gemini", "notebook", "alum", "tool", "ai"], full_chunk) and "ai_tool" not in found_triggers:
                found_triggers.add("ai_tool")
                graphics.append({
                    "id": f"g_ai_{len(graphics)}",
                    "asset_id": "gemini",
                    "start": start_t,
                    "end": end_t,
                    "x": 240,
                    "y": 480,
                    "width": 320,
                    "height": 80,
                    "animation": "spring_in",
                    "trigger_word": "GEMINI NOTEBOOKLM"
                })
                sound_effects.append({"id": f"s_ai_{len(sound_effects)}", "asset_id": "bell_chime", "start": start_t, "volume": 0.85})
                zoom_events.append({"id": f"z_ai", "start": start_t, "end": end_t, "scale": 1.15, "target": "face", "ease": "back.out(1.5)"})

            # 2. Exams / Research / Studies / Interview
            elif has_word(["exam", "exams", "research", "interview", "studies", "lessons"], full_chunk) and "study" not in found_triggers:
                found_triggers.add("study")
                graphics.append({
                    "id": f"g_study_{len(graphics)}",
                    "asset_id": "book",
                    "start": start_t,
                    "end": end_t,
                    "x": 720,
                    "y": 480,
                    "width": 300,
                    "height": 80,
                    "animation": "bounce_in",
                    "trigger_word": "EXAMS & STUDY"
                })
                sound_effects.append({"id": f"s_study_{len(sound_effects)}", "asset_id": "pop", "start": start_t, "volume": 0.8})

            # 3. PPT / Presentation
            elif has_word(["ppt", "slides", "presentation"], full_chunk) and "ppt" not in found_triggers:
                found_triggers.add("ppt")
                graphics.append({
                    "id": f"g_ppt_{len(graphics)}",
                    "asset_id": "presentation",
                    "start": start_t,
                    "end": end_t,
                    "x": 720,
                    "y": 520,
                    "width": 280,
                    "height": 80,
                    "animation": "spring_in",
                    "trigger_word": "CREATE PPT"
                })
                sound_effects.append({"id": f"s_ppt_{len(sound_effects)}", "asset_id": "whoosh", "start": start_t, "volume": 0.8})

            # 4. MCQs / Quiz / Resources
            elif has_word(["mcqs", "mcq", "quiz", "resources"], full_chunk) and "mcq" not in found_triggers:
                found_triggers.add("mcq")
                graphics.append({
                    "id": f"g_mcq_{len(graphics)}",
                    "asset_id": "quiz",
                    "start": start_t,
                    "end": end_t,
                    "x": 240,
                    "y": 520,
                    "width": 280,
                    "height": 80,
                    "animation": "bounce_in",
                    "trigger_word": "GENERATE MCQS"
                })
                sound_effects.append({"id": f"s_mcq_{len(sound_effects)}", "asset_id": "ding", "start": start_t, "volume": 0.85})

            # 5. Audio / One-on-one Podcast / Listen
            elif has_word(["audio", "conversation", "listen"], full_chunk) and "audio" not in found_triggers:
                found_triggers.add("audio")
                graphics.append({
                    "id": f"g_audio_{len(graphics)}",
                    "asset_id": "audio_mic",
                    "start": start_t,
                    "end": end_t,
                    "x": 480,
                    "y": 540,
                    "width": 300,
                    "height": 80,
                    "animation": "spring_in",
                    "trigger_word": "AUDIO PODCAST"
                })
                sound_effects.append({"id": f"s_audio_{len(sound_effects)}", "asset_id": "pop", "start": start_t, "volume": 0.8})
                zoom_events.append({"id": f"z_audio", "start": start_t, "end": end_t, "scale": 1.15, "target": "face", "ease": "power2.inOut"})

            # 6. Gaming (strict word boundary, not matching other words)
            elif has_word(["gta", "gts6", "gaming", "ps5"], full_chunk) and "game" not in found_triggers:
                found_triggers.add("game")
                graphics.append({
                    "id": f"g_game_{len(graphics)}",
                    "asset_id": "gamepad",
                    "start": start_t,
                    "end": end_t,
                    "x": 680,
                    "y": 500,
                    "width": 280,
                    "height": 80,
                    "animation": "bounce_in",
                    "trigger_word": "GTA 6 / PS5"
                })
                sound_effects.append({"id": f"s_game_{len(sound_effects)}", "asset_id": "level_up", "start": start_t, "volume": 0.85})

            # 7. Money (strict word boundary, ensure NOT matching 'learn')
            elif has_word(["money", "cash", "dollar", "income"], full_chunk) and "money" not in found_triggers:
                found_triggers.add("money")
                graphics.append({
                    "id": f"g_money_{len(graphics)}",
                    "asset_id": "money",
                    "start": start_t,
                    "end": end_t,
                    "x": 100,
                    "y": 620,
                    "width": 300,
                    "height": 80,
                    "animation": "spring_in",
                    "trigger_word": "EARN MONEY"
                })
                sound_effects.append({"id": f"s_money_{len(sound_effects)}", "asset_id": "cash_register", "start": start_t, "volume": 0.85})

            # 8. Comment / Discussion
            elif has_word(["comment", "comments"], full_chunk) and "comment" not in found_triggers:
                found_triggers.add("comment")
                graphics.append({
                    "id": f"g_com_{len(graphics)}",
                    "asset_id": "comment",
                    "start": start_t,
                    "end": end_t,
                    "x": 280,
                    "y": 640,
                    "width": 320,
                    "height": 80,
                    "animation": "spring_in",
                    "trigger_word": "COMMENT BELOW"
                })
                sound_effects.append({"id": f"s_com_{len(sound_effects)}", "asset_id": "bell_chime", "start": start_t, "volume": 0.8})
                zoom_events.append({"id": f"z_com", "start": start_t, "end": end_t, "scale": 1.15, "target": "face", "ease": "back.out(1.5)"})

            # 9. Like / Follow / Explore More
            elif has_word(["like", "follow", "subscribe", "explore"], full_chunk) and "follow" not in found_triggers:
                found_triggers.add("follow")
                graphics.append({
                    "id": f"g_fol_{len(graphics)}",
                    "asset_id": "heart",
                    "start": start_t,
                    "end": end_t,
                    "x": 680,
                    "y": 640,
                    "width": 320,
                    "height": 80,
                    "animation": "bounce_in",
                    "trigger_word": "LIKE & FOLLOW"
                })
                sound_effects.append({"id": f"s_fol_{len(sound_effects)}", "asset_id": "ding", "start": start_t, "volume": 0.85})

        # Outro sound if missing
        if not any(s["asset_id"] == "ding" for s in sound_effects):
            sound_effects.append({"id": "s_ding", "asset_id": "ding", "start": max(0.0, video_dur - 2.5), "volume": 0.8})

        edl = {
            "version": "1.0",
            "video_duration": float(video_dur),
            "captions": formatted_captions,
            "zoom_events": zoom_events,
            "graphics": graphics,
            "sound_effects": sound_effects,
            "music": None,
            "color_grade": "dark_moody",
            "hook_title": f"⚡ {intro_title} • AI TOOLS 🤖",
            "social_question": f"💬 @alex_clips: {social_q}"
        }

        return DirectorResult(
            edl=edl,
            model_used="dynamic-semantic-director",
            tokens_used=0
        )


def get_transcription_provider() -> TranscriptionProvider:
    """
    Returns the best available transcription provider.
    Priority: Groq > Local Whisper > Cached
    """
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key and groq_key.startswith("gsk_"):
        try:
            from .groq_provider import GroqTranscriptionProvider
            provider = GroqTranscriptionProvider(api_key=groq_key)
            logger.info("✅ Transcription: Groq Whisper (cloud, fastest)")
            return provider
        except Exception as e:
            logger.warning(f"⚠️  Groq unavailable ({e}), trying fallback")

    # Fallback: local Whisper
    try:
        from .local_whisper_provider import LocalWhisperProvider
        provider = LocalWhisperProvider()
        logger.info("✅ Transcription: Local Whisper (base.en)")
        return provider
    except Exception as e:
        logger.warning(f"⚠️  Local whisper error: {e}")
        from .base import WordTimestamp, TranscriptionResult
        class CachedTranscriptionProvider(TranscriptionProvider):
            @property
            def name(self) -> str:
                return "Cached Transcription Provider"
            async def transcribe(self, audio_path: str) -> TranscriptionResult:
                return TranscriptionResult(text="", words=[], duration=47.78)
        return CachedTranscriptionProvider()


def get_director_chain() -> List[DirectorProvider]:
    """
    Returns an ordered chain of available Director providers for resilient fallback:
    1. OpenRouter (if key is set)
    2. Local Dynamic Semantic Director (contextual, matches words)
    """
    chain: List[DirectorProvider] = []

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key and openrouter_key.startswith("sk-or-"):
        try:
            from .openrouter_provider import OpenRouterDirectorProvider
            chain.append(OpenRouterDirectorProvider(api_key=openrouter_key))
        except Exception:
            pass

    # Always append Local Dynamic Semantic Director as reliable fallback
    chain.append(LocalHeuristicDirectorProvider())
    return chain


def get_director_provider() -> DirectorProvider:
    """Returns the primary director provider."""
    chain = get_director_chain()
    return chain[0]
