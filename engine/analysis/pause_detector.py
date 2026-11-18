"""
Pause detector — finds silent gaps between words in transcription.
"""
from __future__ import annotations


def detect_pauses(
    word_timestamps: list[dict],
    min_gap: float = 0.3,
) -> list[dict]:
    """
    Detect pauses (silence gaps) between words.
    Args:
        word_timestamps: List of dicts with {word, start, end}.
        min_gap: Minimum gap in seconds to count as a pause.
    Returns:
        List of {start, end, duration} dicts.
    """
    if len(word_timestamps) < 2:
        return []

    pauses: list[dict] = []
    for i in range(1, len(word_timestamps)):
        prev_end = word_timestamps[i - 1].get("end", 0.0)
        curr_start = word_timestamps[i].get("start", 0.0)
        gap = curr_start - prev_end
        if gap >= min_gap:
            pauses.append({
                "start": prev_end,
                "end": curr_start,
                "duration": round(gap, 3),
            })

    return pauses
