from engine.assets.semantic_ranker import score_asset_descriptions


def test_asset_ranker_prefers_semantically_matching_catalog_artwork():
    scores, method = score_asset_descriptions(
        "soft floral scrapbook decoration for a spring outfit",
        [
            {
                "id": "flower_blossom",
                "category": "fashion_lifestyle",
                "visual_description": "Soft pink cherry blossom petal for delicate aesthetic styling",
                "keywords": ["flower", "spring", "outfit", "aesthetic"],
            },
            {
                "id": "gamepad",
                "category": "gaming",
                "visual_description": "Video game controller for gameplay footage",
                "keywords": ["game", "gaming", "controller"],
            },
        ],
    )

    assert len(scores) == 2
    assert scores[0] > scores[1]
    assert method in {"sentence-transformers/all-MiniLM-L6-v2", "local_keyword_fallback"}

