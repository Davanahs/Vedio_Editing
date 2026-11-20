"""
Acceptance Test Execution Script for Problem 9.
Renders all 3 required test variants:
1. Pinterest Scrapbook -> Export/notebooklm_pinterest_scrapbook.mp4
2. Glassmorphism       -> Export/notebooklm_glassmorphism.mp4
3. Creative Minimal    -> Export/notebooklm_creative_minimal.mp4
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.pipeline import run_pipeline

RAW_VIDEO = "Raw Footage/WhatsApp_Video_2026-11-18_at_13.03.38.mp4"

TEST_CASES = [
    {
        "name": "Test A - Pinterest Scrapbook",
        "template_id": "pinterest_scrapbook",
        "output_path": "Export/notebooklm_pinterest_scrapbook.mp4",
        "prompt": "Aesthetic scrapbook composition with Polaroid photo frames, hand-drawn white outlines, floating stars, and layered shadows.",
        "additional_instructions": "Use stars and glitter, but do not cover my face. Keep scrapbook look and use pastel colours."
    },
    {
        "name": "Test B - Glassmorphism",
        "template_id": "glassmorphism",
        "output_path": "Export/notebooklm_glassmorphism.mp4",
        "prompt": "Translucent floating glass cards orbiting speaker, frosted-glass panels with pink and cyan glow trails.",
        "additional_instructions": "Ensure clean negative space, do not overlap captions or cover faces."
    },
    {
        "name": "Test C - Creative Minimal",
        "template_id": "creative_minimal",
        "output_path": "Export/notebooklm_creative_minimal.mp4",
        "prompt": "Minimalist edit with extreme restraint: 2-3 maximum high-impact highlights, clean negative space.",
        "additional_instructions": "Minimal overlays, pure white typography, zero clutter."
    }
]


async def run_all_tests():
    export_dir = Path("Export")
    export_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for tc in TEST_CASES:
        print(f"\n=======================================================")
        print(f"🎬 EXECUTING {tc['name']}")
        print(f"   Template: {tc['template_id']}")
        print(f"   Output:   {tc['output_path']}")
        print(f"=======================================================")

        res = await run_pipeline(
            video_path=RAW_VIDEO,
            output_path=tc["output_path"],
            template_id=tc["template_id"],
            user_prompt=tc["prompt"],
            additional_instructions=tc["additional_instructions"]
        )

        out_file = Path(tc["output_path"])
        size_mb = out_file.stat().st_size / (1024 * 1024) if out_file.exists() else 0.0

        # Validate that the EDL and output do NOT contain fake items
        edl = res.get("edl", {})
        graphics = edl.get("graphics", [])
        hook = edl.get("hook_title", "")
        social_q = edl.get("social_question", "")

        fake_words = ["spotify", "akon", "dangerous", "sandals", "alex_clips"]
        all_text = " ".join([
            hook,
            social_q or "",
            *[g.get("trigger_word", "") for g in graphics],
            *[g.get("title", "") for g in graphics]
        ]).lower()

        has_fakes = any(fw in all_text for fw in fake_words)

        results.append({
            "name": tc["name"],
            "template": tc["template_id"],
            "success": res.get("success", False),
            "output_path": str(out_file),
            "size_mb": round(size_mb, 2),
            "has_fakes": has_fakes,
            "graphics_count": len(graphics),
            "captions_count": len(edl.get("captions", []))
        })
        print(f"✅ Finished {tc['name']}: {size_mb:.2f} MB, Fakes Detected: {has_fakes}")

    print("\n=======================================================")
    print("📊 ACCEPTANCE TEST SUMMARY")
    print("=======================================================")
    for r in results:
        status = "PASSED ✅" if r["success"] and not r["has_fakes"] and r["size_mb"] > 0.5 else "FAILED ❌"
        print(f"• {r['name']}: {status}")
        print(f"    File: {r['output_path']} ({r['size_mb']} MB)")
        print(f"    Graphics: {r['graphics_count']}, Captions: {r['captions_count']}, Fakes: {r['has_fakes']}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
