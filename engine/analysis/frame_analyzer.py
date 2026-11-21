"""
Multimodal Visual Frame Analyzer.
Extracts representative video frames at regular sampling intervals (~10s) and scene changes,
detects face bounding boxes with OpenCV, and performs multimodal vision analysis
using Gemini 2.5 Flash / OpenRouter with local computer vision heuristic fallback.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

import cv2
import httpx
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


@dataclass
class VisualFrameAnalysis:
    timestamp: float
    frame_path: str
    width: int
    height: int
    faces: List[Dict[str, int]]  # [{'x': int, 'y': int, 'w': int, 'h': int}]
    face_detected: bool
    objects_detected: List[str]
    subject_activity: str
    setting_environment: str
    visual_aesthetic: str
    dominant_colors: List[str]
    is_scene_transition: bool
    clean_scene_recommended: bool  # True if visually rich or transition where overlays would clutter
    analysis_provider: str = "opencv_heuristic"
    analysis_model: str = ""
    analysis_status: str = "heuristic"
    visual_summary: str = ""
    spoken_topics: List[str] = field(default_factory=list)
    mentioned_entities: List[str] = field(default_factory=list)
    is_visually_cluttered: bool = False
    fallback_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        normalized_faces = [
            {"x": round(max(0, face.get("x", 0)) / max(1, self.width), 4),
             "y": round(max(0, face.get("y", 0)) / max(1, self.height), 4),
             "w": round(max(0, face.get("w", 0)) / max(1, self.width), 4),
             "h": round(max(0, face.get("h", 0)) / max(1, self.height), 4)}
            for face in self.faces
        ]
        return {
            "timestamp": round(self.timestamp, 2),
            "frame_path": self.frame_path,
            "width": self.width,
            "height": self.height,
            "face_detected": self.face_detected,
            "faces": self.faces,
            "objects_detected": self.objects_detected,
            "subject_activity": self.subject_activity,
            "setting_environment": self.setting_environment,
            "visual_aesthetic": self.visual_aesthetic,
            "dominant_colors": self.dominant_colors,
            "is_scene_transition": self.is_scene_transition,
            "clean_scene_recommended": self.clean_scene_recommended,
            "normalized_faces": normalized_faces,
            "analysis_provider": self.analysis_provider,
            "analysis_model": self.analysis_model,
            "analysis_status": self.analysis_status,
            "visual_summary": self.visual_summary,
            "spoken_topics": self.spoken_topics,
            "mentioned_entities": self.mentioned_entities,
            "is_visually_cluttered": self.is_visually_cluttered,
            "fallback_reason": self.fallback_reason,
        }


def extract_representative_frames(
    video_path: str,
    output_dir: Path,
    scene_timestamps: Optional[List[float]] = None,
    interval_s: float = 10.0,
    total_duration: float = 50.0,
    max_samples: int = 24,
) -> List[tuple[float, str, bool]]:
    """
    Extracts representative frames at regular ~10s intervals and at scene changes.
    Returns list of (timestamp_s, saved_image_path, is_scene_change).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Cannot open video for frame extraction: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    vid_dur = total_frames / fps if fps > 0 else total_duration

    if vid_dur <= 0:
        cap.release()
        return []
    max_samples = max(1, int(max_samples))
    interval_s = max(0.5, float(interval_s))

    # Determine sample timestamps
    timestamps_to_sample = set()
    # 1. Regular 10s intervals (e.g. 3.0s, 13.0s, 23.0s, 33.0s, 43.0s)
    t = min(3.0, vid_dur * 0.1)
    while t < vid_dur:
        timestamps_to_sample.add(round(t, 2))
        t += interval_s

    # 2. Add detected scene transitions (offset by 0.5s into the new scene)
    scene_set = set()
    if scene_timestamps:
        for st in scene_timestamps:
            target_t = round(min(vid_dur - 0.5, st + 0.5), 2)
            if target_t > 0:
                timestamps_to_sample.add(target_t)
                scene_set.add(target_t)

    sorted_times = sorted(timestamps_to_sample)
    if len(sorted_times) > max_samples:
        scene_candidates = sorted(t for t in scene_set if t in timestamps_to_sample)
        regular_candidates = [t for t in sorted_times if t not in scene_set]
        scene_slots = min(len(scene_candidates), max_samples // 2)
        regular_slots = max_samples - scene_slots

        def evenly_pick(values: list[float], count: int) -> list[float]:
            if count <= 0 or not values:
                return []
            if len(values) <= count:
                return values
            if count == 1:
                return [values[len(values) // 2]]
            return [values[round(i * (len(values) - 1) / (count - 1))] for i in range(count)]

        selected = evenly_pick(scene_candidates, scene_slots) + evenly_pick(regular_candidates, regular_slots)
        selected_set = set(selected)
        if len(selected_set) < max_samples:
            selected.extend(t for t in sorted_times if t not in selected_set and len(set(selected)) < max_samples)
        sorted_times = sorted(set(selected))[:max_samples]
    extracted: List[tuple[float, str, bool]] = []

    for ts in sorted_times:
        target_frame_num = int(ts * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_num)
        ret, frame = cap.read()
        if ret and frame is not None:
            is_scene = (ts in scene_set)
            fname = f"frame_{int(ts*100):05d}{'_scene' if is_scene else ''}.jpg"
            out_path = output_dir / fname
            # Save compressed JPEG
            cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            extracted.append((ts, str(out_path), is_scene))

    cap.release()
    return extracted


def detect_faces_in_image(image_path: str) -> List[Dict[str, int]]:
    """Detect faces using OpenCV Haar Cascades."""
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_path):
        return []

    face_cascade = cv2.CascadeClassifier(cascade_path)
    img = cv2.imread(image_path)
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    result = []
    for (x, y, w, h) in faces:
        result.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
    return result


def analyze_frame_local_heuristics(
    image_path: str,
    timestamp: float,
    is_scene_transition: bool
) -> VisualFrameAnalysis:
    """Local computer vision fallback for frame analysis."""
    img = cv2.imread(image_path)
    if img is None:
        return VisualFrameAnalysis(
            timestamp=timestamp,
            frame_path=image_path,
            width=1080,
            height=1920,
            faces=[],
            face_detected=False,
            objects_detected=[],
            subject_activity="speaking to camera",
            setting_environment="indoor studio",
            visual_aesthetic="clean video",
            dominant_colors=["#1E293B"],
            is_scene_transition=is_scene_transition,
            clean_scene_recommended=is_scene_transition,
        )

    h, w, _ = img.shape
    faces = detect_faces_in_image(image_path)
    face_detected = len(faces) > 0

    # Color analysis
    avg_color_per_row = numpy_mean_bgr = img.mean(axis=0).mean(axis=0)
    b, g, r = [int(c) for c in avg_color_per_row]
    hex_color = f"#{r:02x}{g:02x}{b:02x}"

    objects = []
    if face_detected:
        objects.append("presenter face")
        activity = "presenter addressing audience directly"
    else:
        activity = "demonstration or visual transition"

    return VisualFrameAnalysis(
        timestamp=timestamp,
        frame_path=image_path,
        width=w,
        height=h,
        faces=faces,
        face_detected=face_detected,
        objects_detected=objects,
        subject_activity=activity,
        setting_environment="indoor presentation room",
        visual_aesthetic="clean content creator setup",
        dominant_colors=[hex_color],
        is_scene_transition=is_scene_transition,
        clean_scene_recommended=is_scene_transition,
    )


class _VisualObservation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    objects: list[str] = Field(default_factory=list, max_length=20)
    subject_activity: str = Field(default="", max_length=300)
    setting: str = Field(default="", max_length=200)
    visual_aesthetic: str = Field(default="", max_length=200)
    dominant_colors: list[str] = Field(default_factory=list, max_length=8)
    visual_summary: str = Field(default="", max_length=500)
    spoken_topics: list[str] = Field(default_factory=list, max_length=12)
    mentioned_entities: list[str] = Field(default_factory=list, max_length=20)
    is_visually_cluttered: bool = False
    leave_clean: bool = False


def _parse_visual_observation(raw: str) -> _VisualObservation:
    clean = raw.strip()
    fence = chr(96) * 3
    if clean.startswith(fence):
        clean = clean.split("\n", 1)[-1].rsplit(fence, 1)[0].strip()
    first, last = clean.find("{"), clean.rfind("}")
    if first < 0 or last <= first:
        raise ValueError("Vision provider returned no JSON object")
    return _VisualObservation.model_validate(json.loads(clean[first:last + 1]))


def _vision_prompt(timestamp: float, topic: str, transcript_context: str) -> str:
    return (
        "Describe only evidence visible in this video frame. Do not infer a brand, "
        "product, person identity, or action that is not clearly visible. Transcript "
        "is context only and may be wrong. Return one JSON object with keys: "
        "objects (string array), subject_activity, setting, visual_aesthetic, "
        "dominant_colors (hex string array), visual_summary, spoken_topics "
        "(topics supported by nearby transcript), mentioned_entities (proper names "
        "that appear exactly in the nearby transcript), is_visually_cluttered "
        "(boolean), leave_clean (boolean). "
        "Set leave_clean true when added graphics would obscure important content. "
        f"Frame timestamp: {timestamp:.2f}s. Topic context: {topic[:300]}. "
        f"Nearby transcript: {transcript_context[:500]}"
    )


async def _call_gemini_vision(image: Image.Image, prompt: str, api_key: str) -> tuple[str, str]:
    import google.generativeai as genai

    model_name = os.getenv("AURA_GEMINI_VISION_MODEL", "models/gemini-2.5-flash")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    loop = asyncio.get_running_loop()
    response = await asyncio.wait_for(
        loop.run_in_executor(
            None,
            lambda: model.generate_content(
                [prompt, image],
                generation_config={"response_mime_type": "application/json", "temperature": 0.1},
            ),
        ),
        timeout=float(os.getenv("AURA_VISION_TIMEOUT_SECONDS", "25")),
    )
    if not response or not getattr(response, "text", None):
        raise ValueError("Gemini returned an empty vision response")
    return response.text, model_name


async def _call_openrouter_vision(image_bytes: bytes, prompt: str, api_key: str) -> tuple[str, str]:
    model_name = os.getenv("AURA_OPENROUTER_VISION_MODEL", "openrouter/free")
    data_url = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": model_name,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        "temperature": 0.1,
        "max_tokens": 600,
    }
    timeout = float(os.getenv("AURA_VISION_TIMEOUT_SECONDS", "25"))
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:5050"),
                "X-Title": "Aura AI Creative Video Studio",
            },
            json=payload,
        )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("OpenRouter returned no vision choices")
    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenRouter returned an empty vision response")
    return content, str(data.get("model") or model_name)


def _transcript_context_for_timestamp(timestamp: float, segments: list[dict[str, Any]]) -> str:
    matching = [
        str(segment.get("text", ""))
        for segment in segments
        if float(segment.get("start", 0.0)) - 2.0 <= timestamp <= float(segment.get("end", 0.0)) + 2.0
        and segment.get("text")
    ]
    return " ".join(matching)[:500]


def _select_frame_samples(
    frame_tuples: List[tuple[float, str, bool]],
    max_samples: int,
) -> List[tuple[float, str, bool]]:
    ordered = sorted(frame_tuples, key=lambda item: item[0])
    unique: list[tuple[float, str, bool]] = []
    seen: set[tuple[float, str]] = set()
    for sample in ordered:
        key = (round(float(sample[0]), 2), str(sample[1]))
        if key not in seen and Path(sample[1]).is_file():
            seen.add(key)
            unique.append((float(sample[0]), str(sample[1]), bool(sample[2])))
    max_samples = max(1, max_samples)
    if len(unique) <= max_samples:
        return unique
    if max_samples == 1:
        return [unique[len(unique) // 2]]
    indexes = [round(i * (len(unique) - 1) / (max_samples - 1)) for i in range(max_samples)]
    return [unique[index] for index in indexes]


async def _analyze_single_frame(
    ts: float,
    frame_path: str,
    is_scene: bool,
    video_topic_hint: str,
    transcript_context: str = "",
) -> VisualFrameAnalysis:
    faces = detect_faces_in_image(frame_path)
    try:
        with Image.open(frame_path) as source:
            image = source.convert("RGB")
            image.thumbnail((1024, 1024))
            from io import BytesIO
            image_buffer = BytesIO()
            image.save(image_buffer, format="JPEG", quality=82, optimize=True)
            image_bytes = image_buffer.getvalue()
        width, height = image.size
        prompt = _vision_prompt(ts, video_topic_hint, transcript_context)
    except Exception as exc:
        fallback = analyze_frame_local_heuristics(frame_path, ts, is_scene)
        fallback.faces = faces
        fallback.face_detected = bool(faces)
        fallback.fallback_reason = f"frame_preparation_failed:{type(exc).__name__}"
        return fallback

    providers: list[tuple[str, str]] = []
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key.startswith("AIzaSy"):
        gemini_key = ""
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if gemini_key:
        providers.append(("gemini", gemini_key))
    if openrouter_key:
        providers.append(("openrouter", openrouter_key))

    errors: list[str] = []
    for provider, api_key in providers:
        try:
            if provider == "gemini":
                raw, model_name = await _call_gemini_vision(image, prompt, api_key)
            else:
                raw, model_name = await _call_openrouter_vision(image_bytes, prompt, api_key)
            observation = _parse_visual_observation(raw)
            return VisualFrameAnalysis(
                timestamp=ts,
                frame_path=frame_path,
                width=width,
                height=height,
                faces=faces,
                face_detected=bool(faces),
                objects_detected=observation.objects,
                subject_activity=observation.subject_activity or "not identified",
                setting_environment=observation.setting or "not identified",
                visual_aesthetic=observation.visual_aesthetic or "not identified",
                dominant_colors=observation.dominant_colors,
                is_scene_transition=is_scene,
                clean_scene_recommended=observation.leave_clean or observation.is_visually_cluttered or is_scene,
                analysis_provider=provider,
                analysis_model=model_name,
                analysis_status="model",
                visual_summary=observation.visual_summary,
                spoken_topics=observation.spoken_topics,
                mentioned_entities=observation.mentioned_entities,
                is_visually_cluttered=observation.is_visually_cluttered,
            )
        except Exception as exc:
            errors.append(f"{provider}:{type(exc).__name__}")
            logger.warning("Vision provider %s failed for frame %.2fs: %s", provider, ts, type(exc).__name__)

    fallback = analyze_frame_local_heuristics(frame_path, ts, is_scene)
    fallback.faces = faces
    fallback.face_detected = bool(faces)
    fallback.fallback_reason = ",".join(errors) if errors else "no_vision_provider_configured"
    return fallback


async def analyze_frames_multimodal(
    frame_tuples: List[tuple[float, str, bool]],
    video_topic_hint: str = "",
    audio_segments: Optional[List[dict[str, Any]]] = None,
    max_samples: int | None = None,
) -> List[VisualFrameAnalysis]:
    """Analyze a bounded frame set with model calls, validation, and explicit fallback provenance."""
    try:
        configured_limit = int(os.getenv("AURA_MAX_ANALYSIS_FRAMES", "24"))
    except ValueError:
        configured_limit = 24
    limit = max_samples if max_samples is not None else configured_limit
    samples = _select_frame_samples(frame_tuples, max(1, min(60, int(limit))))
    if not samples:
        return []
    try:
        concurrency = int(os.getenv("AURA_VISION_CONCURRENCY", "3"))
    except ValueError:
        concurrency = 3
    semaphore = asyncio.Semaphore(max(1, min(8, concurrency)))
    segments = audio_segments or []

    async def analyze(sample: tuple[float, str, bool]) -> VisualFrameAnalysis:
        timestamp, path, is_scene = sample
        context = _transcript_context_for_timestamp(timestamp, segments)
        async with semaphore:
            return await _analyze_single_frame(timestamp, path, is_scene, video_topic_hint, context)

    return list(await asyncio.gather(*(analyze(sample) for sample in samples)))
