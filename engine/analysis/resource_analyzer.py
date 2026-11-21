"""Local, privacy-preserving inspection of user-attached creative resources."""
from __future__ import annotations

import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".ogg", ".m4a", ".flac"}


def _resource_path(name: str, resources_dir: Path) -> tuple[Path | None, str | None]:
    candidate = Path(str(name))
    if candidate.name != str(name) or candidate.name in {"", ".", ".."}:
        return None, None
    for category in ("images", "audio", "graphics"):
        path = (resources_dir / category / candidate.name).resolve()
        if path.is_relative_to((resources_dir / category).resolve()) and path.is_file():
            return path, category
    return None, None


def _inspect_svg(path: Path) -> str:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return ""
    parts: list[str] = []
    for node in root.iter():
        local_name = node.tag.rsplit("}", 1)[-1].lower()
        if local_name in {"title", "desc", "text"} and node.text:
            parts.append(node.text.strip())
        for key in ("aria-label", "title", "alt"):
            value = node.attrib.get(key)
            if value:
                parts.append(value.strip())
    return " ".join(dict.fromkeys(parts))[:1200]


def _inspect_image(path: Path) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as image:
        width, height = image.size
        image_format = image.format or path.suffix.lstrip(".").upper()
        description = ""
        for key in ("Description", "ImageDescription", "Title", "Comment"):
            value = image.info.get(key)
            if isinstance(value, str):
                description += " " + value
        description = description.strip()
        try:
            exif = image.getexif()
            for key, value in exif.items():
                if key in (270, 40091) and isinstance(value, str):
                    description += " " + value
        except Exception:
            pass
        preview = image.convert("RGB")
        preview.thumbnail((96, 96))
        quantized = preview.quantize(colors=4).convert("RGB")
        color_counts = sorted(quantized.getcolors(96 * 96) or [], reverse=True)
        dominant = ["#%02x%02x%02x" % tuple(rgb) for _, rgb in color_counts[:4]]
    return {"width": width, "height": height, "format": image_format, "description": description[:800], "dominant_colors": dominant}


def _inspect_audio(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {}
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration:format_tags=title,artist,album,comment", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=8,
        )
        payload = json.loads(result.stdout) if result.returncode == 0 else {}
        fmt = payload.get("format", {})
        tags = fmt.get("tags", {})
        return {"duration": float(fmt.get("duration", 0)), "tags": {str(k): str(v)[:200] for k, v in tags.items()}}
    except Exception:
        return {}


def analyze_attached_resources(names: list[str] | None, resources_dir: str | Path) -> list[dict[str, Any]]:
    """Extract local labels and embedded text/metadata; never uploads resource data."""
    root = Path(resources_dir).resolve()
    results: list[dict[str, Any]] = []
    for name in names or []:
        path, category = _resource_path(str(name), root)
        if path is None:
            results.append({"filename": Path(str(name)).name[:160], "status": "not_found", "evidence": ""})
            continue
        item: dict[str, Any] = {"filename": path.name, "category": category, "status": "inspected", "evidence": ""}
        ext = path.suffix.lower()
        try:
            if ext in IMAGE_EXTENSIONS:
                item.update(_inspect_image(path))
            elif ext == ".svg":
                item["embedded_text"] = _inspect_svg(path)
            elif ext in AUDIO_EXTENSIONS:
                item.update(_inspect_audio(path))
        except Exception as exc:
            item["status"] = "metadata_only"
            item["inspection_error"] = type(exc).__name__
        parts = [path.stem.replace("_", " ").replace("-", " ")]
        for key in ("description", "embedded_text"):
            if item.get(key):
                parts.append(str(item[key]))
        for key, value in item.get("tags", {}).items():
            parts.extend((str(key), str(value)))
        item["evidence"] = " ".join(parts)[:1200]
        results.append(item)
    return results
