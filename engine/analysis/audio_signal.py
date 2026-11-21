"""Signal-level audio analysis for silence and music-like sound candidates."""
from __future__ import annotations

import math
import os
import wave
from pathlib import Path
from typing import Any

import numpy as np


def _merge_ranges(items: list[tuple[float, float]], min_duration: float = 0.0) -> list[dict[str, float]]:
    if not items:
        return []
    items.sort()
    merged: list[list[float]] = []
    for start, end in items:
        if merged and start <= merged[-1][1] + 0.05:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [
        {"start": round(start, 2), "end": round(end, 2), "duration": round(end - start, 2)}
        for start, end in merged
        if end - start >= min_duration
    ]


def analyze_audio_signal(
    audio_path: str | None,
    transcript_words: list[dict[str, Any]] | None = None,
    *,
    silence_threshold_dbfs: float | None = None,
    window_seconds: float = 0.5,
) -> dict[str, Any]:
    """Return bounded silence, speech, and non-speech sound intervals from PCM WAV."""
    unavailable = {
        "available": False,
        "method": "pcm_rms_and_spectral_heuristic",
        "speech_ranges": [],
        "silence_ranges": [],
        "non_speech_audio_ranges": [],
        "music_candidate_ranges": [],
        "music_detection_note": (
            "Music candidates are heuristic and only identify persistent tonal "
            "non-speech audio; music under speech may not be detected."
        ),
    }
    if not audio_path or not Path(audio_path).is_file():
        return {**unavailable, "reason": "audio_unavailable"}

    threshold = silence_threshold_dbfs
    if threshold is None:
        try:
            threshold = float(os.getenv("AURA_SILENCE_THRESHOLD_DBFS", "-45"))
        except ValueError:
            threshold = -45.0
    window_seconds = min(2.0, max(0.1, float(window_seconds)))

    try:
        with wave.open(str(audio_path), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            raw = wav.readframes(wav.getnframes())
        if sample_width != 2 or sample_rate <= 0 or channels <= 0:
            return {**unavailable, "reason": "unsupported_pcm_format"}
        samples = np.frombuffer(raw, dtype="<i2").astype(np.float32)
        if channels > 1:
            samples = samples[: len(samples) - len(samples) % channels].reshape(-1, channels).mean(axis=1)
        samples /= 32768.0
        if samples.size == 0:
            return {**unavailable, "reason": "empty_audio"}
    except (OSError, EOFError, wave.Error, ValueError) as exc:
        return {**unavailable, "reason": f"audio_read_failed:{type(exc).__name__}"}

    words = sorted(
        (
            (max(0.0, float(w.get("start", 0.0))), max(0.0, float(w.get("end", 0.0))))
            for w in (transcript_words or [])
            if float(w.get("end", 0.0)) > float(w.get("start", 0.0))
        ),
        key=lambda item: item[0],
    )
    win_size = max(1, int(sample_rate * window_seconds))
    silence: list[tuple[float, float]] = []
    speech: list[tuple[float, float]] = []
    non_speech: list[tuple[float, float]] = []
    tonal_non_speech: list[tuple[float, float]] = []

    word_index = 0
    for offset in range(0, len(samples), win_size):
        block = samples[offset : min(len(samples), offset + win_size)]
        if not block.size:
            continue
        start = offset / sample_rate
        end = (offset + len(block)) / sample_rate
        rms = float(np.sqrt(np.mean(np.square(block))))
        dbfs = 20.0 * math.log10(max(rms, 1e-8))
        while word_index < len(words) and words[word_index][1] <= start:
            word_index += 1
        scan_index = word_index
        overlaps_speech = False
        while scan_index < len(words) and words[scan_index][0] < end:
            if words[scan_index][1] > start:
                overlaps_speech = True
                break
            scan_index += 1
        if dbfs <= threshold:
            silence.append((start, end))
        elif overlaps_speech:
            speech.append((start, end))
        else:
            non_speech.append((start, end))
            if len(block) >= 128:
                windowed = block * np.hanning(len(block))
                power = np.square(np.abs(np.fft.rfft(windowed)))
                frequencies = np.fft.rfftfreq(len(block), 1 / sample_rate)
                band = power[(frequencies >= 80) & (frequencies <= min(8000, sample_rate / 2))]
                if band.size and float(np.mean(band)) > 1e-10:
                    flatness = float(np.exp(np.mean(np.log(band + 1e-12))) / (np.mean(band) + 1e-12))
                    if flatness < 0.35:
                        tonal_non_speech.append((start, end))

    music_candidates = _merge_ranges(tonal_non_speech, min_duration=2.0)
    return {
        "available": True,
        "duration": round(len(samples) / sample_rate, 2),
        "sample_rate": sample_rate,
        "channels": channels,
        "silence_threshold_dbfs": threshold,
        "analysis_window_seconds": window_seconds,
        "speech_ranges": _merge_ranges(speech),
        "silence_ranges": _merge_ranges(silence, min_duration=0.2),
        "non_speech_audio_ranges": _merge_ranges(non_speech, min_duration=0.2),
        "music_candidate_ranges": music_candidates,
        "music_likelihood": "candidate_detected" if music_candidates else "not_detected_or_uncertain",
        "method": "pcm_rms_and_spectral_heuristic",
        "music_detection_note": (
            "Music candidates are heuristic and only identify persistent tonal "
            "non-speech audio; music under speech may not be detected."
        ),
    }

