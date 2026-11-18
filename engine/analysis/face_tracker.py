"""
Face tracker — samples frames and detects face bounding boxes using MediaPipe.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    import cv2
    import mediapipe as mp
    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False


def track_faces_sampled(
    video_path: str,
    sample_every_n_frames: int = 30,
) -> list[dict]:
    """
    Sample every N frames and detect faces using MediaPipe FaceDetection.
    Args:
        video_path: Path to video file.
        sample_every_n_frames: Sample 1 frame per N frames (e.g. 30 = ~1fps at 30fps).
    Returns:
        List of {frame_time, x, y, width, height, confidence} dicts.
        Returns [] if MediaPipe is unavailable (graceful degradation).
    """
    if not _MP_AVAILABLE:
        logger.warning(
            "MediaPipe/OpenCV not available — face tracking disabled. "
            "Install with: pip install mediapipe>=0.10.0 opencv-python-headless>=4.9.0"
        )
        return []

    results: list[dict] = []

    mp_face = mp.solutions.face_detection  # type: ignore[attr-defined]
    detector = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_every_n_frames == 0:
                frame_time = frame_idx / fps
                # MediaPipe needs RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detection_result = detector.process(rgb)

                if detection_result.detections:
                    h, w = frame.shape[:2]
                    for det in detection_result.detections:
                        bbox = det.location_data.relative_bounding_box
                        results.append({
                            "frame_time": round(frame_time, 3),
                            "x": round(bbox.xmin * w),
                            "y": round(bbox.ymin * h),
                            "width": round(bbox.width * w),
                            "height": round(bbox.height * h),
                            "confidence": round(det.score[0], 3) if det.score else 0.0,
                        })

            frame_idx += 1
    finally:
        cap.release()
        detector.close()

    logger.info(f"Face tracking: {len(results)} detections across {frame_idx} frames")
    return results
