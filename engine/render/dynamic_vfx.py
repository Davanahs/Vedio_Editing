"""
Dynamic Visual FX & Motion Graphics Engine.
Synthesizes professional, dynamic motion effects:
1. Disco Ball with 360-degree rotating volumetric light rays & mirror reflections.
2. Kinetic Lines & dynamic trailing accent swooshes.
3. Glitter & Twinkling Sparkle particle fields with face clearance.

Generates high-speed screen-blendable MP4 loops or overlays composited natively by FFmpeg.
"""
from __future__ import annotations

import math
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


def detect_dynamic_vfx_intent(
    prompt: str = "",
    transcript: str = "",
    template_id: str = "auto_creative",
    explicit_vfx: Optional[str] = None
) -> Optional[str]:
    """
    Detects if the user prompt, transcript, or explicit option requires a dynamic VFX overlay.
    """
    if explicit_vfx and explicit_vfx.lower() not in {"none", "off", "false"}:
        return explicit_vfx.lower()

    text = f"{prompt} {transcript}".lower().strip()
    if not text:
        return None

    if any(k in text for k in ["disco", "party", "club", "dance", "nightclub", "dj", "celebrat"]):
        return "disco_ball_lights"
    if any(k in text for k in ["glitter", "sparkle", "stars", "twinkle", "shimmer", "magic"]):
        return "glitter_sparkle"
    if any(k in text for k in ["lines", "speed", "kinetic", "fast", "trail", "pulse", "action"]):
        return "kinetic_lines"

    return None


def generate_vfx_overlay_video(
    vfx_type: str,
    output_path: str | Path,
    width: int = 1080,
    height: int = 1920,
    duration: float = 4.0,
    fps: int = 30,
    intensity: str = "creative",
    face_boxes: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Generates a high-speed black-background video designed for screen blending
    (blend=all_mode=screen in FFmpeg) where black is 100% transparent and
    colored light rays, glints, and particles illuminate the video underneath.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_frames = max(15, int(duration * fps))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not out.isOpened():
        logger.error(f"Failed to open VideoWriter for {output_path}")
        return False

    try:
        if vfx_type == "disco_ball_lights":
            _render_disco_ball_frames(out, width, height, total_frames, fps, intensity)
        elif vfx_type == "kinetic_lines":
            _render_kinetic_lines_frames(out, width, height, total_frames, fps, intensity)
        elif vfx_type == "glitter_sparkle":
            _render_glitter_frames(out, width, height, total_frames, fps, intensity, face_boxes)
        else:
            _render_kinetic_lines_frames(out, width, height, total_frames, fps, intensity)
    except Exception as e:
        logger.error(f"Error rendering VFX video {vfx_type}: {e}")
        out.release()
        return False

    out.release()
    return output_path.exists() and output_path.stat().st_size > 0


def _render_disco_ball_frames(
    out: cv2.VideoWriter,
    w: int,
    h: int,
    total_frames: int,
    fps: int,
    intensity: str = "creative"
):
    """
    Renders a suspended rotating mirror disco ball with volumetric spreading light rays
    and mirror reflection spots dancing across the scene.
    """
    # Disco ball center at top
    ball_cx = w // 2
    ball_cy = int(h * 0.14) if h > w else int(h * 0.18)
    ball_r = int(min(w, h) * 0.085)

    # Palette: Neon Cyan, Magenta, Golden Yellow, Laser Purple, Electric Lime (BGR)
    beam_colors = [
        (255, 210, 0),    # Cyan
        (230, 20, 255),   # Magenta
        (30, 220, 255),   # Gold/Yellow
        (255, 80, 180),   # Neon Purple
        (80, 255, 80),    # Lime
        (255, 140, 20),   # Sky Blue
        (20, 160, 255),   # Warm Amber
    ]
    num_beams = 16 if intensity == "high_energy" else 12
    max_dist = math.hypot(w, h) * 1.2

    # Pre-generate 35 mirror light spots with fixed random seeds for consistency
    rng = np.random.RandomState(42)
    spots = []
    for i in range(40):
        spots.append({
            "orbit_r": rng.uniform(ball_r * 1.5, max(w, h) * 0.8),
            "speed": rng.uniform(0.8, 2.2) * (1 if rng.rand() > 0.5 else -1),
            "phase": rng.uniform(0, 2 * math.pi),
            "y_mult": rng.uniform(0.5, 1.4),
            "radius": rng.randint(4, 14),
            "color": beam_colors[i % len(beam_colors)],
            "pulse_freq": rng.uniform(2.0, 5.0),
        })

    for f in range(total_frames):
        t = f / fps
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # 1. Volumetric Rotating Light Beams (Spreading across the frame)
        rot_angle = t * 0.85
        pulse = 0.85 + 0.15 * math.sin(t * 4.0)

        for b in range(num_beams):
            angle = rot_angle + (b * (2 * math.pi / num_beams))
            beam_width_angle = 0.14  # beam spread

            color = beam_colors[b % len(beam_colors)]
            c_scaled = tuple(int(c * 0.55 * pulse) for c in color)

            # End coordinates of beam polygon
            p1 = (
                int(ball_cx + max_dist * math.cos(angle - beam_width_angle / 2)),
                int(ball_cy + max_dist * math.sin(angle - beam_width_angle / 2))
            )
            p2 = (
                int(ball_cx + max_dist * math.cos(angle + beam_width_angle / 2)),
                int(ball_cy + max_dist * math.sin(angle + beam_width_angle / 2))
            )

            # Draw beam triangle onto an accumulation layer
            beam_poly = np.array([[ball_cx, ball_cy], p1, p2], dtype=np.int32)
            cv2.fillPoly(frame, [beam_poly], c_scaled, lineType=cv2.LINE_AA)

        # Soft blur the light beams to make them truly volumetric & atmospheric
        frame = cv2.GaussianBlur(frame, (35, 35), 0)

        # 2. Dancing Specular Mirror Spots / Reflections across the room
        for s in spots:
            spot_angle = s["phase"] + t * s["speed"]
            sx = int(ball_cx + s["orbit_r"] * math.cos(spot_angle))
            sy = int(ball_cy + s["orbit_r"] * math.sin(spot_angle) * s["y_mult"] + (t * 20 % h)) % h
            
            # Pulse intensity
            spot_pulse = max(0.2, math.sin(t * s["pulse_freq"] + s["phase"]))
            sc = tuple(int(c * spot_pulse) for c in s["color"])
            
            if 0 <= sx < w and 0 <= sy < h:
                cv2.circle(frame, (sx, sy), s["radius"], sc, -1, lineType=cv2.LINE_AA)
                # Soft outer glow
                cv2.circle(frame, (sx, sy), int(s["radius"] * 1.8), tuple(c // 3 for c in sc), 1, lineType=cv2.LINE_AA)

        # 3. Suspended Chain
        chain_color = (180, 180, 180)
        cv2.line(frame, (ball_cx, 0), (ball_cx, ball_cy - ball_r), chain_color, 3, lineType=cv2.LINE_AA)

        # 4. 3D Faceted Mirror Disco Ball Sphere
        # Draw base sphere with 3D gradient
        cv2.circle(frame, (ball_cx, ball_cy), ball_r, (70, 70, 75), -1, lineType=cv2.LINE_AA)
        
        # Facet grid lines rotating with perspective
        num_lat = 9
        num_lon = 14
        rot_offset = (t * 1.2) % 1.0

        for i in range(1, num_lat):
            lat_pct = (i / num_lat) * 2 - 1
            lat_r = int(ball_r * math.sqrt(max(0.01, 1 - lat_pct**2)))
            lat_y = int(ball_cy + lat_pct * ball_r * 0.9)
            cv2.ellipse(frame, (ball_cx, lat_y), (lat_r, max(2, int(ball_r * 0.22))), 0, 0, 360, (130, 130, 135), 1, lineType=cv2.LINE_AA)

        for j in range(num_lon):
            lon_phase = ((j / num_lon) + rot_offset) * math.pi
            lon_x = int(ball_cx + ball_r * math.cos(lon_phase))
            # Facet highlights
            glint_brightness = max(0, math.sin(lon_phase * 2 + t * 3.0))
            if glint_brightness > 0.6:
                cv2.line(frame, (lon_x, ball_cy - int(ball_r * 0.8)), (lon_x, ball_cy + int(ball_r * 0.8)), (220, 220, 240), 1, lineType=cv2.LINE_AA)

        # Highlight glint / Specular rim shine
        cv2.circle(frame, (int(ball_cx - ball_r * 0.35), int(ball_cy - ball_r * 0.35)), int(ball_r * 0.28), (240, 240, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (ball_cx, ball_cy), ball_r, (255, 255, 255), 2, lineType=cv2.LINE_AA)

        # Star sparkle bursting from the ball shine
        sparkle_size = int(ball_r * (0.4 + 0.25 * math.sin(t * 6.0)))
        sp_cx = int(ball_cx - ball_r * 0.35)
        sp_cy = int(ball_cy - ball_r * 0.35)
        cv2.line(frame, (sp_cx - sparkle_size, sp_cy), (sp_cx + sparkle_size, sp_cy), (255, 255, 255), 2, lineType=cv2.LINE_AA)
        cv2.line(frame, (sp_cx, sp_cy - sparkle_size), (sp_cx, sp_cy + sparkle_size), (255, 255, 255), 2, lineType=cv2.LINE_AA)

        out.write(frame)


def _render_kinetic_lines_frames(
    out: cv2.VideoWriter,
    w: int,
    h: int,
    total_frames: int,
    fps: int,
    intensity: str = "creative"
):
    """
    Renders sweeping kinetic lines, dark accent swooshes, and glowing speed trails.
    """
    rng = np.random.RandomState(77)
    num_lines = 16 if intensity == "high_energy" else 10
    lines = []
    
    # Palette of sleek neon & dark trails: Electric Cyan, Crisp White, Violet, Amber
    palette = [
        (255, 220, 40),   # Cyan
        (255, 255, 255),  # Pure White
        (240, 100, 180),  # Neon Pink/Purple
        (40, 200, 255),   # Golden Amber
    ]

    for i in range(num_lines):
        y_base = rng.uniform(0.15, 0.85) * h
        lines.append({
            "y": y_base,
            "speed": rng.uniform(0.7, 1.8) * w,
            "length": rng.uniform(0.25, 0.65) * w,
            "thickness": rng.randint(2, 6),
            "color": palette[i % len(palette)],
            "curve_amp": rng.uniform(10, 40),
            "curve_freq": rng.uniform(1.5, 3.5),
            "phase": rng.uniform(0, 2 * math.pi),
        })

    for f in range(total_frames):
        t = f / fps
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        for line in lines:
            # Head of the line sweeping from left to right
            head_x = (t * line["speed"] + line["phase"] * 100) % (w + line["length"] * 2) - line["length"]
            tail_x = head_x - line["length"]

            # Generate smooth sampled curve points
            pts = []
            num_pts = 24
            for p in range(num_pts):
                cur_x = tail_x + (head_x - tail_x) * (p / (num_pts - 1))
                cur_y = line["y"] + line["curve_amp"] * math.sin(cur_x * 0.005 * line["curve_freq"] + t * 4.0)
                pts.append((int(cur_x), int(cur_y)))

            # Draw segmented line with gradient fade toward tail
            for p in range(len(pts) - 1):
                alpha = (p / len(pts)) ** 1.5
                c_scaled = tuple(int(c * alpha) for c in line["color"])
                p1 = pts[p]
                p2 = pts[p + 1]
                if -100 <= p1[0] <= w + 100 and 0 <= p1[1] < h:
                    cv2.line(frame, p1, p2, c_scaled, line["thickness"], lineType=cv2.LINE_AA)

            # Glowing head particle
            if 0 <= head_x < w and 0 <= pts[-1][1] < h:
                cv2.circle(frame, pts[-1], line["thickness"] * 2, (255, 255, 255), -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, pts[-1], line["thickness"] * 4, tuple(c // 2 for c in line["color"]), 1, lineType=cv2.LINE_AA)

        # Subtle Gaussian blur for glowing neon aesthetic
        glow = cv2.GaussianBlur(frame, (15, 15), 0)
        frame = cv2.addWeighted(frame, 1.0, glow, 0.7, 0)
        out.write(frame)


def _render_glitter_frames(
    out: cv2.VideoWriter,
    w: int,
    h: int,
    total_frames: int,
    fps: int,
    intensity: str = "creative",
    face_boxes: Optional[List[Dict[str, Any]]] = None,
):
    """
    Renders floating, shimmering glitter particles and diamond stars with face clearance.
    """
    rng = np.random.RandomState(99)
    num_particles = 40 if intensity == "high_energy" else 28
    particles = []

    palette = [
        (255, 255, 255),  # Crisp White
        (200, 240, 255),  # Warm Cream
        (255, 210, 180),  # Pastel Lavender
        (160, 240, 255),  # Golden Shimmer
    ]

    for i in range(num_particles):
        particles.append({
            "x": rng.uniform(0.05, 0.95) * w,
            "y": rng.uniform(0.05, 0.95) * h,
            "drift_x": rng.uniform(-15, 15),
            "drift_y": rng.uniform(-25, -5), # Gentle upward drift
            "size": rng.randint(4, 12),
            "color": palette[i % len(palette)],
            "twinkle_speed": rng.uniform(2.5, 6.0),
            "phase": rng.uniform(0, 2 * math.pi),
            "is_star": (i % 2 == 0),
        })

    # Build safe face exclusion zones
    safe_zones = []
    if face_boxes:
        for fb in face_boxes:
            fx = fb.get("x", w * 0.3)
            fy = fb.get("y", h * 0.2)
            fw = fb.get("w", w * 0.4)
            fh = fb.get("h", h * 0.4)
            safe_zones.append((fx - 40, fy - 40, fw + 80, fh + 80))

    for f in range(total_frames):
        t = f / fps
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        for p in particles:
            cur_x = (p["x"] + t * p["drift_x"]) % w
            cur_y = (p["y"] + t * p["drift_y"]) % h

            # Check face collision
            in_face = False
            for (zx, zy, zw, zh) in safe_zones:
                if zx <= cur_x <= zx + zw and zy <= cur_y <= zy + zh:
                    in_face = True
                    break
            if in_face:
                continue

            twinkle = max(0.0, math.sin(t * p["twinkle_speed"] + p["phase"]))
            if twinkle < 0.15:
                continue

            c_scaled = tuple(int(c * twinkle) for c in p["color"])
            cx, cy = int(cur_x), int(cur_y)
            s = int(p["size"] * twinkle)

            if p["is_star"] and s >= 3:
                # 4-point diamond star
                cv2.line(frame, (cx - s * 2, cy), (cx + s * 2, cy), c_scaled, 1, lineType=cv2.LINE_AA)
                cv2.line(frame, (cx, cy - s * 2), (cx, cy + s * 2), c_scaled, 1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (cx, cy), max(1, s // 2), (255, 255, 255), -1, lineType=cv2.LINE_AA)
            else:
                # Soft circular mote
                cv2.circle(frame, (cx, cy), max(1, s), c_scaled, -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (cx, cy), max(2, s * 2), tuple(c // 3 for c in c_scaled), 1, lineType=cv2.LINE_AA)

        out.write(frame)
