"""
EDL validator — sanitizes and validates an EditDecisionList.
"""
from __future__ import annotations

from .edl_schema import EditDecisionList, GraphicElement, ZoomEvent


class EDLValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("EDL validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


def apply_plan_composition(edl: EditDecisionList, multimodal_plan: dict, report: dict | None = None) -> EditDecisionList:
    """Carry validated plan geometry into matching EDL overlays before rendering."""
    rejected: list[dict] = []
    aligned = 0
    added = 0
    decisions = [
        item for item in multimodal_plan.get("decisions", [])
        if item.get("needs_visual_element") and item.get("chosen_asset_id")
    ]
    graphics = []
    matched_segments: set[str] = set()
    for graphic in edl.graphics:
        if graphic.id == "g_title_0" or getattr(graphic, "type", "") == "kinetic_title":
            graphics.append(graphic)
            continue
        matches = [
            item for item in decisions
            if item.get("chosen_asset_id") == graphic.asset_id
            and max(float(item.get("start", 0)), graphic.start) < min(float(item.get("end", 0)), graphic.end)
        ]
        if not matches:
            rejected.append({
                "graphic_id": graphic.id,
                "asset_id": graphic.asset_id,
                "reason": "No segment-level validated asset decision supports this graphic",
            })
            continue
        decision = min(matches, key=lambda item: abs(float(item.get("start", 0)) - graphic.start))
        matched_segments.add(str(decision.get("segment_id", "")))
        aligned += 1
        placement = decision.get("placement", {})
        graphics.append(graphic.model_copy(update={
            "start": float(decision.get("start", graphic.start)),
            "end": float(decision.get("end", graphic.end)),
            "x": int(placement.get("x", graphic.x)),
            "y": int(placement.get("y", graphic.y)),
            "width": int(placement.get("width", graphic.width)),
            "height": int(placement.get("height", graphic.height)),
            "z_index": int(placement.get("z_index", graphic.z_index)),
            "rotation": float(placement.get("rotation", graphic.rotation)),
            "animation": str(decision.get("animation", graphic.animation)),
        }))
    for decision in decisions:
        if str(decision.get("segment_id", "")) not in matched_segments:
            placement = decision.get("placement", {})
            graphics.append(GraphicElement(
                id=f"g_plan_{decision.get('chosen_asset_id')}_{decision.get('segment_id')}",
                asset_id=decision["chosen_asset_id"],
                start=float(decision.get("start", 0)),
                end=float(decision.get("end", 0)),
                x=int(placement.get("x", 0)),
                y=int(placement.get("y", 0)),
                width=int(placement.get("width", 180)),
                height=int(placement.get("height", 180)),
                z_index=int(placement.get("z_index", 50)),
                rotation=float(placement.get("rotation", 0)),
                animation=str(decision.get("animation", "fade")),
                title=str(decision.get("asset_badge_title", "")),
                subtitle=str(decision.get("asset_badge_subtitle", "")),
            ))
            added += 1
        for layer_index, layer in enumerate(decision.get("composition_layers", [])):
            identity = (
                layer.get("asset_id"), float(decision.get("start", 0)), float(decision.get("end", 0)),
                int(layer.get("x", 0)), int(layer.get("y", 0)),
            )
            present = any((
                graphic.asset_id, graphic.start, graphic.end, graphic.x, graphic.y,
            ) == identity for graphic in graphics)
            if not present:
                graphics.append(GraphicElement(
                    id=f"g_plan_layer_{layer.get('asset_id')}_{decision.get('segment_id')}_{layer_index}",
                    asset_id=layer["asset_id"],
                    start=float(decision.get("start", 0)),
                    end=float(decision.get("end", 0)),
                    x=int(layer["x"]), y=int(layer["y"]),
                    width=int(layer["width"]), height=int(layer["height"]),
                    z_index=int(layer.get("z_index", 60)),
                    rotation=float(layer.get("rotation", 0)),
                    animation=str(layer.get("animation", "pop_fade")),
                ))
                added += 1
    if report is not None:
        report.update({
            "status": "validated",
            "provider_graphics_aligned": aligned,
            "planned_graphics_added": added,
            "unplanned_graphics_removed": rejected,
            "template_id": edl.template_id,
        })
    return edl.model_copy(update={"graphics": graphics})


def validate_edl(
    edl: EditDecisionList,
    asset_ids: set[str],
    sfx_ids: set[str],
    canvas_width: int = 1080,
    canvas_height: int = 1920,
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
        if g.start < 0 or g.start >= duration:
            errors.append(f"Graphic '{g.id}' start={g.start} out of range")
            continue
        end = min(g.end, duration)
        if end <= g.start:
            errors.append(f"Graphic '{g.id}' has non-positive duration")
            continue
        width = min(max(1, g.width), canvas_width)
        height = min(max(1, g.height), canvas_height)
        x = min(max(0, g.x), canvas_width - width)
        y = min(max(0, g.y), canvas_height - height)
        cleaned_graphics.append(g.model_copy(update={
            "start": max(0.0, g.start), "end": end,
            "x": x, "y": y, "width": width, "height": height,
        }))

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
