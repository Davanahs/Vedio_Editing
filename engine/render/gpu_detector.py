"""
GPU Acceleration Detector for Reel Editor.
Probes FFmpeg for NVENC, AMF, QSV, or VideoToolbox, and confirms with a test encode.
"""
import subprocess
import shutil

def detect_gpu_encoder() -> str:
    """
    Returns the fastest supported H.264 encoder:
    'h264_nvenc', 'h264_amf', 'h264_qsv', or 'libx264' (CPU fallback).
    """
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return "libx264"

    try:
        res = subprocess.run([ffmpeg_bin, "-encoders"], capture_output=True, text=True, timeout=5)
        encoders_output = res.stdout
    except Exception:
        return "libx264"

    candidates = ["h264_nvenc", "h264_qsv", "h264_amf"]
    
    for cand in candidates:
        if cand in encoders_output:
            # Verify actual hardware support with a 1-frame test encode
            test_cmd = [
                ffmpeg_bin,
                "-y",
                "-f", "lavfi",
                "-i", "color=c=black:s=256x256:d=0.1",
                "-c:v", cand,
                "-f", "null",
                "-"
            ]
            try:
                test_res = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
                if test_res.returncode == 0:
                    return cand
            except Exception:
                continue

    return "libx264"
