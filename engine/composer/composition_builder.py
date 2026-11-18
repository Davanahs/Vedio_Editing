"""
Composition Builder for Reel Editor.
Assembles the complete HyperFrames project (index.html, captions.html, overlays.html).
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

from engine.director.edl_schema import EditDecisionList
from engine.composer.caption_builder import build_captions_html
from engine.composer.overlay_builder import build_overlays_html
from engine.composer.camera_fx import build_zoom_js

def build_composition(
    edl: EditDecisionList,
    target_dir: str,
    footage_rel_path: str = "assets/footage.mp4",
    bgm_rel_path: Optional[str] = "assets/bgm.wav",
    asset_registry: Any = None
) -> Dict[str, str]:
    """
    Builds and writes all HTML compositions into target_dir.
    Returns a dict with paths to generated files.
    """
    target = Path(target_dir)
    compositions_dir = target / "compositions"
    compositions_dir.mkdir(parents=True, exist_ok=True)

    duration = round(edl.video_duration, 2)
    
    # 1. Generate Captions HTML
    captions_html = build_captions_html(edl.captions)
    captions_file = compositions_dir / "captions.html"
    captions_file.write_text(captions_html, encoding="utf-8")

    # 2. Generate Overlays HTML
    overlays_html = build_overlays_html(
        graphics=edl.graphics,
        sound_effects=edl.sound_effects,
        video_duration=duration,
        asset_registry=asset_registry
    )
    overlays_file = compositions_dir / "overlays.html"
    overlays_file.write_text(overlays_html, encoding="utf-8")

    # 3. Build Root index.html
    zoom_script = build_zoom_js(edl.zoom_events)
    
    # Background music element
    bgm_audio = ""
    if bgm_rel_path:
        bgm_audio = f'      <audio id="bgm" src="{bgm_rel_path}" data-start="0" data-duration="{duration}" data-track-index="1"></audio>'

    # Dynamic SFX in main root
    sfx_audio_tags = []
    for i, s in enumerate(edl.sound_effects):
        sfx_path = f"assets/{s.asset_id}.wav"
        sfx_audio_tags.append(
            f'      <audio id="root_sfx_{i}" src="{sfx_path}" data-start="{s.start:.2f}" data-duration="0.5"></audio>'
        )
    sfx_block = "\n".join(sfx_audio_tags)

    index_html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, height=1920">
    <title>AI Reel Export</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}

      html, body {{
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #0D0E13;
      }}

      #root {{
        position: relative;
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: radial-gradient(circle at 50% 35%, #1B1E2E 0%, #0D0E13 65%, #07080B 100%);
      }}

      .bg-overlay {{
        position: absolute;
        inset: 0;
        opacity: 0.12;
        background-image: repeating-linear-gradient(90deg, #FFFFFF 0px, #FFFFFF 2px, transparent 2px, transparent 40px);
        pointer-events: none;
      }}

      #footage {{
        position: absolute;
        top: 450px;
        left: 60px;
        width: 960px;
        height: 544px;
        border-radius: 28px;
        object-fit: cover;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(255, 230, 0, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.15);
        z-index: 10;
        transform-origin: center center;
      }}

      .sub-comp {{
        position: absolute;
        inset: 0;
        width: 1080px;
        height: 1920px;
        pointer-events: none;
      }}

      #overlays-layer {{
        z-index: 20;
      }}

      #captions-layer {{
        z-index: 30;
      }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duration}" data-width="1080" data-height="1920">
      <div class="bg-overlay"></div>

      <!-- Main Video Footage -->
      <video id="footage" class="clip" src="{footage_rel_path}" data-start="0" data-duration="{duration}" data-has-audio="true" preload="auto"></video>

      <!-- Sub-Compositions -->
      <div id="overlays-layer" class="clip sub-comp" data-composition-src="compositions/overlays.html" data-composition-id="overlays" data-start="0" data-duration="{duration}"></div>

      <div id="captions-layer" class="clip sub-comp" data-composition-src="compositions/captions.html" data-composition-id="captions" data-start="0" data-duration="{duration}"></div>

{bgm_audio}
{sfx_block}
    </div>

    <script>
      // Camera Zoom Timeline
      {zoom_script}
    </script>
  </body>
</html>'''

    index_file = target / "index.html"
    index_file.write_text(index_html, encoding="utf-8")

    return {
        "index": str(index_file),
        "captions": str(captions_file),
        "overlays": str(overlays_file)
    }
