"""Fetch the pinned Apache-2.0 MediaPipe Selfie Segmenter model artifact."""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

MODEL_URL = "https://huggingface.co/litert-community/MediaPipe-ImageSegmenter-Selfie-Square/resolve/main/selfie_segmenter.tflite"
MODEL_SHA256 = "191ac9529ae506ee0beefa6b2c945a172dab9d07d1e802a290a4e4038226658b"
DESTINATION = Path(__file__).resolve().parent / "models" / "selfie_segmenter.tflite"


def main() -> None:
    if DESTINATION.exists() and hashlib.sha256(DESTINATION.read_bytes()).hexdigest() == MODEL_SHA256:
        print(f"Model already verified: {DESTINATION}")
        return
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(MODEL_URL, headers={"User-Agent": "AuraCreativeStudio/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != MODEL_SHA256:
        raise RuntimeError(f"Downloaded model SHA-256 mismatch: {digest}")
    DESTINATION.write_bytes(payload)
    print(f"Verified model saved: {DESTINATION} ({len(payload)} bytes)")


if __name__ == "__main__":
    main()
