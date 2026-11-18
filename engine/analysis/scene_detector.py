"""
Scene detector — finds scene changes using FFmpeg select filter.
"""
from __future__ import annotations

import asyncio
import re


async def detect_scenes(video_path: str, threshold: float = 0.4) -> list[float]:
    """
    Detect scene changes in a video using FFmpeg.
    Args:
        video_path: Input video path.
        threshold: Scene change sensitivity (0.0–1.0). Higher = fewer scenes detected.
    Returns:
        List of timestamps (in seconds) where scene changes occur.
    """
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-an",
        "-f", "null",
        "-",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    output = stderr.decode(errors="replace")
    timestamps: list[float] = []

    # Extract pts_time values from showinfo output
    # Format: "pts_time:12.345"
    for match in re.finditer(r"pts_time:([\d.]+)", output):
        try:
            timestamps.append(float(match.group(1)))
        except ValueError:
            continue

    timestamps.sort()
    return timestamps
