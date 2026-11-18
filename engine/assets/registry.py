import os
import json
from pathlib import Path
from typing import Dict, List, Optional

class AssetRegistry:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).resolve().parent.parent.parent

        self.manifest_path = Path(__file__).resolve().parent / "manifest.json"
        self.logo_dir = self.base_dir / "assets" / "cache" / "logos"
        self.sfx_dir = self.base_dir / "assets" / "sfx"
        
        self.data: Dict = {"logos": {}, "stickers": {}, "sfx": {}}
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

    def get_summary(self) -> Dict[str, List[str]]:
        return {
            "logos": self.list_available_logos(),
            "stickers": self.list_available_stickers(),
            "sfx": self.list_available_sfx()
        }
