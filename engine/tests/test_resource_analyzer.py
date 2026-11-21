from pathlib import Path

from PIL import Image

from engine.analysis.resource_analyzer import analyze_attached_resources
from fastapi.testclient import TestClient
from engine import server


def test_resource_analysis_extracts_local_image_and_svg_content(tmp_path):
    image_dir = tmp_path / "images"
    graphic_dir = tmp_path / "graphics"
    image_dir.mkdir()
    graphic_dir.mkdir()
    Image.new("RGB", (64, 40), (240, 30, 20)).save(image_dir / "red_product_photo.png")
    (graphic_dir / "brand_card.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" aria-label="Blue brand card"><title>Blue Harbor</title><text>Summer collection</text></svg>',
        encoding="utf-8",
    )

    results = analyze_attached_resources(["red_product_photo.png", "brand_card.svg"], tmp_path)

    assert results[0]["status"] == "inspected"
    assert results[0]["width"] == 64 and results[0]["height"] == 40
    assert results[0]["dominant_colors"]
    assert "red product photo" in results[0]["evidence"]
    assert "Blue Harbor" in results[1]["evidence"]
    assert "Summer collection" in results[1]["evidence"]


def test_resource_analysis_rejects_path_traversal(tmp_path):
    result = analyze_attached_resources(["..\\private.png"], tmp_path)
    assert result[0]["status"] == "not_found"
    assert "private.png" in result[0]["filename"]


def test_resource_catalog_hides_placeholders_and_unsupported_files(tmp_path, monkeypatch):
    images = tmp_path / "images"
    graphics = tmp_path / "graphics"
    images.mkdir()
    graphics.mkdir()
    (images / ".gitkeep").write_text("", encoding="utf-8")
    (images / "notes.txt").write_text("not an image", encoding="utf-8")
    (images / "cover.png").write_bytes(b"png placeholder")
    (graphics / ".gitkeep").write_text("", encoding="utf-8")
    monkeypatch.setattr(server, "RESOURCES_DIR", tmp_path)

    response = TestClient(server.app).get("/api/resources")

    assert response.status_code == 200
    assert [item["filename"] for item in response.json()["resources"]] == ["cover.png"]
