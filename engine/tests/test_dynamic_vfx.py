import pytest
from pathlib import Path
from engine.render.dynamic_vfx import (
    detect_dynamic_vfx_intent,
    generate_vfx_overlay_video,
)


def test_detect_dynamic_vfx_intent():
    assert detect_dynamic_vfx_intent(prompt="make it a disco party vibe with lights") == "disco_ball_lights"
    assert detect_dynamic_vfx_intent(prompt="add glitter and magical stars") == "glitter_sparkle"
    assert detect_dynamic_vfx_intent(prompt="fast kinetic speed lines behind elements") == "kinetic_lines"
    assert detect_dynamic_vfx_intent(explicit_vfx="disco_ball_lights") == "disco_ball_lights"
    assert detect_dynamic_vfx_intent(explicit_vfx="none") is None
    assert detect_dynamic_vfx_intent() is None


def test_generate_vfx_overlay_video(tmp_path):
    disco_path = tmp_path / "disco.mp4"
    ok = generate_vfx_overlay_video("disco_ball_lights", disco_path, width=320, height=568, duration=0.5, fps=15)
    assert ok is True
    assert disco_path.exists()
    assert disco_path.stat().st_size > 0

    lines_path = tmp_path / "lines.mp4"
    ok2 = generate_vfx_overlay_video("kinetic_lines", lines_path, width=320, height=568, duration=0.5, fps=15)
    assert ok2 is True
    assert lines_path.exists()
    assert lines_path.stat().st_size > 0

    glitter_path = tmp_path / "glitter.mp4"
    ok3 = generate_vfx_overlay_video("glitter_sparkle", glitter_path, width=320, height=568, duration=0.5, fps=15)
    assert ok3 is True
    assert glitter_path.exists()
    assert glitter_path.stat().st_size > 0
