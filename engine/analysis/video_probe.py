"""
Video probe — extracts metadata from a video file using ffprobe.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path


async def probe_video(video_path: str) -> dict:
    """
    Probe video file and return metadata dict.
    Returns:
        {duration, width, height, fps, rotation, codec, has_audio, file_size}
    """
    video_path = str(video_path)
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        video_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (code {proc.returncode}):\n"
            f"{stderr.decode(errors='replace')}"
        )

    data = json.loads(stdout.decode())
    streams = data.get("streams", [])
    fmt = data.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not video_stream:
        raise RuntimeError("No video stream found in file")

    # Parse FPS (can be "30000/1001" fraction)
    fps_raw = video_stream.get("avg_frame_rate", "30/1")
    try:
        num, den = fps_raw.split("/")
        fps = round(float(num) / float(den), 3)
    except Exception:
        fps = 30.0

    # Rotation from side_data or tags
    rotation = 0
    tags = video_stream.get("tags", {})
    if "rotate" in tags:
        rotation = int(tags["rotate"])
    side_data = video_stream.get("side_data_list", [])
    for sd in side_data:
        if sd.get("side_data_type") == "Display Matrix":
            rotation = sd.get("rotation", 0)
            break

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))

    # Swap if rotated 90/270
    if abs(rotation) in (90, 270):
        width, height = height, width

    duration = float(fmt.get("duration", video_stream.get("duration", 0)))
    file_size = int(fmt.get("size", Path(video_path).stat().st_size))

    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "rotation": rotation,
        "codec": video_stream.get("codec_name", "unknown"),
        "has_audio": audio_stream is not None,
        "file_size": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
    }
