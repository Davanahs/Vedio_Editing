"""
Test Suite for Creative Template Gallery, SafeZone Collision Detection, and Context-Aware Composer.
"""
import os
import tempfile
from pathlib import Path
import pytest

from engine.templates.definitions import TEMPLATES, get_template
from engine.composer.collision_detector import SafeZoneCollisionEngine, BoundingBox
from engine.analysis.reference_analyzer import analyze_reference_style_image
from engine.render.ffmpeg_reel_builder import generate_ass_subtitles


def test_all_seven_templates_registered():
    """Verify all 7 creative templates are properly defined with creative specs and previews."""
    expected_templates = [
        "pinterest_scrapbook",
        "aesthetic_lifestyle",
        "floating_music_player",
        "glassmorphism",
        "retro_camera",
        "creative_minimal",
        "auto_creative"
    ]
    for tid in expected_templates:
        assert tid in TEMPLATES, f"Template {tid} missing from registry"
        tmpl = get_template(tid)
        assert tmpl.id == tid
        assert tmpl.preview_image.startswith("/template_previews/")
        assert tmpl.creative_spec, f"Template {tid} missing creative_spec"
        assert "element_types" in tmpl.creative_spec
        assert "composition_style" in tmpl.creative_spec
        assert tmpl.color_palette, f"Template {tid} missing color_palette"


def test_preview_images_exist_on_disk():
    """Ensure all template preview image assets exist on disk for the frontend gallery."""
    preview_dir = Path(__file__).resolve().parent.parent / "web" / "template_previews"
    assert preview_dir.exists(), "template_previews directory missing"
    
    for tid in TEMPLATES:
        if tid == "auto_creative":
            img_file = preview_dir / "auto_creative.jpg"
        else:
            img_file = preview_dir / f"{tid}.jpg"
        assert img_file.exists(), f"Preview image missing for {tid}: {img_file}"
        assert img_file.stat().st_size > 500, f"Preview image empty for {tid}"


def test_safe_zone_collision_avoids_face_and_captions():
    """Verify collision detector prevents placing overlays across presenter faces or caption zones."""
    engine = SafeZoneCollisionEngine(
        canvas_w=1080,
        canvas_h=1920,
        face_boxes=[{"x": 300, "y": 300, "w": 480, "h": 600}]
    )

    placement = engine.find_safe_placement(
        element_id="test_badge_1",
        start_t=2.0,
        end_t=5.0,
        width=300,
        height=80
    )

    assert placement is not None, "Failed to find safe placement in margins"
    px, py = placement

    # Verify no intersection with face zone (with padding x in 270..840, y in 270..960)
    badge_box = BoundingBox(x=px, y=py, w=300, h=80)
    face_box = BoundingBox(x=270, y=270, w=540, h=660)
    assert not badge_box.intersects(face_box), f"Badge at ({px}, {py}) collided with presenter face!"

    # Verify not in caption zone (bottom 28% -> y >= 1920 * 0.72 = 1382)
    assert py + 80 <= 1920 * 0.72 + 50, f"Badge at ({px}, {py}) covered lower captions!"


def test_reference_image_analysis():
    """Verify color extraction and style descriptor generation from reference image."""
    preview_path = Path(__file__).resolve().parent.parent / "web" / "template_previews" / "pinterest_scrapbook.jpg"
    result = analyze_reference_style_image(str(preview_path))
    assert result["success"] is True
    assert len(result["palette"]) == 5
    assert "guidance_note" in result
    assert result["style_cue"] == "pinterest_scrapbook"


def test_ass_subtitles_zero_alex_clips_and_dynamic_coords():
    """Verify generated ASS subtitle file never contains fake @alex_clips and honors EDL coordinates."""
    with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as tmp:
        ass_path = tmp.name

    try:
        sample_graphics = [
            {
                "id": "g_gemini_1",
                "asset_id": "gemini",
                "title": "NOTEBOOKLM STUDY",
                "trigger_word": "NOTEBOOKLM",
                "start": 1.5,
                "end": 4.5,
                "x": 120,
                "y": 280
            }
        ]
        sample_captions = [
            {"start": 1.0, "end": 2.5, "lead": "Welcome to", "keyword": "NOTEBOOKLM"}
        ]

        generate_ass_subtitles(
            captions=sample_captions,
            graphics=sample_graphics,
            output_path=ass_path,
            width=1920,
            height=1080,
            hook_title="NOTEBOOKLM STUDY GUIDE",
            social_question="💬 @alex_clips: Have you explored this AI tool yet?",
            template_id="pinterest_scrapbook",
            source_width=1920,
            source_height=1080
        )

        with open(ass_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Strict assertion: @alex_clips MUST be purged
        assert "@alex_clips" not in content, "Fake @alex_clips detected in ASS subtitles!"

        # Dynamic coordinates & animation must be used
        assert "120,280" in content, "Failed to use exact EDL (x, y) coordinates!"
        assert "\\move(" in content, "Failed to apply dynamic motion animation!"

        # Template styling applied
        assert "Georgia" in content, "Failed to apply Pinterest Scrapbook Georgia font style!"
        assert "NOTEBOOKLM STUDY" in content

    finally:
        if os.path.exists(ass_path):
            os.remove(ass_path)
