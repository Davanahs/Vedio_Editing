"""Checks for real, documented SVG elements in the creative asset library."""
from pathlib import Path
from types import SimpleNamespace
import subprocess

from fastapi.testclient import TestClient
from engine.assets.registry import AssetRegistry
from engine.render import ffmpeg_reel_builder
from engine.server import app
from engine.analysis.multimodal_synthesizer import _select_contextual_element
from engine.templates.definitions import get_template


def test_vector_assets_have_files_and_usage_metadata():
    registry = AssetRegistry()
    elements_dir = Path(__file__).resolve().parents[1] / "assets" / "elements"
    vector_count = 0

    for asset_id in registry.list_available_stickers():
        metadata = registry.get_asset_metadata(asset_id)
        if metadata.get("type") not in {"svg", "png"}:
            continue
        vector_count += 1
        svg_path = elements_dir / metadata["file"].removeprefix("elements/")
        if metadata.get("type") == "svg":
            assert svg_path.is_file(), f"Missing SVG artwork for {asset_id}"
            assert svg_path.read_text(encoding="utf-8").lstrip().startswith("<svg")
        png_path = svg_path.with_suffix(".png")
        assert png_path.is_file(), f"Missing transparent artwork for {asset_id}"
        from PIL import Image
        with Image.open(png_path) as artwork:
            assert artwork.mode == "RGBA"
            assert artwork.getchannel("A").getextrema()[0] == 0
        assert metadata.get("category")
        assert metadata.get("style")
        assert metadata.get("animation_type")
        assert metadata.get("intended_purpose")

    assert vector_count == 38


def test_reusable_animation_catalog_covers_legacy_and_new_names():
    from engine.render.animations import animation_catalog, get_animation

    assert {entry["name"] for entry in animation_catalog()} == {
        "fade", "scale", "slide", "rotate", "float", "pop", "glitter", "pop_fade"
    }
    assert get_animation("spring_in").kind == "pop"
    assert get_animation("glass_slide").kind == "slide"
    assert get_animation("soft_float").kind == "float"
    assert get_animation("glow_expand").kind == "glitter"


def test_asset_api_serves_every_catalog_image_as_png():
    client = TestClient(app)
    response = client.get("/api/assets")
    assert response.status_code == 200
    elements = response.json()["elements"]
    assert len(elements) == 38
    for element in elements:
        image = client.get(element["preview_url"])
        assert image.status_code == 200, element["id"]
        assert image.headers["content-type"].startswith("image/png"), element["id"]


def test_export_filtergraph_places_vector_art_during_edl_range(tmp_path, monkeypatch):
    commands = []
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source placeholder")
    output = tmp_path / "export.mp4"

    def fake_run(command, **_kwargs):
        if "ffprobe" in command[0]:
            return SimpleNamespace(returncode=0, stdout='{"streams":[{"width":1080,"height":1920}]}', stderr="")
        commands.append(command)
        output.write_bytes(b"render placeholder")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ffmpeg_reel_builder.render_reel_ffmpeg(
        str(source), str(output),
        {
            "video_duration": 5,
            "video_metadata": {"width": 1080, "height": 1920},
            "graphics": [{"asset_id": "sparkle_stars", "start": 1.25, "end": 3.5, "x": 90, "y": 210, "width": 320, "height": 80, "animation": "pop_fade"}],
        },
        aspect_ratio="9:16",
        sfx_dir=str(tmp_path),
    )

    assert result["success"] is True
    command = commands[0]
    filtergraph = command[command.index("-filter_complex") + 1]
    assert "[1:v]" in filtergraph and "format=rgba" in filtergraph
    assert "scale=w=" in filtergraph
    assert "fade=t=in:st=1.250" in filtergraph
    assert "overlay=x='90-(w-" in filtergraph
    assert "':y='210-(h-" in filtergraph
    assert "enable='between(t,1.250,3.500)'" in filtergraph


def test_export_applies_rotation_and_composites_explicit_z_order(tmp_path, monkeypatch):
    commands = []
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source placeholder")
    output = tmp_path / "layered.mp4"

    def fake_run(command, **_kwargs):
        if "ffprobe" in command[0]:
            return SimpleNamespace(returncode=0, stdout='{"streams":[{"width":1920,"height":1080}]}', stderr="")
        commands.append(command)
        output.write_bytes(b"render placeholder")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = ffmpeg_reel_builder.render_reel_ffmpeg(
        str(source), str(output),
        {
            "video_duration": 4,
            "video_metadata": {"width": 1920, "height": 1080},
            "graphics": [
                {"asset_id": "flower_blossom", "start": 1, "end": 3, "x": 300, "y": 180, "width": 180, "height": 180, "rotation": -3, "z_index": 60},
                {"asset_id": "sparkle_stars", "start": 1, "end": 3, "x": 250, "y": 150, "width": 180, "height": 180, "rotation": 0, "z_index": 40},
            ],
        },
        aspect_ratio="16:9",
        sfx_dir=str(tmp_path),
    )

    assert result["success"] is True
    command = commands[0]
    image_inputs = [command[i + 1] for i, value in enumerate(command[:-1]) if value == "-i" and value != command[0]]
    image_inputs = [path for path in image_inputs if path.endswith(".png")]
    assert image_inputs[0].endswith("sparkle_stars.png")
    assert image_inputs[1].endswith("flower_blossom.png")
    filtergraph = command[command.index("-filter_complex") + 1]
    assert "rotate=-0.052360" in filtergraph


def test_ass_does_not_duplicate_rasterized_vector_art(tmp_path):
    ass_path = tmp_path / "graphics.ass"
    ffmpeg_reel_builder.generate_ass_subtitles(
        captions=[],
        graphics=[{"asset_id": "sparkle_stars", "title": "HIGHLIGHT", "start": 1, "end": 3}],
        output_path=str(ass_path),
        width=1080,
        height=1920,
    )
    content = ass_path.read_text(encoding="utf-8")
    assert "HIGHLIGHT" not in content


def test_all_output_ratios_use_intentional_nondistorting_composition(tmp_path, monkeypatch):
    graphs = []
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source placeholder")

    def fake_run(command, **_kwargs):
        if "ffprobe" in command[0]:
            return SimpleNamespace(returncode=0, stdout='{"streams":[{"width":848,"height":474}]}', stderr="")
        graphs.append(command[command.index("-filter_complex") + 1])
        Path(command[-1]).write_bytes(b"render placeholder")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    for ratio in ("9:16", "16:9", "1:1"):
        output = tmp_path / f"{ratio.replace(':', 'x')}.mp4"
        result = ffmpeg_reel_builder.render_reel_ffmpeg(
            str(source), str(output),
            {"video_duration": 1, "video_metadata": {"width": 848, "height": 474}, "graphics": []},
            aspect_ratio=ratio,
            background_mode="blur",
        )
        assert result["success"]

    assert len(graphs) == 3
    for graph in graphs:
        assert "force_original_aspect_ratio=increase" in graph
        assert "boxblur=24:12" in graph
        assert "force_original_aspect_ratio=decrease" in graph
        assert "overlay=(W-w)/2:(H-h)/2" in graph


def test_selected_template_id_controls_ffmpeg_color_treatment(tmp_path, monkeypatch):
    graphs = []
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source placeholder")

    def fake_run(command, **_kwargs):
        if "ffprobe" in command[0]:
            return SimpleNamespace(returncode=0, stdout='{"streams":[{"width":848,"height":474}]}', stderr="")
        graphs.append(command[command.index("-filter_complex") + 1])
        Path(command[-1]).write_bytes(b"render placeholder")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    for template in ("glassmorphism", "retro_camera"):
        result = ffmpeg_reel_builder.render_reel_ffmpeg(
            str(source), str(tmp_path / f"{template}.mp4"),
            {"video_duration": 1, "template_id": template, "video_metadata": {"width": 1920, "height": 1080}, "graphics": []},
            aspect_ratio="16:9", background_mode="fit",
        )
        assert result["success"]

    assert "eq=contrast=1.08:brightness=0.01:saturation=1.18" in graphs[0]
    assert "eq=contrast=1.05:saturation=0.92" in graphs[1]


def test_fill_and_fit_modes_have_explicit_crop_or_padding(tmp_path, monkeypatch):
    graphs = []
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source placeholder")

    def fake_run(command, **_kwargs):
        if "ffprobe" in command[0]:
            return SimpleNamespace(returncode=0, stdout='{"streams":[{"width":848,"height":474}]}', stderr="")
        graphs.append(command[command.index("-filter_complex") + 1])
        Path(command[-1]).write_bytes(b"render placeholder")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    for mode in ("fill", "fit"):
        result = ffmpeg_reel_builder.render_reel_ffmpeg(
            str(source), str(tmp_path / f"{mode}.mp4"),
            {"video_duration": 1, "video_metadata": {"width": 848, "height": 474}, "graphics": []},
            aspect_ratio="9:16", background_mode=mode,
        )
        assert result["success"]

    assert "force_original_aspect_ratio=increase" in graphs[0]
    assert "crop=1080:1920" in graphs[0]
    assert "force_original_aspect_ratio=decrease" in graphs[1]
    assert "pad=1080:1920" in graphs[1]


def test_composite_assets_are_selected_only_with_matching_evidence():
    registry = AssetRegistry()
    music = _select_contextual_element(
        "instrumental track", "music track", set(), get_template("floating_music_player"),
        False, registry, scene_context="music player and headphones",
    )
    retro = _select_contextual_element(
        "the camera is recording", "camera vlog", set(), get_template("retro_camera"),
        False, registry, scene_context="camcorder recording overlay",
    )
    scrapbook = _select_contextual_element(
        "my travel photos", "travel memory", set(), get_template("pinterest_scrapbook"),
        False, registry, scene_context="photo scrapbook paper layer",
    )
    resource_hint = _select_contextual_element(
        "please review this", "", set(), get_template("floating_music_player"),
        False, registry, resource_context="music cover art",
    )
    title_hint = _select_contextual_element(
        "emphasize this takeaway", "key point", set(), get_template("creative_minimal"),
        False, registry, scene_context="main idea title card",
    )

    assert music[0] == "music_player_card"
    assert retro[0] == "retro_recording_hud"
    assert scrapbook[0] == "scrapbook_tape"
    assert resource_hint[0] == "music_player_card"
    assert title_hint[0] == "kinetic_title_card"


def test_asset_retrieval_honors_explicit_exclusions():
    registry = AssetRegistry()
    result = registry.validate_asset_relevance(
        "flower_blossom", topic="outfit", scene_visuals="sunny garden",
        template_id="pinterest_scrapbook", additional_instructions="No flowers, please.",
    )
    assert result["relevant"] is False
    assert "explicitly excluded" in result["reason"]
