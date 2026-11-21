import asyncio
import unittest
from pathlib import Path

from engine.assets.registry import AssetRegistry
from engine.providers.registry import LocalHeuristicDirectorProvider


_ROOT = Path(__file__).resolve().parent.parent.parent


class TestDirectorFallbackAssets(unittest.TestCase):
    def test_default_hook_uses_registered_asset(self):
        registry = AssetRegistry(str(_ROOT))
        result = asyncio.run(LocalHeuristicDirectorProvider().generate_edl(
            "Create a simple edit.",
            context={
                "transcript": "Today I want to share a simple creator workflow.",
                "caption_bursts": [],
                "video_metadata": {"duration": 12.0, "width": 1080, "height": 1920},
                "available_assets": registry.list_available_logos() + registry.list_available_stickers(),
                "available_sfx": registry.list_available_sfx(),
            },
        ))
        available = set(registry.list_available_logos() + registry.list_available_stickers())
        graphics = result.edl.get("graphics", [])
        self.assertTrue(graphics)
        self.assertTrue(all(item["asset_id"] in available for item in graphics))


if __name__ == "__main__":
    unittest.main()
