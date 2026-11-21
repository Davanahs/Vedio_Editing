import pytest
from engine.analysis.silence_cutter import (
    detect_gaps_from_words,
    detect_false_starts_and_repeats,
    compute_keep_segments,
    retime_timestamp,
    retime_edl,
    build_jump_cut_filtergraph_expr,
)


def test_detect_gaps_from_words():
    words = [
        {"word": "Hello", "start": 1.0, "end": 1.5},
        {"word": "world", "start": 2.2, "end": 2.8},  # gap of 0.7s (2.2 - 1.5)
        {"word": "how", "start": 2.9, "end": 3.1},    # gap of 0.1s (normal)
        {"word": "are", "start": 4.5, "end": 4.8},    # gap of 1.4s (4.5 - 3.1)
        {"word": "you", "start": 4.9, "end": 5.2},
    ]
    cuts = detect_gaps_from_words(words, min_gap_s=0.35, pad_s=0.065, total_duration=7.0)
    assert len(cuts) >= 3  # leading silence, gap 1, gap 2, trailing silence
    # Gap 1 cut should be around 1.565 to 2.135
    cut1 = cuts[1]
    assert 1.5 < cut1[0] < 1.6
    assert 2.1 < cut1[1] < 2.2


def test_compute_keep_segments():
    total_dur = 10.0
    cuts = [(1.5, 2.2), (4.0, 5.5)]
    keep = compute_keep_segments(total_dur, cuts)
    assert len(keep) == 3
    assert keep[0] == (0.0, 1.5)
    assert keep[1] == (2.2, 4.0)
    assert keep[2] == (5.5, 10.0)


def test_retime_edl():
    keep_segments = [(0.0, 2.0), (3.0, 5.0)]  # removed 1s (2.0 to 3.0) -> total length 4.0s
    edl = {
        "video_duration": 5.0,
        "captions": [
            {"start": 0.5, "end": 1.5, "keyword": "first"},
            {"start": 3.5, "end": 4.5, "keyword": "second"},  # was at 3.5s -> in segment 2 (after cut of 1.0s), should be at 2.5s
        ],
        "graphics": [
            {"start": 3.2, "end": 4.8, "asset_id": "gamepad"}
        ],
        "sound_effects": [
            {"start": 3.5, "asset_id": "pop"}
        ],
        "zoom_events": []
    }
    retimed = retime_edl(edl, keep_segments)
    assert retimed["video_duration"] == 4.0
    assert retimed["captions"][0]["start"] == 0.5
    assert retimed["captions"][1]["start"] == 2.5
    assert retimed["graphics"][0]["start"] == 2.2
    assert retimed["sound_effects"][0]["start"] == 2.5


def test_build_jump_cut_filtergraph_expr():
    keep = [(0.0, 2.5), (3.5, 6.0)]
    v_expr, a_expr = build_jump_cut_filtergraph_expr(keep)
    assert "between(t,0.000,2.500)" in v_expr
    assert "between(t,3.500,6.000)" in v_expr
    assert "aresample=async=1000" in a_expr
