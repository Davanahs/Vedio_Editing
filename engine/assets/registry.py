import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

class AssetRegistry:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).resolve().parent.parent.parent

        self.manifest_path = Path(__file__).resolve().parent / "manifest.json"
        self.logo_dir = self.base_dir / "assets" / "cache" / "logos"
        self.sfx_dir = self.base_dir / "assets" / "sfx"
        
        self.data: Dict = {"version": "2.0", "categories": [], "logos": {}, "stickers": {}, "sfx": {}}
        self.load()

    def load(self):
        if self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def get_logo(self, name: str) -> Optional[Dict]:
        logo_info = self.data.get("logos", {}).get(name.lower())
        if not logo_info:
            return None
        file_path = self.logo_dir / logo_info.get("file", f"{name}.svg")
        res = dict(logo_info)
        res["exists_locally"] = file_path.exists()
        res["local_path"] = str(file_path) if file_path.exists() else None
        return res

    def get_sticker(self, name: str) -> Optional[Dict]:
        return self.data.get("stickers", {}).get(name.lower())

    def get_asset_metadata(self, name: str) -> Optional[Dict]:
        """Unified lookup for sticker or logo metadata."""
        n = name.lower()
        if n in self.data.get("stickers", {}):
            d = dict(self.data["stickers"][n])
            d["asset_type"] = "sticker"
            d["id"] = n
            return d
        if n in self.data.get("logos", {}):
            d = dict(self.data["logos"][n])
            d["asset_type"] = "logo"
            d["id"] = n
            return d
        return None

    def get_sfx(self, name: str) -> Optional[Dict]:
        sfx_info = self.data.get("sfx", {}).get(name.lower())
        if not sfx_info:
            return None
        file_path = self.sfx_dir / sfx_info.get("file", f"{name}.wav")
        res = dict(sfx_info)
        res["exists_locally"] = file_path.exists()
        res["local_path"] = str(file_path) if file_path.exists() else None
        return res

    def list_available_logos(self) -> List[str]:
        return list(self.data.get("logos", {}).keys())

    def list_available_stickers(self) -> List[str]:
        return list(self.data.get("stickers", {}).keys())

    def list_available_sfx(self) -> List[str]:
        return list(self.data.get("sfx", {}).keys())

    def list_categories(self) -> List[str]:
        return list(self.data.get("categories", []))

    def list_assets_by_category(self, category: str) -> List[Dict]:
        """Returns all assets (stickers + logos) matching a specific category."""
        res = []
        for k, v in self.data.get("stickers", {}).items():
            if v.get("category") == category:
                item = dict(v)
                item["id"] = k
                res.append(item)
        for k, v in self.data.get("logos", {}).items():
            if v.get("category") == category:
                item = dict(v)
                item["id"] = k
                res.append(item)
        return res

    def validate_asset_relevance(
        self,
        asset_id: str,
        topic: str,
        scene_visuals: str,
        template_id: str = "auto_creative",
        additional_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates whether an asset is semantically relevant to the topic & visual scene.
        Rejects mismatched assets (e.g. Spotify on AI tutorial, tech chips on lifestyle outfits).
        """
        meta = self.get_asset_metadata(asset_id)
        if not meta:
            return {"relevant": False, "reason": f"Asset '{asset_id}' not found in registry"}

        cat = meta.get("category", "")
        keywords = meta.get("keywords", [])
        suitable_types = meta.get("suitable_content_types", ["all"])

        topic_low = (topic or "").lower()
        scene_low = (scene_visuals or "").lower()
        instr_low = (additional_instructions or "").lower()

        # Check negative rule: Never place gaming or cash stickers on non-gaming/non-finance topics
        if cat == "gaming" and not any(w in topic_low or w in scene_low for w in ["game", "gaming", "esports", "gta", "playstation", "xbox", "fps", "stream"]):
            return {"relevant": False, "reason": "Gaming asset rejected for non-gaming content"}

        # Check negative rule: Never place music track cards on non-music/non-audio topics unless template is floating_music_player
        if cat == "music_audio" and asset_id == "music_card" and template_id != "floating_music_player":
            if not any(w in topic_low for w in ["music", "song", "audio", "spotify", "playlist"]):
                return {"relevant": False, "reason": "Music player card rejected for non-music topic"}

        # Check negative rule: Never place tech chips/code brackets on pure fashion/outfit/cooking scenes
        if cat == "ai_technology" and any(w in topic_low or w in scene_low for w in ["outfit", "dress", "recipe", "cooking", "skincare", "picnic"]):
            if not any(w in topic_low for w in ["ai", "tech", "code", "software", "tool"]):
                return {"relevant": False, "reason": "Tech asset rejected for lifestyle/cooking content"}

        # Check negative rule: Never place food cooking on coding/tech
        if cat == "food_cooking" and not any(w in topic_low or w in scene_low for w in ["food", "recipe", "cook", "chef", "eat", "meal", "kitchen", "bake"]):
            return {"relevant": False, "reason": "Food asset rejected for non-food content"}

        # User explicit restriction check
        if "minimal" in instr_low and "no sticker" in instr_low:
            return {"relevant": False, "reason": "User requested zero stickers"}

        # Positive matching check: Does any keyword appear in topic or scene?
        matched_kw = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', topic_low + " " + scene_low)]
        
        # Universal social engagement assets (like, comment, bell) are allowed during closing segments
        if cat == "social_engagement":
            return {"relevant": True, "score": 0.85, "reason": "Engagement callout appropriate"}

        if matched_kw or "all" in suitable_types:
            return {"relevant": True, "score": 0.9, "matched_keywords": matched_kw}

        # If template is explicitly selected, check if style matches
        if template_id == "pinterest_scrapbook" and cat in ["scrapbook_decorative", "fashion_lifestyle"]:
            return {"relevant": True, "score": 0.8, "reason": "Matches Pinterest scrapbook visual style"}

        return {"relevant": False, "reason": "No semantic relevance to audio or visual scene"}

    def get_summary(self) -> Dict[str, Any]:
        return {
            "categories": self.list_categories(),
            "logos": self.list_available_logos(),
            "stickers": self.list_available_stickers(),
            "sfx": self.list_available_sfx()
        }
