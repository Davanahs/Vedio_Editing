from engine.composer.collision_detector import BoundingBox, SafeZoneCollisionEngine
from engine.director.edl_schema import EditDecisionList
from engine.director.validator import apply_plan_composition, validate_edl
from engine.analysis.multimodal_synthesizer import _build_composition_layers
from engine.assets.registry import AssetRegistry


def test_frame_local_faces_only_block_overlays_near_the_observed_time():
    engine = SafeZoneCollisionEngine(
        canvas_w=1920,
        canvas_h=1080,
        face_boxes=[{"x": 1200, "y": 220, "w": 300, "h": 300, "start": 9, "end": 11}],
    )
    off_scene = engine.find_safe_placement("early", 1, 2, 240, 120, "right")
    near_face_time = engine.find_safe_placement("later", 9.5, 10.5, 240, 120, "right")

    assert off_scene is not None and off_scene[0] >= 1000
    assert near_face_time is not None
    candidate = BoundingBox(*near_face_time, 240, 120)
    observed_face = BoundingBox(1170, 190, 360, 360)
    assert not candidate.intersects(observed_face, padding=25)


def test_edl_validation_clamps_graphics_to_requested_canvas_and_keeps_layers():
    edl = EditDecisionList(
        video_duration=10,
        graphics=[{
            "id": "g1", "asset_id": "sparkle_stars", "start": 8, "end": 12,
            "x": 1850, "y": 1000, "width": 300, "height": 160,
            "z_index": 65, "rotation": -3,
        }],
    )

    cleaned = validate_edl(edl, {"sparkle_stars"}, set(), canvas_width=1920, canvas_height=1080)
    graphic = cleaned.graphics[0]

    assert (graphic.x, graphic.y) == (1620, 920)
    assert (graphic.width, graphic.height, graphic.end) == (300, 160, 10)
    assert graphic.z_index == 65
    assert graphic.rotation == -3


def test_director_output_inherits_safe_geometry_from_validated_plan():
    edl = EditDecisionList(
        video_duration=10,
        graphics=[{
            "id": "g_flower", "asset_id": "flower_blossom", "start": 2, "end": 4,
            "x": 900, "y": 600, "width": 320, "height": 80, "animation": "spring_in",
        }],
    )
    plan = {"decisions": [{
        "needs_visual_element": True,
        "chosen_asset_id": "flower_blossom",
        "start": 2.2,
        "end": 3.8,
        "animation": "float",
        "placement": {"x": 120, "y": 250, "width": 180, "height": 180, "rotation": 3, "z_index": 60},
        "composition_layers": [{
            "asset_id": "scrapbook_tape", "x": 220, "y": 260,
            "width": 104, "height": 64, "z_index": 70, "rotation": -2,
            "animation": "pop_fade",
        }],
    }]}

    composed = apply_plan_composition(edl, plan)
    result = composed.graphics[0]

    assert (result.start, result.end) == (2.2, 3.8)
    assert (result.x, result.y, result.width, result.height) == (120, 250, 180, 180)
    assert (result.animation, result.rotation, result.z_index) == ("float", 3, 60)
    assert len(composed.graphics) == 2
    assert composed.graphics[1].asset_id == "scrapbook_tape"
    assert composed.graphics[1].z_index == 70


def test_scrapbook_card_gets_a_small_grounded_accent_and_respects_exclusion():
    registry = AssetRegistry()
    placement = {"x": 200, "y": 250, "width": 280, "height": 340}
    layers = _build_composition_layers(
        "pinterest_scrapbook", "book", placement, 1080, 1920,
        "AI study guide", "laptop and notes", "Use scrapbook styling", registry,
    )
    excluded = _build_composition_layers(
        "pinterest_scrapbook", "book", placement, 1080, 1920,
        "AI study guide", "laptop and notes", "Use scrapbook styling, no tape", registry,
    )
    glass = _build_composition_layers(
        "glassmorphism", "book", placement, 1080, 1920,
        "AI study guide", "laptop and notes", "Use a modern interface treatment", registry,
    )
    glass_excluded = _build_composition_layers(
        "glassmorphism", "book", placement, 1080, 1920,
        "AI study guide", "laptop and notes", "Use a modern interface treatment, no glass", registry,
    )
    lifestyle = _build_composition_layers(
        "aesthetic_lifestyle", "sun_warmth", placement, 1080, 1920,
        "sunny outdoor outfit", "golden hour fashion", "Soft lifestyle highlights", registry,
    )
    music = _build_composition_layers(
        "floating_music_player", "music_player_card", placement, 1080, 1920,
        "favorite song track", "music audio player", "Show this music moment", registry,
    )

    assert len(layers) == 1
    assert layers[0]["asset_id"] == "scrapbook_tape"
    assert layers[0]["z_index"] > 50
    assert excluded == []
    assert glass[0]["asset_id"] == "glass_pill"
    assert glass_excluded == []
    assert lifestyle[0]["asset_id"] == "sparkle_stars"
    assert music[0]["asset_id"] == "sound_wave"


def test_director_reconciliation_removes_unplanned_graphics_and_reports_reason():
    edl = EditDecisionList(
        video_duration=10,
        graphics=[
            {"id": "planned", "asset_id": "book", "start": 2, "end": 4, "x": 100, "y": 200},
            {"id": "random", "asset_id": "money", "start": 2, "end": 4, "x": 400, "y": 200},
        ],
    )
    plan = {"decisions": [{
        "segment_id": "seg1", "needs_visual_element": True, "chosen_asset_id": "book",
        "start": 2, "end": 4, "placement": {"x": 120, "y": 220, "width": 180, "height": 180},
    }]}
    report = {}

    result = apply_plan_composition(edl, plan, report=report)

    assert [item.asset_id for item in result.graphics] == ["book"]
    assert report["unplanned_graphics_removed"] == [{
        "graphic_id": "random", "asset_id": "money",
        "reason": "No segment-level validated asset decision supports this graphic",
    }]
    assert report["provider_graphics_aligned"] == 1

