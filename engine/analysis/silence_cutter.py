"""
Silence & Conversational Gap Cutter with Smart Jump-Cuts & Retake Detection.
Removes dead air between sentences/words with safety padding, detects false starts/repeats,
and retimes EDL elements (captions, graphics, SFX) to maintain 100% sync.
"""
import os
import re
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


def detect_silence_intervals_ffmpeg(
    audio_path: str,
    noise_threshold_db: float = -32.0,
    min_silence_duration_s: float = 0.35,
) -> List[Tuple[float, float]]:
    """
    Uses FFmpeg's silencedetect filter to find acoustic dead air.
    Returns a list of (start_seconds, end_seconds).
    """
    cmd = [
        "ffmpeg", "-hide_banner", "-vn",
        "-i", str(audio_path),
        "-af", f"silencedetect=noise={noise_threshold_db}dB:d={min_silence_duration_s}",
        "-f", "null", "-"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        stderr = proc.stderr or ""
    except Exception as e:
        logger.warning(f"FFmpeg silencedetect error: {e}")
        return []

    silence_starts = []
    silence_ends = []
    for line in stderr.splitlines():
        if "silence_start:" in line:
            m = re.search(r"silence_start:\s*([0-9.]+)", line)
            if m:
                silence_starts.append(float(m.group(1)))
        elif "silence_end:" in line:
            m = re.search(r"silence_end:\s*([0-9.]+)", line)
            if m:
                silence_ends.append(float(m.group(1)))

    intervals = []
    for s, e in zip(silence_starts, silence_ends):
        if e > s:
            intervals.append((s, e))
    return intervals


def detect_gaps_from_words(
    words: List[Dict[str, Any]],
    min_gap_s: float = 0.35,
    pad_s: float = 0.065,
    total_duration: float = 0.0,
) -> List[Tuple[float, float]]:
    """
    Detects dead air between consecutive spoken words using Whisper word timestamps.
    Applies safety padding (pad_s) so plosives/consonants are never truncated.
    Returns cut intervals: [(cut_start, cut_end), ...]
    """
    if not words:
        return []

    cuts = []
    # Check leading silence before first word
    first_start = float(words[0].get("start", 0.0))
    if first_start > min_gap_s + pad_s:
        cuts.append((0.0, max(0.0, first_start - pad_s)))

    # Gaps between words
    for i in range(len(words) - 1):
        w_curr_end = float(words[i].get("end", 0.0))
        w_next_start = float(words[i + 1].get("start", 0.0))
        raw_gap = w_next_start - w_curr_end

        if raw_gap >= min_gap_s:
            cut_start = w_curr_end + pad_s
            cut_end = w_next_start - pad_s
            if cut_end > cut_start + 0.05:
                cuts.append((round(cut_start, 3), round(cut_end, 3)))

    # Check trailing silence after last word
    if total_duration > 0 and len(words) > 0:
        last_end = float(words[-1].get("end", 0.0))
        if total_duration - last_end > min_gap_s + pad_s:
            cuts.append((round(last_end + pad_s, 3), round(total_duration, 3)))

    return cuts


def detect_false_starts_and_repeats(
    words: List[Dict[str, Any]],
    similarity_window_s: float = 8.0,
    min_ngram: int = 3,
) -> List[Tuple[float, float]]:
    """
    Detects when a speaker stumbles and repeats the same phrase or restart.
    e.g., 'So for this... wait... So for this website you can copy...'
    Identifies the false start range so it can be excised.
    """
    if len(words) < 8:
        return []

    # Build word token list with timestamps
    tokens = [w.get("word", "").lower().strip(".,!?;:\"'") for w in words]
    outtakes = []

    # Check for repeated 3-word or 4-word ngrams within the window
    for n in (4, 3):
        for i in range(len(tokens) - n):
            phrase = tokens[i:i + n]
            if not all(len(p) > 2 for p in phrase):
                continue
            # Look ahead in window
            t_curr = float(words[i].get("start", 0.0))
            for j in range(i + n, min(len(tokens) - n, i + 35)):
                t_future = float(words[j].get("start", 0.0))
                if t_future - t_curr > similarity_window_s:
                    break
                if tokens[j:j + n] == phrase:
                    # Found duplicate phrase! Candidate false start is i..j
                    cut_start = float(words[i].get("start", 0.0))
                    cut_end = float(words[j].get("start", 0.0))
                    if cut_end - cut_start > 0.6:
                        outtakes.append((round(cut_start, 3), round(cut_end, 3)))
                    break

    return outtakes


def compute_keep_segments(
    total_duration: float,
    cut_intervals: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """
    Inverts a list of cut intervals to produce contiguous 'keep' segments.
    Ensures no overlap and enforces a minimum segment duration of 0.2s.
    """
    if not cut_intervals:
        return [(0.0, round(total_duration, 3))]

    # Sort and merge overlapping cuts
    sorted_cuts = sorted(cut_intervals, key=lambda x: x[0])
    merged_cuts = []
    for c in sorted_cuts:
        if not merged_cuts:
            merged_cuts.append(c)
        else:
            prev_s, prev_e = merged_cuts[-1]
            if c[0] <= prev_e:
                merged_cuts[-1] = (prev_s, max(prev_e, c[1]))
            else:
                merged_cuts.append(c)

    keep = []
    cursor = 0.0
    for c_start, c_end in merged_cuts:
        c_start = max(0.0, min(total_duration, c_start))
        c_end = max(0.0, min(total_duration, c_end))
        if c_start > cursor + 0.15:
            keep.append((round(cursor, 3), round(c_start, 3)))
        cursor = max(cursor, c_end)

    if cursor < total_duration - 0.15:
        keep.append((round(cursor, 3), round(total_duration, 3)))

    return keep if keep else [(0.0, round(total_duration, 3))]


def retime_timestamp(t: float, keep_segments: List[Tuple[float, float]]) -> float:
    """
    Maps an original timestamp `t` into the newly shortened timeline after cuts.
    """
    new_t = 0.0
    for s, e in keep_segments:
        if t < s:
            return new_t
        elif s <= t <= e:
            return new_t + (t - s)
        else:
            new_t += (e - s)
    return new_t


def retime_edl(
    edl: Dict[str, Any],
    keep_segments: List[Tuple[float, float]],
) -> Dict[str, Any]:
    """
    Retimes all captions, graphics, sound effects, and zoom events to match
    the new shortened jump-cut timeline.
    """
    new_duration = sum(e - s for s, e in keep_segments)
    retimed_edl = dict(edl)
    retimed_edl["video_duration"] = round(new_duration, 3)

    # Retime captions
    new_captions = []
    for cap in edl.get("captions", []):
        old_s = float(cap.get("start", 0.0))
        old_e = float(cap.get("end", 0.0))
        new_s = retime_timestamp(old_s, keep_segments)
        new_e = retime_timestamp(old_e, keep_segments)
        if new_e > new_s + 0.1:
            c_copy = dict(cap)
            c_copy["start"] = round(new_s, 3)
            c_copy["end"] = round(new_e, 3)
            new_captions.append(c_copy)
    retimed_edl["captions"] = new_captions

    # Retime graphics / stickers / overlays
    new_graphics = []
    for g in edl.get("graphics", []):
        old_s = float(g.get("start", 0.0))
        old_e = float(g.get("end", 0.0))
        new_s = retime_timestamp(old_s, keep_segments)
        new_e = retime_timestamp(old_e, keep_segments)
        if new_e > new_s + 0.2:
            g_copy = dict(g)
            g_copy["start"] = round(new_s, 3)
            g_copy["end"] = round(new_e, 3)
            new_graphics.append(g_copy)
    retimed_edl["graphics"] = new_graphics

    # Retime sound effects
    new_sfx = []
    for s in edl.get("sound_effects", []):
        old_s = float(s.get("start", 0.0))
        new_s = retime_timestamp(old_s, keep_segments)
        s_copy = dict(s)
        s_copy["start"] = round(new_s, 3)
        new_sfx.append(s_copy)
    retimed_edl["sound_effects"] = new_sfx

    # Retime zoom events
    new_zooms = []
    for z in edl.get("zoom_events", []):
        old_s = float(z.get("start", 0.0))
        old_e = float(z.get("end", 0.0))
        new_s = retime_timestamp(old_s, keep_segments)
        new_e = retime_timestamp(old_e, keep_segments)
        if new_e > new_s + 0.2:
            z_copy = dict(z)
            z_copy["start"] = round(new_s, 3)
            z_copy["end"] = round(new_e, 3)
            new_zooms.append(z_copy)
    retimed_edl["zoom_events"] = new_zooms

    return retimed_edl


def build_jump_cut_filtergraph_expr(
    keep_segments: List[Tuple[float, float]],
    source_v_label: str = "0:v",
    source_a_label: str = "0:a",
    out_v_label: str = "v_cut",
    out_a_label: str = "a_cut",
) -> Tuple[str, str]:
    """
    Builds FFmpeg 'select' and 'aselect' expressions that execute instant, sample-accurate
    jump-cuts across all keep segments in a single encoding pass.
    """
    conditions = [f"between(t,{s:.3f},{e:.3f})" for s, e in keep_segments]
    full_cond = "+".join(conditions)

    v_expr = f"[{source_v_label}]select='{full_cond}',setpts=N/FRAME_RATE/TB[{out_v_label}]"
    a_expr = f"[{source_a_label}]aselect='{full_cond}',asetpts=N/SR/TB,aresample=async=1000:first_pts=0[{out_a_label}]"
    return v_expr, a_expr
