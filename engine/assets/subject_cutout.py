"""Person background segmentation and transparent cutout generation.

Uses Google's MediaPipe Selfie Segmenter (TFLite). This is model-based pixel
segmentation; Haar face boxes are not used to infer the body silhouette.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

ASSET_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("AURA_SEGMENTATION_MODEL", str(ASSET_DIR / "models" / "selfie_segmenter.tflite")))
_SEGMENTER = None
_SEGMENTER_LOCK = threading.Lock()


def _get_segmenter():
    global _SEGMENTER
    if _SEGMENTER is not None:
        return _SEGMENTER
    with _SEGMENTER_LOCK:
        if _SEGMENTER is not None:
            return _SEGMENTER
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Selfie segmentation model missing at {MODEL_PATH}. "
                "Run `python -m engine.assets.download_segmentation_model`."
            )
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError("Install project requirements to enable subject cutouts (MediaPipe is missing).") from exc

        options = mp.tasks.vision.ImageSegmenterOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            output_category_mask=True,
            output_confidence_masks=True,
        )
        _SEGMENTER = mp.tasks.vision.ImageSegmenter.create_from_options(options)
        return _SEGMENTER


def _confidence_mask(rgb: np.ndarray) -> np.ndarray:
    import mediapipe as mp

    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
    result = _get_segmenter().segment(image)
    masks = result.confidence_masks or []
    if masks:
        mask = np.asarray(masks[0].numpy_view(), dtype=np.float32)
    elif result.category_mask is not None:
        mask = np.asarray(result.category_mask.numpy_view(), dtype=np.float32)
        mask = (mask > 0).astype(np.float32)
    else:
        raise RuntimeError("Segmentation model returned no mask")
    if mask.ndim == 3:
        mask = mask[..., 0]
    if mask.shape != rgb.shape[:2]:
        mask = cv2.resize(mask, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
    return np.clip(mask, 0.0, 1.0)


def create_subject_cutout(
    image_path: str | Path,
    output_path: str | Path,
    outline_color: Optional[str] = None,
    outline_width: int = 0,
    threshold: float = 0.48,
    edge_softness: float = 0.8,
) -> dict:
    """Segment a person and save an RGBA PNG, optionally with a colored outline."""
    source_path = Path(image_path)
    output = Path(output_path)
    with Image.open(source_path) as source:
        rgb_image = source.convert("RGB")
        if rgb_image.width * rgb_image.height > 24_000_000:
            scale = (24_000_000 / (rgb_image.width * rgb_image.height)) ** 0.5
            rgb_image = rgb_image.resize((round(rgb_image.width * scale), round(rgb_image.height * scale)), Image.Resampling.LANCZOS)
        rgb = np.asarray(rgb_image)

    mask = _confidence_mask(rgb)
    threshold = float(np.clip(threshold, 0.05, 0.95))
    alpha = np.clip((mask - max(0.0, threshold - 0.22)) / 0.22, 0.0, 1.0)
    if edge_softness > 0:
        alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=float(np.clip(edge_softness, 0.1, 3.0)))
    component_count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0.38).astype(np.uint8), 8)
    if component_count > 1:
        component_areas = stats[1:, cv2.CC_STAT_AREA]
        largest_area = int(component_areas.max())
        keep_labels = [index + 1 for index, area in enumerate(component_areas) if area >= max(48, largest_area * 0.02)]
        alpha[~np.isin(labels, keep_labels)] = 0.0
    alpha_u8 = np.round(alpha * 255).astype(np.uint8)
    subject_array = np.dstack([rgb, alpha_u8])

    # Trim transparent margins so the cutout can be positioned and scaled as a
    # foreground graphic instead of carrying the full source-frame rectangle.
    occupied = np.argwhere(alpha_u8 > 24)
    if occupied.size == 0:
        raise ValueError("The segmentation model did not find a confident person in this frame")
    top, left = occupied.min(axis=0)
    bottom, right = occupied.max(axis=0) + 1
    pad_x = max(8, round((right - left) * 0.045))
    pad_y = max(8, round((bottom - top) * 0.045))
    left, right = max(0, left - pad_x), min(subject_array.shape[1], right + pad_x)
    top, bottom = max(0, top - pad_y), min(subject_array.shape[0], bottom + pad_y)
    subject = Image.fromarray(subject_array[top:bottom, left:right], mode="RGBA")
    alpha_cropped = alpha_u8[top:bottom, left:right]

    output.parent.mkdir(parents=True, exist_ok=True)
    if outline_color and int(outline_width) > 0:
        color = outline_color.lstrip("#")
        if len(color) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in color):
            raise ValueError("outline_color must be a six-digit hex color")
        width = max(1, min(64, int(outline_width)))
        foreground = (alpha_cropped > 96).astype(np.uint8) * 255
        kernel_size = width * 2 + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        expanded = cv2.dilate(foreground, kernel)
        ring = cv2.subtract(expanded, foreground)
        r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
        outline = Image.new("RGBA", subject.size, (r, g, b, 0))
        outline.putalpha(Image.fromarray(ring))
        subject = Image.alpha_composite(outline, subject)

    subject.save(output, format="PNG", optimize=True)
    return {
        "output_path": str(output),
        "width": subject.width,
        "height": subject.height,
        "transparent_pixels": int(np.count_nonzero(alpha_u8 < 16)),
        "foreground_coverage": float(np.count_nonzero(alpha_u8 > 128) / alpha_u8.size),
        "model": "MediaPipe Selfie Segmenter 256x256",
    }


def close_segmenter() -> None:
    global _SEGMENTER
    with _SEGMENTER_LOCK:
        if _SEGMENTER is not None:
            _SEGMENTER.close()
            _SEGMENTER = None
