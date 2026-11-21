"""
Audio & Narration Segmenter.
Divides spoken audio into semantic topical time segments (e.g., Intro, Feature Callout,
Demo, Conclusion/CTA) with emotional tone, keywords, and speech density.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AudioSegment:
    segment_id: str
    start: float
    end: float
    duration: float
    text: str
    topic_summary: str
    keywords: List[str]
    tone: str
    speech_density: float  # words per second
    is_quiet: bool
    is_cta: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "duration": round(self.duration, 2),
            "text": self.text,
            "topic_summary": self.topic_summary,
            "keywords": self.keywords,
            "tone": self.tone,
            "speech_density": round(self.speech_density, 2),
            "is_quiet": self.is_quiet,
            "is_cta": self.is_cta,
        }


def segment_audio_narration(
    words: List[Dict[str, Any]],
    total_duration: float,
    min_segment_duration: float = 5.0,
    max_segment_duration: float = 12.0,
) -> List[AudioSegment]:
    """
    Groups word-level timestamps into logical narrative segments based on sentence
    boundaries, topic shifts, and duration constraints.
    """
    if not words:
        # Fallback for silent video or video without words
        return [
            AudioSegment(
                segment_id="seg_1",
                start=0.0,
                end=total_duration,
                duration=total_duration,
                text="",
                topic_summary="Ambient scene with background audio",
                keywords=[],
                tone="ambient",
                speech_density=0.0,
                is_quiet=True,
                is_cta=False,
            )
        ]

    segments: List[AudioSegment] = []
    current_words: List[Dict[str, Any]] = []
    seg_start = words[0].get("start", 0.0)

    for i, w in enumerate(words):
        current_words.append(w)
        word_text = w.get("word", "").strip()
        w_end = w.get("end", seg_start)
        seg_dur = w_end - seg_start

        # Break conditions:
        # 1. Punctuation break after min_segment_duration
        ends_sentence = word_text.endswith((".", "!", "?"))
        # 2. Exceeded max_segment_duration
        over_max = seg_dur >= max_segment_duration
        # 3. Next word has a long pause (> 0.8s)
        next_pause = False
        if i < len(words) - 1:
            next_start = words[i + 1].get("start", w_end)
            if next_start - w_end >= 0.8:
                next_pause = True

        is_last = (i == len(words) - 1)

        if is_last or (seg_dur >= min_segment_duration and (ends_sentence or next_pause or over_max)):
            seg_end = w_end
            text_str = " ".join([cw.get("word", "").strip() for cw in current_words])
            duration = max(0.1, seg_end - seg_start)
            density = len(current_words) / duration

            # Analyze topic and tone
            topic, keywords, tone, is_cta = _analyze_segment_semantics(text_str, is_last, i, len(words))

            segments.append(
                AudioSegment(
                    segment_id=f"seg_{len(segments)+1}",
                    start=seg_start,
                    end=seg_end,
                    duration=duration,
                    text=text_str,
                    topic_summary=topic,
                    keywords=keywords,
                    tone=tone,
                    speech_density=density,
                    is_quiet=(density < 0.5),
                    is_cta=is_cta,
                )
            )

            # Reset for next segment
            if not is_last:
                seg_start = words[i + 1].get("start", seg_end)
                current_words = []

    return segments


def _analyze_segment_semantics(text: str, is_last: bool, word_idx: int, total_words: int) -> tuple[str, List[str], str, bool]:
    """Derive topic summary, keywords, emotional tone, and CTA flag from segment text."""
    low = text.lower()
    keywords: List[str] = []
    is_cta = False
    tone = "informative"

    # Extract keywords
    key_terms = [
        "gemini", "notebooklm", "ai", "exams", "study", "research", "interview",
        "mcqs", "ppt", "presentation", "audio", "podcast", "notes", "code", "laptop",
        "recipe", "cooking", "outfit", "style", "game", "fashion", "vlog", "tips"
    ]
    for kt in key_terms:
        if re.search(r'\b' + re.escape(kt) + r'\b', low):
            keywords.append(kt)

    # Topic synthesis
    if any(k in low for k in ["like", "comment", "subscribe", "follow", "website link"]):
        topic = "Audience Engagement & Call to Action"
        tone = "upbeat friendly"
        is_cta = True
    elif any(k in low for k in ["gta", "gts", "gta6", "gts6", "gaming", "game", "clipping", "clips", "earn money", "views"]):
        topic = "Gaming & Content Monetization"
        tone = "high-energy discovery"
    elif any(k in low for k in ["gemini", "notebooklm", "notebook alum"]):
        topic = "AI Productivity: Gemini NotebookLM"
        tone = "enthusiastic discovery"
    elif any(k in low for k in ["exam", "exams", "study", "research", "interview"]):
        topic = "Academic & Career Utility"
        tone = "instructional helpful"
    elif any(k in low for k in ["mcq", "quiz", "questions"]):
        topic = "Automated Quiz & Knowledge Check"
        tone = "excited educational"
    elif any(k in low for k in ["ppt", "presentation", "slides"]):
        topic = "Presentation & Document Creation"
        tone = "productive efficient"
    elif any(k in low for k in ["audio", "podcast", "conversation", "listen"]):
        topic = "Audio Synthesis & Dialogue"
        tone = "conversational engaging"
    elif any(k in low for k in ["tool", "software", "app", "application", "ai"]):
        topic = "AI Tools & Workflow Overview"
        tone = "clear narrative"
    elif word_idx < total_words * 0.25:
        topic = "Video Introduction & Hook"
        tone = "engaging welcoming"
    elif is_last:
        topic = "Summary & Closing Takeaway"
        tone = "warm concluding"
        is_cta = True
    else:
        topic = "Core Feature Explanation"
        tone = "clear narrative"

    return topic, keywords, tone, is_cta
