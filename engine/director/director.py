"""
AI Director orchestrator — generates and validates an EDL with automatic provider fallback.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from ..director.edl_schema import EditDecisionList
from ..director.prompts import format_director_prompt
from ..director.validator import EDLValidationError, validate_edl
from ..providers.registry import get_director_chain

logger = logging.getLogger(__name__)

MAX_RETRIES = 1


async def generate_edl(
    transcript: str,
    caption_bursts: list[dict],
    video_metadata: dict,
    asset_registry: Any,  # AssetRegistry instance
    sfx_registry: list[str],
) -> EditDecisionList:
    """
    Main director orchestrator.
    Iterates through configured providers (Gemini -> OpenRouter -> Local Heuristic)
    with automatic fallback until a valid EDL is produced.
    """
    chain = get_director_chain()

    available_assets = (
        asset_registry.list_available_logos()
        + asset_registry.list_available_stickers()
    )
    available_sfx = asset_registry.list_available_sfx()

    asset_ids = set(available_assets)
    sfx_ids = set(available_sfx)

    prompt = format_director_prompt(
        transcript=transcript,
        bursts=caption_bursts,
        video_metadata=video_metadata,
        available_assets=available_assets,
        available_sfx=available_sfx,
    )

    last_error: Exception | None = None

    for provider in chain:
        logger.info(f"🎬 Director trying: {provider.name}")
        error_feedback = ""

        for attempt in range(1, MAX_RETRIES + 1):
            full_prompt = prompt
            if error_feedback:
                full_prompt += (
                    f"\n\n## PREVIOUS ATTEMPT FAILED\n"
                    f"Fix these errors and output valid JSON only:\n{error_feedback}"
                )

            t0 = time.perf_counter()
            try:
                result = await provider.generate_edl(
                    full_prompt, 
                    context={
                        "transcript": transcript,
                        "caption_bursts": caption_bursts,
                        "video_metadata": video_metadata,
                        "available_assets": available_assets,
                        "available_sfx": available_sfx
                    }
                )
                elapsed = time.perf_counter() - t0
                logger.info(
                    f"  {provider.name} responded in {elapsed:.2f}s "
                    f"({result.tokens_used} tokens)"
                )
            except Exception as e:
                last_error = e
                logger.warning(f"  {provider.name} attempt {attempt} failed: {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1)
                continue

            # Parse EDL
            try:
                edl_obj = EditDecisionList(**result.edl)
            except Exception as e:
                last_error = e
                error_feedback = f"JSON parsed but schema invalid: {e}"
                logger.warning(f"  Schema error: {e}")
                continue

            # Validate
            try:
                edl_obj = validate_edl(edl_obj, asset_ids=asset_ids, sfx_ids=sfx_ids)
                logger.info(
                    f"✅ EDL validated: {len(edl_obj.captions)} captions, "
                    f"{len(edl_obj.graphics)} graphics, "
                    f"{len(edl_obj.zoom_events)} zooms, "
                    f"{len(edl_obj.sound_effects)} sfx"
                )
                return edl_obj
            except EDLValidationError as e:
                last_error = e
                error_feedback = str(e)
                logger.warning(f"  Validation error: {e}")
                continue

        logger.warning(f"⚠️ Provider {provider.name} could not produce a valid EDL, trying next provider in chain...")

    raise RuntimeError(
        f"All Director providers failed. Last error: {last_error}"
    )
