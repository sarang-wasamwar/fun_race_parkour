"""
Collision helpers. Kept separate so viva questions about collision
detection have a clear home.
"""
import math


def circle_circle(x1, y1, r1, x2, y2, r2) -> bool:
    dx = x1 - x2
    dy = y1 - y2
    r = r1 + r2
    return dx * dx + dy * dy <= r * r


def point_segment_distance(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)