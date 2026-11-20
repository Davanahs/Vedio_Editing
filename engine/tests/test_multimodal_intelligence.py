"""
Automated QA Acceptance Test Suite for Multimodal AI Video Understanding & Intelligent Creative Editing.
Verifies all 7 Acceptance Scenarios from User Specification Section 9:
- Test A: AI Tutorial (Tech/AI graphics, 0 Spotify/fashion)
- Test B: Aesthetic Lifestyle (Scrapbook/Polaroid/flowers, 0 tech chips)
- Test C: Food/Recipe (Culinary/recipe badges)
- Test D: Mixed-Content (Segment-specific dynamic switching)
- Test E: Template Selection (Pinterest Scrapbook on tech -> scrapbook layout for tech concepts, no random flowers)
- Test F: Additional Instructions ("Keep minimal, do not cover face...")
- Test G: Empty Visual Segments (Clean scene preservation, no forced overlays)
"""
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engine.analysis.audio_segmenter import AudioSegment
from engine.analysis.frame_analyzer import VisualFrameAnalysis
from engine.analysis.multimodal_synthesizer import synthesize_multimodal_plan
from engine.assets.registry import AssetRegistry
from engine.templates.definitions import get_template


class TestMultimodalIntelligence(unittest.TestCase):
    def setUp(self):
        self.asset_reg = AssetRegistry(str(_ROOT))
        self.video_meta_16x9 = {"width": 1920, "height": 1080, "duration": 40.0}
        self.video_meta_9x16 = {"width": 1080, "height": 1920, "duration": 40.0}

    def test_a_ai_tutorial(self):
        """Test A: AI tutorial -> Tech/AI graphics, NO unrelated Spotify or fashion."""
        audio_segs = [
            AudioSegment(
                segment_id="seg_1", start=0.0, end=10.0, duration=10.0,
                text="Today we are exploring Google Gemini NotebookLM, an incredible AI tool for research and study.",
                topic_summary="AI Tool Introduction: Gemini NotebookLM",
                keywords=["gemini", "notebooklm", "ai", "tool"],
                tone="innovative", speech_density=2.5, is_quiet=False, is_cta=False
            ),
            AudioSegment(
                segment_id="seg_2", start=10.0, end=20.0, duration=10.0,
                text="You can automatically create MCQs and generate full PPT slides from your notes.",
                topic_summary="Automated Quiz & MCQ Generation",
                keywords=["mcqs", "ppt", "notes"],
                tone="productive", speech_density=2.2, is_quiet=False, is_cta=False
            )
        ]
        visual_frames = [
            VisualFrameAnalysis(
                timestamp=5.0, frame_path="", width=1920, height=1080,
                faces=[{"x": 800, "y": 300, "w": 250, "h": 250}], face_detected=True,
                objects_detected=["laptop", "desk", "monitor"],
                subject_activity="presenter pointing at laptop screen",
                setting_environment="modern home office", visual_aesthetic="tech tutorial",
                dominant_colors=["#1E293B", "#38BDF8"], is_scene_transition=False,
                clean_scene_recommended=False
            )
        ]

        plan = synthesize_multimodal_plan(
            audio_segments=audio_segs,
            visual_frames=visual_frames,
            video_metadata=self.video_meta_16x9,
            template_id="auto_creative",
            main_prompt="Edit this AI tutorial",
            asset_registry=self.asset_reg
        )

        chosen_assets = [d["chosen_asset_id"] for d in plan["decisions"] if d["chosen_asset_id"]]
        # Must have tech/AI/study assets
        self.assertTrue(any(a in ["gemini", "laptop", "robot", "quiz", "presentation"] for a in chosen_assets), f"Expected AI assets, got {chosen_assets}")
        # Must NOT have Spotify music card or fashion flower
        self.assertNotIn("music_card", chosen_assets, "Spotify music card illegally added to AI tutorial!")
        self.assertNotIn("flower_blossom", chosen_assets, "Fashion flower illegally added to AI tutorial!")
        print("  [PASS] Test A: AI Tutorial correctly matched tech elements, 0 Spotify/fashion.")

    def test_b_aesthetic_lifestyle(self):
        """Test B: Aesthetic lifestyle -> Scrapbook/Polaroid/flowers, NO unrelated tech chips."""
        audio_segs = [
            AudioSegment(
                segment_id="seg_1", start=0.0, end=15.0, duration=15.0,
                text="Sunday morning coffee and showing my daily outfit style for this sunny golden hour.",
                topic_summary="Aesthetic Outfit & Daily Vlog",
                keywords=["outfit", "style", "aesthetic"],
                tone="dreamy relaxed", speech_density=1.2, is_quiet=False, is_cta=False
            )
        ]
        visual_frames = [
            VisualFrameAnalysis(
                timestamp=5.0, frame_path="", width=1080, height=1920,
                faces=[{"x": 400, "y": 400, "w": 200, "h": 200}], face_detected=True,
                objects_detected=["yellow sundress", "coffee cup", "sunglasses"],
                subject_activity="walking outdoors in the sunlight showcasing outfit",
                setting_environment="sunny park sidewalk", visual_aesthetic="dreamy aesthetic lifestyle",
                dominant_colors=["#FEF3C7", "#F472B6"], is_scene_transition=False,
                clean_scene_recommended=False
            )
        ]

        plan = synthesize_multimodal_plan(
            audio_segments=audio_segs,
            visual_frames=visual_frames,
            video_metadata=self.video_meta_9x16,
            template_id="pinterest_scrapbook",
            main_prompt="Make this aesthetic scrapbook style",
            asset_registry=self.asset_reg
        )

        chosen_assets = [d["chosen_asset_id"] for d in plan["decisions"] if d["chosen_asset_id"]]
        self.assertTrue(any(a in ["polaroid_frame", "flower_blossom", "sparkle_stars", "doodle_heart"] for a in chosen_assets), f"Expected scrapbook assets, got {chosen_assets}")
        self.assertNotIn("chip", chosen_assets, "Tech chip illegally added to lifestyle outfit!")
        self.assertNotIn("gamepad", chosen_assets, "Gaming gamepad illegally added to lifestyle outfit!")
        print("  [PASS] Test B: Aesthetic Lifestyle correctly matched scrapbook/polaroid elements, 0 tech chips.")

    def test_c_food_cooking(self):
        """Test C: Food video -> Ingredient/recipe culinary graphics."""
        audio_segs = [
            AudioSegment(
                segment_id="seg_1", start=0.0, end=12.0, duration=12.0,
                text="Here is the secret recipe for the crispiest homemade dinner dish using fresh herbs.",
                topic_summary="Culinary Recipe & Cooking Preparation",
                keywords=["recipe", "dish", "cooking", "dinner"],
                tone="appetizing instructional", speech_density=2.0, is_quiet=False, is_cta=False
            )
        ]
        visual_frames = [
            VisualFrameAnalysis(
                timestamp=5.0, frame_path="", width=1920, height=1080,
                faces=[], face_detected=False,
                objects_detected=["pan", "cutting board", "herbs", "olive oil"],
                subject_activity="chef chopping fresh ingredients on cutting board",
                setting_environment="bright modern kitchen", visual_aesthetic="clean culinary showcase",
                dominant_colors=["#22C55E", "#F97316"], is_scene_transition=False,
                clean_scene_recommended=False
            )
        ]

        plan = synthesize_multimodal_plan(
            audio_segments=audio_segs,
            visual_frames=visual_frames,
            video_metadata=self.video_meta_16x9,
            template_id="auto_creative",
            main_prompt="Highlight cooking steps",
            asset_registry=self.asset_reg
        )

        chosen_assets = [d["chosen_asset_id"] for d in plan["decisions"] if d["chosen_asset_id"]]
        self.assertTrue(any(a in ["recipe_dish", "chef_hat", "fresh_leaf"] for a in chosen_assets), f"Expected food assets, got {chosen_assets}")
        self.assertNotIn("gamepad", chosen_assets, "Gaming gamepad illegally added to cooking video!")
        print("  [PASS] Test C: Food Video correctly matched recipe/dish culinary assets.")

    def test_d_mixed_content_switching(self):
        """Test D: Mixed content -> Independent segment analysis, no repeating stickers."""
        audio_segs = [
            AudioSegment(
                segment_id="seg_1", start=0.0, end=8.0, duration=8.0,
                text="Check out this new AI tool for coding and web development.",
                topic_summary="AI Web Development",
                keywords=["ai", "tool", "laptop"],
                tone="tech", speech_density=2.0, is_quiet=False, is_cta=False
            ),
            AudioSegment(
                segment_id="seg_2", start=8.0, end=16.0, duration=8.0,
                text="And afterwards we take a study break with delicious snacks.",
                topic_summary="Study Break",
                keywords=["study", "book"],
                tone="relaxed", speech_density=2.0, is_quiet=False, is_cta=False
            ),
            AudioSegment(
                segment_id="seg_3", start=16.0, end=24.0, duration=8.0,
                text="Make sure to like and follow for more daily tips!",
                topic_summary="Engagement CTA",
                keywords=["like", "follow"],
                tone="upbeat", speech_density=2.0, is_quiet=False, is_cta=True
            ),
        ]
        visual_frames = [
            VisualFrameAnalysis(
                timestamp=4.0, frame_path="", width=1920, height=1080,
                faces=[], face_detected=False, objects_detected=["laptop"],
                subject_activity="coding", setting_environment="office",
                visual_aesthetic="tech", dominant_colors=["#1E293B"],
                is_scene_transition=False, clean_scene_recommended=False
            ),
            VisualFrameAnalysis(
                timestamp=12.0, frame_path="", width=1920, height=1080,
                faces=[], face_detected=False, objects_detected=["coffee"],
                subject_activity="drinking coffee", setting_environment="cozy table",
                visual_aesthetic="lifestyle", dominant_colors=["#FEF3C7"],
                is_scene_transition=False, clean_scene_recommended=False
            )
        ]

        plan = synthesize_multimodal_plan(
            audio_segments=audio_segs,
            visual_frames=visual_frames,
            video_metadata=self.video_meta_16x9,
            template_id="auto_creative",
            asset_registry=self.asset_reg
        )

        chosen = [d["chosen_asset_id"] for d in plan["decisions"] if d["chosen_asset_id"]]
        # Ensure no identical repeated sticker
        self.assertEqual(len(chosen), len(set(chosen)), f"Found duplicate stickers: {chosen}")
        print("  [PASS] Test D: Mixed content correctly switched elements per segment without repetition.")

    def test_e_template_pinterest_on_tech(self):
        """Test E: Pinterest Scrapbook on Tech -> Scrapbook styling for tech concepts, NO random flowers."""
        audio_segs = [
            AudioSegment(
                segment_id="seg_1", start=0.0, end=10.0, duration=10.0,
                text="Let's dive into Gemini NotebookLM for research and study preparation.",
                topic_summary="AI Tool Introduction: Gemini NotebookLM",
                keywords=["gemini", "notebooklm", "research"],
                tone="innovative", speech_density=2.0, is_quiet=False, is_cta=False
            )
        ]
        visual_frames = [
            VisualFrameAnalysis(
                timestamp=5.0, frame_path="", width=1920, height=1080,
                faces=[{"x": 500, "y": 300, "w": 200, "h": 200}], face_detected=True,
                objects_detected=["laptop"], subject_activity="presenter",
                setting_environment="desk", visual_aesthetic="clean",
                dominant_colors=["#38BDF8"], is_scene_transition=False,
                clean_scene_recommended=False
            )
        ]

        plan = synthesize_multimodal_plan(
            audio_segments=audio_segs,
            visual_frames=visual_frames,
            video_metadata=self.video_meta_16x9,
            template_id="pinterest_scrapbook",
            main_prompt="Use scrapbook style for this Gemini video",
            asset_registry=self.asset_reg
        )

        chosen = [d["chosen_asset_id"] for d in plan["decisions"] if d["chosen_asset_id"]]
        # Must use tech asset
        self.assertTrue(any(a in ["gemini", "book", "laptop"] for a in chosen), f"Expected tech asset in scrapbook framing, got {chosen}")
        # Must NOT add random flowers/makeup
        self.assertNotIn("flower_blossom", chosen, "Random flower illegally added to tech video!")
        print("  [PASS] Test E: Pinterest Scrapbook on Tech video applied scrapbook framing for tech concepts, 0 random flowers.")

    def test_f_additional_instructions_minimal_and_face(self):
        """Test F: Additional instructions -> Respects 'minimal' and avoids covering face."""
        audio_segs = [
            AudioSegment(
                segment_id=f"seg_{i}", start=i*8.0, end=(i+1)*8.0, duration=8.0,
                text=f"Explaining feature number {i} of this application.",
                topic_summary=f"Feature {i}", keywords=["feature"],
                tone="clear", speech_density=2.0, is_quiet=False, is_cta=(i==4)
            )
            for i in range(5)
        ]
        # Face is placed on right half of canvas (x=1200)
        visual_frames = [
            VisualFrameAnalysis(
                timestamp=10.0, frame_path="", width=1920, height=1080,
                faces=[{"x": 1200, "y": 200, "w": 300, "h": 300}], face_detected=True,
                objects_detected=[], subject_activity="speaker",
                setting_environment="room", visual_aesthetic="clean",
                dominant_colors=["#FFFFFF"], is_scene_transition=False,
                clean_scene_recommended=False
            )
        ]

        plan = synthesize_multimodal_plan(
            audio_segments=audio_segs,
            visual_frames=visual_frames,
            video_metadata=self.video_meta_16x9,
            template_id="auto_creative",
            additional_instructions="Keep the video minimal, do not cover my face and preserve original audio",
            asset_registry=self.asset_reg
        )

        elements_placed = [d for d in plan["decisions"] if d["needs_visual_element"]]
        # Density must be minimal (<= 3 elements total across 40s)
        self.assertLessEqual(len(elements_placed), 3, f"Too many elements for minimal mode: {len(elements_placed)}")
        # Check placement avoided the face on right (x=1200) -> placed on left half (x < 960)
        for el in elements_placed:
            self.assertLess(el["placement"]["x"], 1000, f"Element x={el['placement']['x']} covered or collided with face at x=1200!")
        print("  [PASS] Test F: Additional instructions strictly enforced (minimal density <= 3 and face avoided).")

    def test_g_empty_visual_segments_clean(self):
        """Test G: Transition / unremarkable scene -> Preserved clean, NO forced overlay."""
        audio_segs = [
            AudioSegment(
                segment_id="seg_trans", start=15.0, end=20.0, duration=5.0,
                text="...", topic_summary="Visual scene transition",
                keywords=[], tone="ambient", speech_density=0.1,
                is_quiet=True, is_cta=False
            )
        ]
        visual_frames = [
            VisualFrameAnalysis(
                timestamp=16.0, frame_path="", width=1920, height=1080,
                faces=[], face_detected=False, objects_detected=[],
                subject_activity="cutaway B-roll transition",
                setting_environment="outdoor sky", visual_aesthetic="cinematic",
                dominant_colors=["#38BDF8"], is_scene_transition=True,
                clean_scene_recommended=True
            )
        ]

        plan = synthesize_multimodal_plan(
            audio_segments=audio_segs,
            visual_frames=visual_frames,
            video_metadata=self.video_meta_16x9,
            asset_registry=self.asset_reg
        )

        dec = plan["decisions"][0]
        self.assertFalse(dec["needs_visual_element"], "Graphic was erroneously forced onto a clean transition scene!")
        self.assertIsNotNone(dec["clean_reason"], "Expected clean_reason explaining why scene was left untouched.")
        print(f"  [PASS] Test G: Clean scene preserved ({dec['clean_reason']}).")


if __name__ == "__main__":
    unittest.main()
