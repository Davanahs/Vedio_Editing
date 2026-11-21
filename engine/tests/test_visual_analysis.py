import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from PIL import Image

from engine.analysis.frame_analyzer import (
    VisualFrameAnalysis,
    _analyze_single_frame,
    _parse_visual_observation,
    _select_frame_samples,
)


class TestVisualAnalysis(unittest.TestCase):
    def test_parses_provider_json_and_rejects_invalid_response(self):
        observation = _parse_visual_observation(json.dumps({
            "objects": ["person", "laptop"],
            "subject_activity": "speaking to camera",
            "setting": "home office",
            "visual_aesthetic": "tutorial",
            "dominant_colors": ["#112233"],
            "visual_summary": "A presenter sits beside a laptop.",
            "spoken_topics": ["study workflow"],
            "mentioned_entities": ["NotebookLM"],
            "is_visually_cluttered": False,
            "leave_clean": False,
        }))
        self.assertEqual(observation.objects, ["person", "laptop"])
        self.assertEqual(observation.mentioned_entities, ["NotebookLM"])
        with self.assertRaises(Exception):
            _parse_visual_observation("not json")

    def test_frame_sample_limit_is_deterministic_and_requires_files(self):
        samples = []
        for index in range(10):
            temporary = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temporary.close()
            path = Path(temporary.name)
            Image.new("RGB", (16, 16), (index, 20, 30)).save(path)
            self.addCleanup(path.unlink, missing_ok=True)
            samples.append((float(index), str(path), index % 2 == 0))
        selected = _select_frame_samples(samples, 4)
        self.assertEqual(len(selected), 4)
        self.assertEqual(selected, _select_frame_samples(samples, 4))
        self.assertEqual(selected[0][0], 0.0)
        self.assertEqual(selected[-1][0], 9.0)

    def test_face_positions_are_normalized_and_provider_provenance_is_exposed(self):
        frame = VisualFrameAnalysis(
            timestamp=2.0, frame_path="", width=100, height=200,
            faces=[{"x": 25, "y": 50, "w": 30, "h": 40}],
            face_detected=True, objects_detected=["person"],
            subject_activity="standing", setting_environment="room",
            visual_aesthetic="vlog", dominant_colors=["#000000"],
            is_scene_transition=False, clean_scene_recommended=False,
            analysis_provider="openrouter", analysis_model="openrouter/free",
            analysis_status="model",
        ).to_dict()
        self.assertEqual(frame["normalized_faces"][0], {"x": 0.25, "y": 0.25, "w": 0.3, "h": 0.2})
        self.assertEqual(frame["analysis_provider"], "openrouter")
        self.assertEqual(frame["analysis_status"], "model")

    def test_provider_failure_falls_back_with_provenance(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temporary.close()
        path = Path(temporary.name)
        Image.new("RGB", (64, 64), (40, 50, 60)).save(path)
        self.addCleanup(path.unlink, missing_ok=True)
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "GEMINI_API_KEY": ""}, clear=False):
            with patch("engine.analysis.frame_analyzer._call_openrouter_vision", new=AsyncMock(side_effect=TimeoutError)):
                result = asyncio.run(_analyze_single_frame(1.0, str(path), False, "demo"))
        self.assertEqual(result.analysis_status, "heuristic")
        self.assertIn("openrouter:TimeoutError", result.fallback_reason)


if __name__ == "__main__":
    unittest.main()
