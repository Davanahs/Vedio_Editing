"""
Audio extractor — pulls mono 16kHz WAV from video using FFmpeg.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path


async def extract_audio(video_path: str, output_path: str | None = None) -> str:
    """
    Extract mono 16kHz PCM WAV from video.
    Args:
        video_path: Input video file path.
        output_path: Output WAV path. Defaults to same dir as video with .wav extension.
    Returns:
        Path to output WAV file.
    """
    video_path = str(video_path)
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if output_path is None:
        stem = Path(video_path).stem
        output_path = str(Path(video_path).parent / f"{stem}_audio.wav")

    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",                      # overwrite
        "-i", video_path,
        "-vn",                     # no video
        "-acodec", "pcm_s16le",    # 16-bit PCM
        "-ar", "16000",            # 16kHz sample rate
        "-ac", "1",                # mono
        output_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg audio extraction failed (code {proc.returncode}):\n"
            f"{stderr.decode(errors='replace')}"
        )

    if not Path(output_path).exists():
        raise RuntimeError(f"FFmpeg ran but output not found: {output_path}")

    size_kb = Path(output_path).stat().st_size // 1024
    return output_path
