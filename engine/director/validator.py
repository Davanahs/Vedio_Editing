"""
EDL validator — sanitizes and validates an EditDecisionList.
"""
from __future__ import annotations

from .edl_schema import EditDecisionList, GraphicElement, ZoomEvent


class EDLValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("EDL validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


def validate_edl(
    edl: EditDecisionList,
    asset_ids: set[str],
    sfx_ids: set[str],
) -> EditDecisionList:
    """
    Validate and sanitize an EDL.
    - Clamps timestamps to [0, video_duration]
    - Validates asset references
    - Clamps zoom scale to [1.0, 1.4]
    - Removes out-of-bounds graphics
    Returns a sanitized EditDecisionList or raises EDLValidationError.
    """
    errors: list[str] = []
    duration = edl.video_duration

    if duration <= 0:
        errors.append(f"video_duration must be > 0, got {duration}")

    # --- Captions ---
    cleaned_captions = []
    for c in edl.captions:
        if c.start < 0 or c.start > duration:
            errors.append(f"Caption '{c.id}' start={c.start} out of range [0, {duration}]")
            continue
        if c.end > duration:
            c = c.model_copy(update={"end": duration})
        if c.start >= c.end:
            errors.append(f"Caption '{c.id}' start >= end ({c.start} >= {c.end})")
            continue
        cleaned_captions.append(c)

    # --- Zoom Events ---
    cleaned_zooms = []
    for z in edl.zoom_events:
        if z.start < 0 or z.start > duration:
            errors.append(f"ZoomEvent '{z.id}' start={z.start} out of range")
            continue
        end = min(z.end, duration)
        scale = max(1.0, min(1.4, z.scale))
        cleaned_zooms.append(z.model_copy(update={"end": end, "scale": scale}))

    # --- Graphics ---
    cleaned_graphics: list[GraphicElement] = []
    for g in edl.graphics:
        # Validate asset exists
        if g.asset_id not in asset_ids:
            errors.append(
                f"Graphic '{g.id}' references unknown asset '{g.asset_id}'. "
                f"Available: {sorted(asset_ids)}"
            )
            continue
        # Check canvas bounds (1080x1920)
        if g.x < 0 or g.x > 1080 or g.y < 0 or g.y > 1920:
            errors.append(
                f"Graphic '{g.id}' position ({g.x}, {g.y}) outside canvas (1080x1920), skipped"
            )
            continue
        if g.start < 0 or g.start > duration:
            errors.append(f"Graphic '{g.id}' start={g.start} out of range")
            continue
        end = min(g.end, duration)
        cleaned_graphics.append(g.model_copy(update={"end": end}))

    # --- Sound Effects ---
    cleaned_sfx = []
    for s in edl.sound_effects:
        if s.asset_id not in sfx_ids:
            errors.append(
                f"SFX '{s.id}' references unknown sfx '{s.asset_id}'. "
                f"Available: {sorted(sfx_ids)}"
            )
            continue
        if s.start < 0 or s.start > duration:
            errors.append(f"SFX '{s.id}' start={s.start} out of range")
            continue
        cleaned_sfx.append(s)

    # Hard errors (not just warnings)
    if any("out of range" in e and "Caption" in e for e in errors):
        # Soft: we already filtered them out
        pass

    # Build sanitized EDL (only raise if critical errors)
    critical = [e for e in errors if "unknown asset" in e or "unknown sfx" in e]
    if critical:
        raise EDLValidationError(critical)

    sanitized = edl.model_copy(update={
        "captions": cleaned_captions,
        "zoom_events": cleaned_zooms,
        "graphics": cleaned_graphics,
        "sound_effects": cleaned_sfx,
    })
    return sanitized
