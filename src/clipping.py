"""
Sutherland-Hodgman polygon clipping.

This is the clipping algorithm you requested. It is used in the actual
gameplay loop: when a road-side pole / flag / race banner polygon
crosses the *internal* render frustum, the polygon is clipped before
being drawn. The frustum rectangle is a mathematical boundary - it is
never drawn to the screen.

The algorithm:
  1. For each edge of the clip rectangle (in order L,R,T,B)
     we clip the polygon against the half-plane defined by that edge.
  2. We iterate over every polygon edge (current -> next).
  3. Cases:
        inside -> inside : keep next
        inside -> outside: keep intersection
        outside-> inside : keep intersection, then next
        outside-> outside: keep nothing
"""
from typing import List, Tuple

Point = Tuple[float, float]


def _inside(p: Point, edge: str, bound: float) -> bool:
    x, y = p
    if edge == "left":   return x >= bound
    if edge == "right":  return x <= bound
    if edge == "top":    return y >= bound
    if edge == "bottom": return y <= bound
    return True


def _intersect(p1: Point, p2: Point, edge: str, bound: float) -> Point:
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1

    if edge in ("left", "right"):
        if dx == 0:
            return (bound, y1)
        t = (bound - x1) / dx
    else:
        if dy == 0:
            return (x1, bound)
        t = (bound - y1) / dy

    return (x1 + t * dx, y1 + t * dy)


def clip_polygon(
    polygon: List[Point],
    x_min: float, y_min: float,
    x_max: float, y_max: float,
) -> List[Point]:
    """
    Return the polygon clipped to the axis-aligned rectangle.
    Coordinates are expected to already be in *screen* space.
    """
    if not polygon:
        return []

    edges = [
        ("left",   x_min),
        ("right",  x_max),
        ("top",    y_min),
        ("bottom", y_max),
    ]

    output = list(polygon)
    for edge, bound in edges:
        input_list = output
        output = []
        if not input_list:
            break

        n = len(input_list)
        for i in range(n):
            cur = input_list[i]
            nxt = input_list[(i + 1) % n]

            cur_in = _inside(cur, edge, bound)
            nxt_in = _inside(nxt, edge, bound)

            if cur_in and nxt_in:
                output.append(nxt)
            elif cur_in and not nxt_in:
                output.append(_intersect(cur, nxt, edge, bound))
            elif (not cur_in) and nxt_in:
                output.append(_intersect(cur, nxt, edge, bound))
                output.append(nxt)

    return output


def polygon_is_degenerate(poly: List[Point], eps: float = 1e-3) -> bool:
    if len(poly) < 3:
        return True
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (max(xs) - min(xs) < eps) and (max(ys) - min(ys) < eps)