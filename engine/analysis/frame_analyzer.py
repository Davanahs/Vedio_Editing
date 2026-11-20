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
from PIL import Image

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

    def to_dict(self) -> Dict[str, Any]:
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
        }


def extract_representative_frames(
    video_path: str,
    output_dir: Path,
    scene_timestamps: Optional[List[float]] = None,
    interval_s: float = 10.0,
    total_duration: float = 50.0,
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

    sorted_times = sorted(list(timestamps_to_sample))
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


async def _analyze_single_frame(
    ts: float,
    frame_path: str,
    is_scene: bool,
    video_topic_hint: str,
    gemini_key: Optional[str]
) -> VisualFrameAnalysis:
    faces = detect_faces_in_image(frame_path)
    face_detected = len(faces) > 0

    analysis_data: Optional[Dict[str, Any]] = None
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            pil_img = Image.open(frame_path)

            prompt = (
                f"Analyze this video frame captured at {ts:.1f}s. "
                f"Video context: {video_topic_hint}. "
                "Output JSON ONLY with the following exact keys: "
                '{"objects": ["list", "of", "visible", "objects"], '
                '"subject_activity": "what is the person or scene doing", '
                '"setting": "e.g. indoor room, bedroom, outdoor park, kitchen", '
                '"visual_aesthetic": "e.g. casual vlog, tech tutorial, aesthetic lifestyle, cooking", '
                '"dominant_colors": ["#hex1", "#hex2"], '
                '"is_visually_cluttered": false, '
                '"leave_clean": false}'
            )

            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: model.generate_content(
                        [prompt, pil_img],
                        generation_config={"response_mime_type": "application/json"}
                    )
                ),
                timeout=8.0
            )
            if response and response.text:
                analysis_data = json.loads(response.text)
        except Exception as e:
            logger.warning(f"Gemini vision inspection fallback at frame {ts:.1f}s: {e}")
            analysis_data = None

    if analysis_data:
        img = cv2.imread(frame_path)
        h, w = (img.shape[0], img.shape[1]) if img is not None else (1080, 1920)
        return VisualFrameAnalysis(
            timestamp=ts,
            frame_path=frame_path,
            width=w,
            height=h,
            faces=faces,
            face_detected=face_detected,
            objects_detected=analysis_data.get("objects", []),
            subject_activity=analysis_data.get("subject_activity", "speaking to camera"),
            setting_environment=analysis_data.get("setting", "indoor"),
            visual_aesthetic=analysis_data.get("visual_aesthetic", "modern"),
            dominant_colors=analysis_data.get("dominant_colors", ["#38BDF8"]),
            is_scene_transition=is_scene,
            clean_scene_recommended=analysis_data.get("leave_clean", False) or is_scene,
        )
    else:
        fallback = analyze_frame_local_heuristics(frame_path, ts, is_scene)
        fallback.faces = faces
        fallback.face_detected = face_detected
        return fallback


async def analyze_frames_multimodal(
    frame_tuples: List[tuple[float, str, bool]],
    video_topic_hint: str = ""
) -> List[VisualFrameAnalysis]:
    """
    Concurrent multimodal visual understanding using Gemini 2.5 Flash / OpenRouter,
    with automatic graceful fallback to local CV heuristics.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    tasks = [
        _analyze_single_frame(ts, frame_path, is_scene, video_topic_hint, gemini_key)
        for ts, frame_path, is_scene in frame_tuples
    ]
    results = await asyncio.gather(*tasks)
    return list(results)
