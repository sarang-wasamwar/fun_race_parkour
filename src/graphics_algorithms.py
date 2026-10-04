"""
Computer Graphics Algorithms used throughout the game.

Every function here is actually used by the rendering pipeline.
The names match what you will present during the viva.

  1. Bresenham Line    -> bresenham_line
  2. Bresenham Circle  -> bresenham_circle
  3. Flood Fill        -> flood_fill (4-connected, stack based)
  4. Translation       -> translate_point
  5. Rotation          -> rotate_point / rotate_vector
  6. Bresenham Polyline-> polyline_bresenham
"""
import math
import pygame


# ============================================================
# 1. BRESENHAM LINE DRAWING
#    Integer-only incremental DDA that never multiplies.
#    We write directly into a pygame Surface via set_at().
# ============================================================
def bresenham_line(x1, y1, x2, y2, color, surface):
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    w, h = surface.get_width(), surface.get_height()

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= x1 < w and 0 <= y1 < h:
            surface.set_at((x1, y1), color)

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


# ============================================================
# 2. BRESENHAM CIRCLE
#    8-way symmetric midpoint circle rasterization.
# ============================================================
def bresenham_circle(cx, cy, radius, color, surface):
    cx, cy, radius = int(cx), int(cy), int(radius)
    if radius <= 0:
        return
    w, h = surface.get_width(), surface.get_height()

    def plot8(px, py):
        for qx, qy in (
            (cx + px, cy + py), (cx - px, cy + py),
            (cx + px, cy - py), (cx - px, cy - py),
            (cx + py, cy + px), (cx - py, cy + px),
            (cx + py, cy - px), (cx - py, cy - px),
        ):
            if 0 <= qx < w and 0 <= qy < h:
                surface.set_at((qx, qy), color)

    x = 0
    y = radius
    d = 3 - 2 * radius

    while x <= y:
        plot8(x, y)
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1


# ============================================================
# 3. FLOOD FILL
#    4-connected, stack-based, works on any Surface.
#    Avoids the unbounded set() of the original version.
# ============================================================
def flood_fill(surface, x, y, fill_color, boundary_color):
    x, y = int(x), int(y)
    w, h = surface.get_width(), surface.get_height()
    if not (0 <= x < w and 0 <= y < h):
        return

    target = surface.get_at((x, y))[:3]
    if target == fill_color or target == boundary_color:
        return

    stack = [(x, y)]
    while stack:
        px, py = stack.pop()
        if not (0 <= px < w and 0 <= py < h):
            continue
        if surface.get_at((px, py))[:3] != target:
            continue

        surface.set_at((px, py), fill_color)

        stack.append((px + 1, py))
        stack.append((px - 1, py))
        stack.append((px, py + 1))
        stack.append((px, py - 1))


# ============================================================
# 4. TRANSLATION
#    x' = x + tx
#    y' = y + ty
# ============================================================
def translate_point(x, y, tx, ty):
    return x + tx, y + ty


# ============================================================
# 5. ROTATION
#    Standard 2-D rotation matrix about an arbitrary pivot.
#
#       | cos -sin |   | x - cx |     | cx |
#       | sin  cos | * | y - cy |  +  | cy |
# ============================================================
def rotate_point(x, y, cx, cy, angle_degrees):
    a = math.radians(angle_degrees)
    ca, sa = math.cos(a), math.sin(a)

    dx, dy = x - cx, y - cy
    rx = dx * ca - dy * sa
    ry = dx * sa + dy * ca
    return rx + cx, ry + cy


def rotate_vector(x, y, angle_degrees):
    return rotate_point(x, y, 0.0, 0.0, angle_degrees)


# ============================================================
# 6. BRESENHAM POLYLINE
#    Convenience helper to rasterize an arbitrary path.
# ============================================================
def polyline_bresenham(points, color, surface):
    for i in range(len(points) - 1):
        bresenham_line(
            points[i][0], points[i][1],
            points[i + 1][0], points[i + 1][1],
            color, surface,
        )