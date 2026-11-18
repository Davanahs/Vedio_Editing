"""
Main async video analyzer — orchestrates all analysis stages.
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from .audio_extractor import extract_audio
from .face_tracker import track_faces_sampled
from .pause_detector import detect_pauses
from .scene_detector import detect_scenes
from .video_probe import probe_video

logger = logging.getLogger(__name__)


async def analyze_video(video_path: str, transcript: dict) -> dict:
    """
    Full async video analysis.
    Runs audio extraction, video probe, and scene detection concurrently.
    Runs face tracking in a thread pool (CPU-bound).

    Args:
        video_path: Path to source video.
        transcript: Transcription result dict (with 'words' list).

    Returns:
        Dict with keys: probe, scenes, pauses, faces, audio_path, benchmarks
    """
    video_path = str(video_path)
    timings: dict[str, float] = {}

    # --- Stage 1: Probe + Scene detection concurrently ---
    t0 = time.perf_counter()
    audio_out = str(Path(video_path).parent / "extracted_audio.wav")

    logger.info("🔍 Analyzing video concurrently (probe + audio + scenes)...")
    probe_task = asyncio.create_task(probe_video(video_path))
    audio_task = asyncio.create_task(extract_audio(video_path, audio_out))
    scene_task = asyncio.create_task(detect_scenes(video_path, threshold=0.4))

    probe, audio_path, scenes = await asyncio.gather(
        probe_task, audio_task, scene_task, return_exceptions=True
    )

    timings["probe_audio_scenes"] = round(time.perf_counter() - t0, 2)

    # Handle partial failures gracefully
    if isinstance(probe, Exception):
        logger.warning(f"⚠️  Video probe failed: {probe}")
        probe = {}
    if isinstance(audio_path, Exception):
        logger.warning(f"⚠️  Audio extraction failed: {audio_path}")
        audio_path = None
    if isinstance(scenes, Exception):
        logger.warning(f"⚠️  Scene detection failed: {scenes}")
        scenes = []

    # --- Stage 2: Pause detection (synchronous, fast) ---
    words = transcript.get("words", [])
    pauses = detect_pauses(words, min_gap=0.3)
    logger.info(f"⏸️  Found {len(pauses)} pauses, {len(scenes)} scene changes")

    # --- Stage 3: Face tracking (CPU-bound, thread pool) ---
    t_face = time.perf_counter()
    logger.info("👤 Starting face tracking (thread pool)...")
    loop = asyncio.get_event_loop()
    try:
        faces = await loop.run_in_executor(
            None, track_faces_sampled, video_path, 30
        )
    except Exception as e:
        logger.warning(f"⚠️  Face tracking failed: {e}")
        faces = []
    timings["face_tracking"] = round(time.perf_counter() - t_face, 2)

    logger.info(
        f"✅ Analysis complete: probe={bool(probe)}, "
        f"scenes={len(scenes)}, pauses={len(pauses)}, faces={len(faces)}, "
        f"audio={'✓' if audio_path else '✗'}"
    )

    return {
        "probe": probe,
        "scenes": scenes,
        "pauses": pauses,
        "faces": faces,
        "audio_path": audio_path,
        "benchmarks": timings,
    }
