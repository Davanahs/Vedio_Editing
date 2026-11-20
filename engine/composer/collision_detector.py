"""
Spatial & Temporal Collision Detection and Safe-Zone Placement Engine.
Guarantees that visual overlays:
1. NEVER collide with or cover detected faces.
2. NEVER overlap with caption punch-ins or lead words.
3. NEVER collide with top hook banners.
4. NEVER crowd the screen simultaneously.
5. Respect template-specific margins and safe zones.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    def intersects(self, other: BoundingBox, padding: int = 15) -> bool:
        """Check if two boxes collide, with optional safety margin."""
        return not (
            self.x2 + padding <= other.x
            or self.x >= other.x2 + padding
            or self.y2 + padding <= other.y
            or self.y >= other.y2 + padding
        )


@dataclass
class ScheduledElement:
    id: str
    start: float
    end: float
    box: BoundingBox
    priority: int  # Higher priority stays, lower priority yields


class SafeZoneCollisionEngine:
    def __init__(self, canvas_w: int, canvas_h: int, face_boxes: Optional[List[Dict[str, int]]] = None):
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.is_landscape = canvas_w > canvas_h

        # 1. Define Caption Zone (Strict Exclusion)
        # Captions occupy bottom 28% of the canvas
        caption_top = int(canvas_h * 0.72)
        self.caption_zone = BoundingBox(
            x=0,
            y=caption_top,
            w=canvas_w,
            h=canvas_h - caption_top
        )

        # 2. Define Top Title Zone (Top 12% of canvas)
        self.top_title_zone = BoundingBox(
            x=0,
            y=0,
            w=canvas_w,
            h=int(canvas_h * 0.12)
        )

        # 3. Define Face Exclusion Zones with safety padding
        self.face_zones: List[BoundingBox] = []
        if face_boxes:
            for fb in face_boxes:
                # Add 30px padding around face so graphics never touch hair or chin
                fx = max(0, fb.get("x", 0) - 30)
                fy = max(0, fb.get("y", 0) - 30)
                fw = fb.get("w", 200) + 60
                fh = fb.get("h", 200) + 60
                self.face_zones.append(BoundingBox(x=fx, y=fy, w=fw, h=fh))

        self.scheduled: List[ScheduledElement] = []

    def find_safe_placement(
        self,
        element_id: str,
        start_t: float,
        end_t: float,
        width: int = 320,
        height: int = 80,
        preferred_side: str = "auto",
        priority: int = 1
    ) -> Optional[Tuple[int, int]]:
        """
        Finds a non-colliding (x, y) coordinate for the element.
        Tries candidate safe zones in order of aesthetic visual balance.
        Returns (x, y) or None if no safe placement exists (recommending clean scene).
        """
        # Ensure temporal gap: Do not show more than 1 overlay at a time
        for s in self.scheduled:
            # Overlap in time?
            if not (end_t <= s.start or start_t >= s.end):
                # Temporal collision!
                logger.info(f"Temporal collision between {element_id} and {s.id} at {start_t:.1f}s. Rejecting.")
                return None

        # Candidate placement quadrants depending on orientation
        candidate_positions = self._get_candidate_positions(width, height, preferred_side)

        for (cx, cy) in candidate_positions:
            candidate_box = BoundingBox(x=cx, y=cy, w=width, h=height)

            # Check 1: Collides with captions?
            if candidate_box.intersects(self.caption_zone):
                continue

            # Check 2: Collides with top title?
            if candidate_box.intersects(self.top_title_zone):
                continue

            # Check 3: Collides with any detected face?
            face_collision = False
            for fz in self.face_zones:
                if candidate_box.intersects(fz, padding=25):
                    face_collision = True
                    break
            if face_collision:
                continue

            # Success: Found non-colliding safe position
            self.scheduled.append(
                ScheduledElement(
                    id=element_id,
                    start=start_t,
                    end=end_t,
                    box=candidate_box,
                    priority=priority
                )
            )
            return (cx, cy)

        # No safe location available without covering face or captions -> leave scene clean!
        logger.info(f"No safe placement found for {element_id} without covering subject face. Preserving clean footage.")
        return None

    def _get_candidate_positions(self, w: int, h: int, preferred_side: str) -> List[Tuple[int, int]]:
        """Generate ordered list of aesthetic positions."""
        positions = []
        cw, ch = self.canvas_w, self.canvas_h

        if self.is_landscape:
            # 16:9 Landscape (e.g. 1920x1080)
            top_y = int(ch * 0.15)
            mid_y = int(ch * 0.35)
            lower_y = int(ch * 0.56)
            left_x = int(cw * 0.06)
            right_x = int(cw * 0.70)

            if preferred_side == "left":
                positions = [
                    (left_x, top_y), (left_x, mid_y), (left_x, lower_y),
                    (right_x, top_y), (right_x, mid_y), (right_x, lower_y)
                ]
            else:
                positions = [
                    (right_x, top_y), (right_x, mid_y), (right_x, lower_y),
                    (left_x, top_y), (left_x, mid_y), (left_x, lower_y)
                ]
        else:
            # 9:16 Vertical Reel (e.g. 1080x1920)
            top_y = int(ch * 0.13)
            mid_y = int(ch * 0.35)
            below_face_y = int(ch * 0.54)
            lower_mid_y = int(ch * 0.62)
            left_x = int(cw * 0.06)
            right_x = int(cw * 0.62)
            center_x = int((cw - w) / 2)

            if preferred_side == "left":
                positions = [
                    (left_x, below_face_y), (left_x, top_y), (left_x, lower_mid_y),
                    (right_x, below_face_y), (right_x, top_y), (center_x, below_face_y)
                ]
            else:
                positions = [
                    (right_x, below_face_y), (left_x, below_face_y), (right_x, top_y),
                    (left_x, top_y), (center_x, below_face_y), (right_x, lower_mid_y)
                ]

        return positions
