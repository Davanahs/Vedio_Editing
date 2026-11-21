import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from engine.analysis.audio_signal import analyze_audio_signal


class TestAudioSignalAnalysis(unittest.TestCase):
    def _write_wav(self, samples: np.ndarray) -> str:
        temporary = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(np.asarray(samples * 32767, dtype="<i2").tobytes())
        self.addCleanup(path.unlink, missing_ok=True)
        return str(path)

    def test_detects_silence_and_music_candidate_without_transcript(self):
        rate = 16000
        time_axis = np.arange(rate * 2) / rate
        tone = 0.2 * np.sin(2 * np.pi * 440 * time_axis)
        samples = np.concatenate([tone, np.zeros(rate * 2)])
        result = analyze_audio_signal(self._write_wav(samples), [])
        self.assertTrue(result["available"])
        self.assertTrue(result["silence_ranges"])
        self.assertTrue(result["music_candidate_ranges"])
        self.assertIn("heuristic", result["method"])

    def test_marks_transcript_word_overlap_as_speech(self):
        rate = 16000
        samples = 0.12 * np.sin(2 * np.pi * 170 * np.arange(rate * 2) / rate)
        result = analyze_audio_signal(
            self._write_wav(samples),
            [{"word": "hello", "start": 0.2, "end": 1.2}],
        )
        self.assertTrue(result["speech_ranges"])
        self.assertFalse(result["silence_ranges"])

    def test_missing_audio_is_a_structured_nonfatal_result(self):
        result = analyze_audio_signal(None, [])
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "audio_unavailable")


if __name__ == "__main__":
    unittest.main()
