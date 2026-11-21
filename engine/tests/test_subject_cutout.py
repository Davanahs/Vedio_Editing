from pathlib import Path

import numpy as np
from PIL import Image

from engine.assets import subject_cutout


def test_cutout_writes_transparency_and_optional_outline(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    output = tmp_path / "cutout.png"
    Image.new("RGB", (120, 100), (20, 80, 160)).save(source)
    mask = np.zeros((100, 120), dtype=np.float32)
    mask[20:82, 42:78] = 0.98
    mask[4:8, 8:12] = 0.99  # detached false-positive speck is discarded
    monkeypatch.setattr(subject_cutout, "_confidence_mask", lambda _rgb: mask)

    stats = subject_cutout.create_subject_cutout(source, output, "#FFFFFF", 5)

    cutout = Image.open(output).convert("RGBA")
    alpha = np.asarray(cutout)[:, :, 3]
    assert stats["width"] < 65 and stats["height"] < 100
    assert np.any(alpha == 0)
    assert np.any(alpha > 128)
    assert np.any((alpha > 0) & (alpha < 255))
    assert np.any((np.asarray(cutout)[:, :, :3] == 255).all(axis=2) & (alpha > 0))


def test_subject_cutout_requires_model_artifact(tmp_path, monkeypatch):
    missing_model = tmp_path / "missing.tflite"
    monkeypatch.setattr(subject_cutout, "MODEL_PATH", missing_model)
    monkeypatch.setattr(subject_cutout, "_SEGMENTER", None)
    try:
        subject_cutout._get_segmenter()
    except FileNotFoundError as error:
        assert "download_segmentation_model" in str(error)
    else:
        raise AssertionError("Missing segmentation model must be reported")


def test_colored_outline_uses_requested_hex_color(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    output = tmp_path / "colored.png"
    Image.new("RGB", (80, 80), (10, 20, 30)).save(source)
    mask = np.zeros((80, 80), dtype=np.float32)
    mask[18:62, 22:58] = 0.99
    monkeypatch.setattr(subject_cutout, "_confidence_mask", lambda _rgb: mask)

    subject_cutout.create_subject_cutout(source, output, "#12ABEF", 4)
    pixels = np.asarray(Image.open(output).convert("RGBA"))
    color_match = (pixels[:, :, 0] == 0x12) & (pixels[:, :, 1] == 0xAB) & (pixels[:, :, 2] == 0xEF)
    assert np.any(color_match & (pixels[:, :, 3] > 0))
