"""
Graphics Algorithm Demo mode.

Renders animated side-by-side visualisations of every algorithm
used in the game. Purely educational - it does NOT interfere with
gameplay.

Controls:
    LEFT / RIGHT  -> previous / next algorithm
    ESC           -> back to menu
"""
import math
import pygame
from . import graphics_algorithms as ga
from .clipping import clip_polygon
from .levels import WHITE, YELLOW, CYAN, GREEN, RED, BLUE, BLACK


DEMOS = [
    ("Bresenham Line",
     "Integer-only incremental line rasterizer.\n"
     "Used for: road edges, lane dashes, HUD frame."),
    ("Bresenham Circle",
     "8-way symmetric midpoint circle.\n"
     "Used for: player, AI, and coin sprites."),
    ("Flood Fill",
     "4-connected stack-based region fill.\n"
     "Used for: road interior, coin interior, obstacle fill."),
    ("Translation",
     "x' = x + tx,  y' = y + ty\n"
     "Used for: camera, road sampling, marker placement."),
    ("Rotation",
     "2-D rotation matrix about a pivot.\n"
     "Used for: curved road generation, rotated obstacles."),
    ("Sutherland-Hodgman Clipping",
     "Clip a polygon to a rectangle before drawing.\n"
     "Used for: race poles / banners entering the view frustum."),
]


class DemoMode:
    def __init__(self, screen, fonts, clock):
        self.screen = screen
        self.fonts = fonts
        self.clock = clock
        self.index = 0
        self.t = 0.0

    # ---------- event ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % len(DEMOS)
                self.t = 0.0
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.index = (self.index - 1) % len(DEMOS)
                self.t = 0.0
        return None

    # ---------- update ----------
    def update(self, dt):
        self.t += dt

    # ---------- draw ----------
    def draw(self):
        scr = self.screen
        scr.fill((14, 14, 22))

        W, H = scr.get_size()

        # Header
        name, desc = DEMOS[self.index]
        title_font = self.fonts["title"]
        body_font = self.fonts["body"]

        pygame.draw.rect(scr, (25, 25, 40), (0, 0, W, 90))
        pygame.draw.line(scr, CYAN, (0, 90), (W, 90), 2)

        t_surf = title_font.render(name, True, YELLOW)
        scr.blit(t_surf, (30, 18))

        for i, line in enumerate(desc.split("\n")):
            s = body_font.render(line, True, WHITE)
            scr.blit(s, (30, 58 + i * 20))

        # Demo canvas
        canvas = pygame.Rect(40, 130, W - 80, H - 200)
        pygame.draw.rect(scr, (18, 18, 28), canvas)
        pygame.draw.rect(scr, (60, 60, 90), canvas, 2)

        # Offset: sub-surface
        sub = scr.subsurface(canvas)

        fn = [
            self._demo_bresenham_line,
            self._demo_bresenham_circle,
            self._demo_flood_fill,
            self._demo_translation,
            self._demo_rotation,
            self._demo_clipping,
        ][self.index]
        fn(sub)

        # Footer
        hint = body_font.render(
            "LEFT / RIGHT: switch algorithm    ESC: back to menu",
            True, (180, 180, 200),
        )
        scr.blit(hint, hint.get_rect(center=(W // 2, H - 30)))

        # Index marker
        idx = body_font.render(
            f"{self.index + 1} / {len(DEMOS)}", True, CYAN)
        scr.blit(idx, idx.get_rect(topright=(W - 30, 30)))

    # ---------------------------------------------------------
    # individual demos
    # ---------------------------------------------------------
    def _demo_bresenham_line(self, surf):
        w, h = surf.get_size()
        # Animate endpoint along an arc.
        cx, cy = w // 2, h // 2
        r = min(w, h) // 3
        ang = self.t * 1.2
        x2 = int(cx + r * math.cos(ang))
        y2 = int(cy + r * math.sin(ang))
        ga.bresenham_line(40, h - 40, x2, y2, YELLOW, surf)
        ga.bresenham_line(w - 40, h - 40, x2, y2, CYAN, surf)

    def _demo_bresenham_circle(self, surf):
        w, h = surf.get_size()
        cx, cy = w // 2, h // 2
        radius = int(40 + 60 * (0.5 + 0.5 * math.sin(self.t * 2)))
        # Rings
        for i, r in enumerate(range(radius, radius + 30, 10)):
            color = [YELLOW, CYAN, WHITE][i % 3]
            ga.bresenham_circle(cx, cy, r, color, surf)
        ga.bresenham_line(cx, cy, cx + radius, cy, (90, 90, 120), surf)

    def _demo_flood_fill(self, surf):
        w, h = surf.get_size()
        # Draw a rectangular boundary; flood fill interior once and cache.
        if getattr(self, "_ff_cache", None) is None or self._ff_dirty():
            self._ff_cache = pygame.Surface((w, h))
            self._ff_cache.fill((0, 0, 0))
            rect = pygame.Rect(60, 40, w - 120, h - 80)
            ga.bresenham_line(rect.left,  rect.top,    rect.right, rect.top,    WHITE, self._ff_cache)
            ga.bresenham_line(rect.right, rect.top,    rect.right, rect.bottom, WHITE, self._ff_cache)
            ga.bresenham_line(rect.right, rect.bottom, rect.left,  rect.bottom, WHITE, self._ff_cache)
            ga.bresenham_line(rect.left,  rect.bottom, rect.left,  rect.top,    WHITE, self._ff_cache)
            ga.flood_fill(self._ff_cache, w // 2, h // 2,
                          (60, 130, 220), WHITE)
            self._ff_size = (w, h)
        surf.blit(self._ff_cache, (0, 0))

    def _ff_dirty(self):
        return getattr(self, "_ff_size", None) != surf_size(self)

    def surf_size(self):
        return self.screen.get_size()

    def _demo_translation(self, surf):
        w, h = surf.get_size()
        cx, cy = w // 2, h // 2
        # Draw a moving square (its position is a translation)
        for i in range(6):
            t = (self.t * 1.2 + i * 0.4) % 1.0
            x = int(60 + t * (w - 200))
            y = cy + int(math.sin(self.t * 2 + i) * 60)
            pygame.draw.rect(surf, [YELLOW, CYAN, GREEN][i % 3],
                             (x, y, 40, 40), 2)

    def _demo_rotation(self, surf):
        w, h = surf.get_size()
        cx, cy = w // 2, h // 2
        angle = math.degrees(self.t * 0.8)

        # A square rotated about its centre
        base_pts = [(-60, -60), (60, -60), (60, 60), (-60, 60)]
        rotated = [ga.rotate_point(x, y, 0, 0, angle) for x, y in base_pts]
        scr_pts = [(cx + x, cy + y) for x, y in rotated]

        # Use Bresenham to draw edges
        for i in range(4):
            p1 = scr_pts[i]
            p2 = scr_pts[(i + 1) % 4]
            ga.bresenham_line(p1[0], p1[1], p2[0], p2[1], YELLOW, surf)

        # Pivot marker
        ga.bresenham_circle(cx, cy, 4, RED, surf)

    def _demo_clipping(self, surf):
        w, h = surf.get_size()

        # Internal clip rectangle (NOT drawn as a filled object)
        margin = 60
        cx0, cy0 = margin, margin
        cx1, cy1 = w - margin, h - margin

        # Show the clip boundary as a thin dashed guide
        _dashed_rect(surf, cx0, cy0, cx1, cy1, (80, 80, 110))

        # A large polygon sliding right, crossing the clip boundary
        cx, cy = w // 2, h // 2
        t = (self.t * 0.6) % 2.0
        offset = -100 + t * 200

        poly = [
            (cx - 180 + offset, cy - 120),
            (cx + 180 + offset, cy - 80),
            (cx + 140 + offset, cy + 120),
            (cx - 160 + offset, cy + 90),
        ]

        # Unclipped: outline in dim colour
        for i in range(4):
            p1, p2 = poly[i], poly[(i + 1) % 4]
            ga.bresenham_line(p1[0], p1[1], p2[0], p2[1],
                              (90, 90, 120), surf)

        # Clipped polygon
        clipped = clip_polygon(poly, cx0, cy0, cx1, cy1)
        if len(clipped) >= 3:
            # Fill clipped polygon using flood fill from its centre
            xs = [p[0] for p in clipped]
            ys = [p[1] for p in clipped]
            # Draw edges with Bresenham
            for i in range(len(clipped)):
                p1 = clipped[i]
                p2 = clipped[(i + 1) % len(clipped)]
                ga.bresenham_line(p1[0], p1[1], p2[0], p2[1],
                                  YELLOW, surf)

            # Optional fill using a temp surface to avoid flooding the screen
            minx, maxx = int(min(xs)) + 1, int(max(xs))
            miny, maxy = int(min(ys)) + 1, int(max(ys))
            if maxx > minx and maxy > miny:
                try:
                    ga.flood_fill(surf, (minx + maxx) // 2,
                                  (miny + maxy) // 2,
                                  (170, 130, 40), YELLOW)
                except Exception:
                    pass


def _demo_flood_fill(self, surf):
    w, h = surf.get_size()
    # Build a filled rectangle ONCE for this canvas size, cache it.
    if getattr(self, "_ff_cache", None) is None or \
        getattr(self, "_ff_size", None) != (w, h):
        self._ff_cache = pygame.Surface((w, h))
        self._ff_cache.fill((0, 0, 0))
        rect = pygame.Rect(60, 40, w - 120, h - 80)
        ga.bresenham_line(rect.left,  rect.top,    rect.right, rect.top,    WHITE, self._ff_cache)
        ga.bresenham_line(rect.right, rect.top,    rect.right, rect.bottom, WHITE, self._ff_cache)
        ga.bresenham_line(rect.right, rect.bottom, rect.left,  rect.bottom, WHITE, self._ff_cache)
        ga.bresenham_line(rect.left,  rect.bottom, rect.left,  rect.top,    WHITE, self._ff_cache)
        ga.flood_fill(self._ff_cache, w // 2, h // 2,
                        (60, 130, 220), WHITE)
        self._ff_size = (w, h)
    surf.blit(self._ff_cache, (0, 0))