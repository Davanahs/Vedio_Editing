"""
Camera FX Builder for Reel Editor.
Generates GSAP timeline animations for dynamic camera punch-ins and zooms.
"""
from typing import List, Union
from engine.director.edl_schema import ZoomEvent

def build_zoom_js(zoom_events: List[Union[ZoomEvent, dict]]) -> str:
    """
    Builds client-side JavaScript to animate the #footage element.
    """
    if not zoom_events:
        return "// No zoom events"

    js_lines = [
        "// Camera punch-in and zoom timeline",
        "const footageEl = document.querySelector('#footage');",
        "if (footageEl) {",
        "  const zoomTl = gsap.timeline();"
    ]

    # Sort events by start time
    sorted_events = sorted(
        zoom_events, 
        key=lambda x: x.get("start", 0.0) if isinstance(x, dict) else x.start
    )

    last_time = 0.0

    for z in sorted_events:
        if isinstance(z, dict):
            start = float(z.get("start", 0.0))
            end = float(z.get("end", 0.0))
            scale = float(z.get("scale", 1.15))
            ease = z.get("ease", "power2.inOut")
        else:
            start = z.start
            end = z.end
            scale = z.scale
            ease = z.ease

        dur = max(0.2, end - start)
        
        # Punch in
        js_lines.append(f"  zoomTl.to(footageEl, {{ scale: {scale:.2f}, duration: 0.25, ease: '{ease}' }}, {start:.3f});")
        # Return to base
        js_lines.append(f"  zoomTl.to(footageEl, {{ scale: 1.0, duration: 0.25, ease: 'power2.out' }}, {end:.3f});")

    js_lines.append("}")
    return "\n".join(js_lines)
