"""
Fun Race & Parkour - Graphics Algorithms
Core game module.

Contains:
    * Game state machine (MENU, LEVEL_SELECT, PLAYING, PAUSED, ...)
    * Data-driven world generation from src.levels.TrackSpec
    * Player / AI racers, coins, obstacles, speed bumps
    * Bresenham + Flood Fill based rendering, Sutherland-Hodgman clipping
    * Polished HUD, pause overlay, results screen
"""
import math
import random
import sys
import os
import pygame

from . import graphics_algorithms as ga
from .clipping import clip_polygon, polygon_is_degenerate
from .collision import circle_circle
from .levels import (
    ALL_LEVELS, TrackSpec, get_level,
    BLACK, WHITE, RED, BLUE, GREEN, YELLOW, CYAN, ORANGE,
    ROAD_COLOR, ROAD_EDGE_COLOR, GRASS_COLOR,
)
from .ui import Button, draw_text, overlay
from .demo import DemoMode
from .resources import FONTS_DIR
from . import states as st


# ============================================================
# Window / constants
# ============================================================
SCREEN_W, SCREEN_H = 1000, 700
FPS = 60

ROAD_WIDTH = 180
ROAD_HALF_WIDTH = ROAD_WIDTH // 2
LANE_WIDTH = ROAD_WIDTH / 3
COIN_RADIUS = 12
COIN_COLLECT_DISTANCE = 28

CHECKPOINT_SPACING = 900.0
STUN_DURATION = 0.65
SPEED_BUMP_SPEED = 100.0
SPEED_BUMP_DURATION = 0.5

# Race start countdown
COUNTDOWN_TIME = 3.0
GO_DISPLAY_TIME = 0.7

# The clip rectangle used by Sutherland-Hodgman when drawing race
# poles. It is a mathematical boundary that corresponds to the
# visible screen area - it is NEVER drawn to the screen.
CLIP_MARGIN = 0


# ============================================================
# Racer
# ============================================================
class Racer:
    def __init__(self, name, color, lane, is_player=False,
                 ai_speed=110.0, reaction=1.0, risk=0.5):
        self.name = name
        self.color = color
        self.lane = lane
        self.is_player = is_player

        self.ai_speed = ai_speed
        self.reaction = reaction
        self.risk = risk

        self.position = 0.0
        self.checkpoint = 0.0
        self.speed = 0.0

        self.finished = False
        self.finish_time = None
        self.collision_count = 0
        self.stun_timer = 0.0
        self.speed_bump_timer = 0.0

    def reset(self):
        self.position = 0.0
        self.checkpoint = 0.0
        self.speed = 0.0
        self.finished = False
        self.finish_time = None
        self.collision_count = 0
        self.stun_timer = 0.0
        self.speed_bump_timer = 0.0


# ============================================================
# Coin / Obstacle / SpeedBump
# ============================================================
class Coin:
    __slots__ = ("position", "lane", "collected", "phase")
    def __init__(self, position, lane=0):
        self.position = position
        self.lane = lane
        self.collected = False
        self.phase = random.random() * math.tau


class Obstacle:
    __slots__ = ("position", "offset", "speed", "direction", "_surface")
    def __init__(self, position, speed, start_side=1):
        self.position = position
        self.offset = (-ROAD_HALF_WIDTH + 25) if start_side == 1 \
            else (ROAD_HALF_WIDTH - 25)
        self.speed = speed
        self.direction = 1 if start_side == 1 else -1
        self._surface = None

    def update(self, dt):
        self.offset += self.speed * self.direction * dt
        limit = ROAD_HALF_WIDTH - 25
        if self.offset >= limit:
            self.offset = limit
            self.direction = -1
        elif self.offset <= -limit:
            self.offset = -limit
            self.direction = 1


class SpeedBump:
    __slots__ = ("position", "width", "height", "_surface")
    def __init__(self, position):
        self.position = position
        self.width = ROAD_WIDTH + 10
        self.height = 40
        self._surface = None


# ============================================================
# Sprite cache
# ============================================================
_racer_sprite_cache = {}
_coin_sprite = None
_obstacle_cache = {}


def _make_racer_sprite(color, outer_r, inner_r):
    key = (color, outer_r, inner_r)
    if key in _racer_sprite_cache:
        return _racer_sprite_cache[key]

    size = outer_r * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    ga.bresenham_circle(cx, cy, outer_r, BLACK, surf)
    ga.flood_fill(surf, cx, cy, BLACK, BLACK)
    ga.bresenham_circle(cx, cy, inner_r, color, surf)
    ga.flood_fill(surf, cx, cy, color, WHITE)
    ga.bresenham_circle(cx, cy, inner_r, WHITE, surf)

    _racer_sprite_cache[key] = surf
    return surf


def _make_coin_sprite():
    global _coin_sprite
    if _coin_sprite is not None:
        return _coin_sprite

    size = (COIN_RADIUS + 5) * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    ga.bresenham_circle(cx + 2, cy + 2, COIN_RADIUS + 2, BLACK, surf)
    ga.flood_fill(surf, cx + 2, cy + 2, BLACK, BLACK)

    ga.bresenham_circle(cx, cy, COIN_RADIUS, ORANGE, surf)
    ga.flood_fill(surf, cx, cy, YELLOW, ORANGE)
    ga.bresenham_circle(cx, cy, COIN_RADIUS - 4, ORANGE, surf)
    ga.bresenham_circle(cx - 4, cy - 4, 3, WHITE, surf)
    ga.flood_fill(surf, cx - 4, cy - 4, WHITE, WHITE)

    _coin_sprite = surf
    return _coin_sprite


def _make_obstacle_sprite(angle_deg):
    key = int(angle_deg) % 360
    if key in _obstacle_cache:
        return _obstacle_cache[key]

    base = pygame.Surface((90, 64), pygame.SRCALPHA)
    pts = [(10, 10), (80, 10), (80, 54), (10, 54)]
    for i in range(4):
        ga.bresenham_line(*pts[i], *pts[(i + 1) % 4], BLACK, base)
    ga.flood_fill(base, 45, 32, ORANGE, BLACK)

    inner = [(19, 19), (71, 19), (71, 45), (19, 45)]
    for i in range(4):
        ga.bresenham_line(*inner[i], *inner[(i + 1) % 4], RED, base)
    ga.flood_fill(base, 45, 32, RED, RED)
    ga.bresenham_line(27, 32, 63, 32, WHITE, base)

    rotated = pygame.transform.rotate(base, -angle_deg)
    _obstacle_cache[key] = rotated
    return rotated


def _make_speed_bump_sprite(angle_deg):
    key = ("bump", int(angle_deg) % 360)
    if key in _obstacle_cache:
        return _obstacle_cache[key]

    width = ROAD_WIDTH + 30
    height = 60
    base = pygame.Surface((width, height), pygame.SRCALPHA)

    left, right = 5, width - 5
    top, bottom = 5, height - 5
    ga.bresenham_line(left, top, right, top, BLACK, base)
    ga.bresenham_line(right, top, right, bottom, BLACK, base)
    ga.bresenham_line(right, bottom, left, bottom, BLACK, base)
    ga.bresenham_line(left, bottom, left, top, BLACK, base)
    ga.flood_fill(base, width // 2, height // 2, YELLOW, BLACK)

    for x in range(left - 10, right, 45):
        ga.bresenham_line(x, bottom, x + 18, top, BLACK, base)
        ga.bresenham_line(x + 1, bottom, x + 19, top, BLACK, base)
        ga.bresenham_line(x + 2, bottom, x + 20, top, BLACK, base)

    ga.bresenham_line(left + 5, top + 3, right - 5, top + 3, WHITE, base)

    rotated = pygame.transform.rotate(base, -angle_deg)
    _obstacle_cache[key] = rotated
    return rotated


# ============================================================
# Track / World
# ============================================================
class Track:
    """
    Encapsulates everything that depends on a level: road geometry,
    obstacles, coins, AI opponents, road surface.
    """
    def __init__(self, spec: TrackSpec):
        self.spec = spec

        self.points = []
        self.distances = []
        self.tangents = []
        self.total_length = 0.0

        self.obstacles = []
        self.speed_bumps = []
        self.coins = []
        self.racers = []

        self.road_surface = None
        self.road_origin = (0, 0)

        self.finish_position = 0.0
        self.player_speed = spec.player_speed
        self.max_reverse = spec.max_reverse
        self.default_ai_speed = spec.default_ai_speed

        self._build()

    # ---------- geometry ----------
    def _build(self):
        self._generate_road()
        self._build_road_surface()
        self._create_entities()
        self.finish_position = self.total_length - 80.0

    def _generate_road(self):
        pts = [(0.0, 350.0)]
        heading = 0.0
        x, y = pts[0]
        step = 10.0

        for cmd in self.spec.road_commands:
            if cmd[0] == "straight":
                dist = cmd[1]
                n = max(1, int(dist / step))
                for _ in range(n):
                    dx, dy = ga.rotate_vector(step, 0, heading)
                    x, y = ga.translate_point(x, y, dx, dy)
                    pts.append((x, y))
            else:
                _, turn_angle, radius = cmd
                arc = radius * math.radians(abs(turn_angle))
                n = max(2, int(arc / step))
                a_step = turn_angle / n
                for _ in range(n):
                    dx, dy = ga.rotate_vector(step, 0, heading)
                    x, y = ga.translate_point(x, y, dx, dy)
                    pts.append((x, y))
                    heading += a_step

        self.points = pts
        self.distances = [0.0]
        self.tangents = []
        total = 0.0

        for i in range(len(pts)):
            if i == 0:
                dx = pts[1][0] - pts[0][0]
                dy = pts[1][1] - pts[0][1]
            elif i == len(pts) - 1:
                dx = pts[-1][0] - pts[-2][0]
                dy = pts[-1][1] - pts[-2][1]
            else:
                dx = pts[i + 1][0] - pts[i - 1][0]
                dy = pts[i + 1][1] - pts[i - 1][1]

            length = math.hypot(dx, dy)
            tangent = (1.0, 0.0) if length == 0 else (dx / length, dy / length)
            self.tangents.append(tangent)

            if i > 0:
                seg = math.hypot(pts[i][0] - pts[i - 1][0],
                                 pts[i][1] - pts[i - 1][1])
                total += seg
                self.distances.append(total)

        self.total_length = total

    def road_position(self, position):
        position = max(0.0, min(position, self.total_length))
        dists = self.distances
        for i in range(1, len(dists)):
            if position <= dists[i]:
                prev = dists[i - 1]
                seg = dists[i] - prev
                ratio = 0.0 if seg == 0 else (position - prev) / seg
                x1, y1 = self.points[i - 1]
                x2, y2 = self.points[i]
                x = x1 + (x2 - x1) * ratio
                y = y1 + (y2 - y1) * ratio
                tx, ty = self.tangents[i]
                return x, y, tx, ty

        x, y = self.points[-1]
        tx, ty = self.tangents[-1]
        return x, y, tx, ty

    def world_position(self, position, offset=0.0):
        x, y, tx, ty = self.road_position(position)
        nx, ny = -ty, tx
        return ga.translate_point(x, y, nx * offset, ny * offset)

    # ---------- road surface ----------
    def _build_road_surface(self):
        min_x = int(min(p[0] for p in self.points)) - ROAD_WIDTH - 20
        max_x = int(max(p[0] for p in self.points)) + ROAD_WIDTH + 20
        min_y = int(min(p[1] for p in self.points)) - ROAD_WIDTH - 20
        max_y = int(max(p[1] for p in self.points)) + ROAD_WIDTH + 20

        w = max_x - min_x + 1
        h = max_y - min_y + 1
        self.road_origin = (min_x, min_y)

        surf = pygame.Surface((w, h))
        surf.fill(self.spec.grass_color)
        self.road_surface = surf

        def local(x, y):
            return int(x - min_x), int(y - min_y)

        left_pts, right_pts = [], []
        for i, (x, y) in enumerate(self.points):
            tx, ty = self.tangents[i]
            nx, ny = -ty, tx
            left_pts.append(local(x + nx * ROAD_HALF_WIDTH,
                                  y + ny * ROAD_HALF_WIDTH))
            right_pts.append(local(x - nx * ROAD_HALF_WIDTH,
                                   y - ny * ROAD_HALF_WIDTH))

        for i in range(len(left_pts) - 1):
            ga.bresenham_line(*left_pts[i], *left_pts[i + 1],
                              ROAD_EDGE_COLOR, surf)
            ga.bresenham_line(*right_pts[i], *right_pts[i + 1],
                              ROAD_EDGE_COLOR, surf)

        ga.bresenham_line(*left_pts[0], *right_pts[0],
                          ROAD_EDGE_COLOR, surf)
        ga.bresenham_line(*left_pts[-1], *right_pts[-1],
                          ROAD_EDGE_COLOR, surf)

        mid = self.points[len(self.points) // 2]
        sx, sy = local(*mid)
        ga.flood_fill(surf, sx, sy, ROAD_COLOR, ROAD_EDGE_COLOR)

        pos = 0.0
        while pos < self.total_length:
            dash_end = min(pos + 35, self.total_length)
            for lane_offset in (-LANE_WIDTH / 2, LANE_WIDTH / 2):
                pts = []
                p = pos
                while p <= dash_end:
                    x, y = self.world_position(p, lane_offset)
                    pts.append(local(x, y))
                    p += 8
                ga.polyline_bresenham(pts, WHITE, surf)
            pos += 70

    # ---------- entities ----------
    def _create_entities(self):
        for o in self.spec.obstacles:
            self.obstacles.append(Obstacle(o.position, o.speed, o.start_side))

        for b in self.spec.speed_bumps:
            self.speed_bumps.append(SpeedBump(b.position))

        self.coins = []
        pos = self.spec.coin_start
        i = 0
        while pos < self.total_length - self.spec.coin_end_margin:
            lane = [0, -1, 1][i % 3]
            self.coins.append(Coin(pos, lane))
            pos += self.spec.coin_spacing
            i += 1

        self.racers = [Racer("YOU", RED, 0, is_player=True)]
        for ai in self.spec.ai_opponents:
            self.racers.append(
                Racer(ai.name, ai.color, ai.lane, is_player=False,
                      ai_speed=ai.ai_speed, reaction=ai.reaction,
                      risk=ai.risk)
            )

    # ---------- update ----------
    def update_ai(self, racer, dt):
        if racer.finished:
            return
        if racer.stun_timer > 0:
            racer.stun_timer -= dt
            return

        nearest, ndist = self._nearest_obstacle_ahead(racer.position)
        target = racer.ai_speed

        if nearest is not None and not isinstance(nearest, SpeedBump):
            rel = abs(nearest.offset)
            if racer.risk < 0.5:
                if ndist < 350 and rel < 55: target = 120
                if ndist < 200 and rel < 60: target = 65
                if ndist < 100 and rel < 65: target = 35
            else:
                if ndist < 250 and rel < 45: target = 170
                if ndist < 130 and rel < 50: target = 110
                if ndist < 70  and rel < 55: target = 50

        if racer.speed_bump_timer > 0:
            racer.speed_bump_timer -= dt
            target = min(target, SPEED_BUMP_SPEED)

        if racer.speed < target:
            racer.speed += 400 * racer.reaction * dt
            if racer.speed > target:
                racer.speed = target
        elif racer.speed > target:
            racer.speed -= 500 * racer.reaction * dt
            if racer.speed < target:
                racer.speed = target

        racer.position += racer.speed * dt
        racer.position = min(racer.position, self.finish_position)

        self._update_checkpoint(racer)
        self._handle_collision(racer)

    def _nearest_obstacle_ahead(self, position):
        best, best_d = None, float("inf")
        all_obs = self.obstacles + self.speed_bumps
        for o in all_obs:
            d = o.position - position
            if 0 < d < best_d:
                best, best_d = o, d
        return best, best_d

    def _update_checkpoint(self, racer):
        cp = int(racer.position // CHECKPOINT_SPACING) * CHECKPOINT_SPACING
        if cp > racer.checkpoint:
            racer.checkpoint = cp

    def _handle_collision(self, racer):
        if racer.finished:
            return

        for b in self.speed_bumps:
            if abs(racer.position - b.position) < 30:
                racer.speed_bump_timer = SPEED_BUMP_DURATION
                break

        rx, ry = self.world_position(racer.position, racer.lane * LANE_WIDTH)
        for o in self.obstacles:
            if abs(racer.position - o.position) > 60:
                continue
            ox, oy = self.world_position(o.position, o.offset)
            if circle_circle(rx, ry, 30, ox, oy, 22):
                racer.position = max(0.0, racer.checkpoint - 15)
                racer.speed = 0.0
                racer.stun_timer = STUN_DURATION
                racer.collision_count += 1
                return

    def collect_coins(self, racer, counter):
        if not racer.is_player:
            return
        rx, ry = self.world_position(racer.position,
                                     racer.lane * LANE_WIDTH)
        for c in self.coins:
            if c.collected:
                continue
            cx, cy = self.world_position(c.position, c.lane * LANE_WIDTH)
            if circle_circle(rx, ry, COIN_COLLECT_DISTANCE, cx, cy, 0):
                c.collected = True
                counter[0] += 1

    def reset(self):
        for r in self.racers:
            r.reset()
        for c in self.coins:
            c.collected = False
        for o in self.obstacles:
            side = 1 if random.random() < 0.5 else -1
            o.offset = (-ROAD_HALF_WIDTH + 25) if side == 1 \
                else (ROAD_HALF_WIDTH - 25)
            o.direction = side


# ============================================================
# Game
# ============================================================
class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.audio_ok = True
        except pygame.error:
            self.audio_ok = False

        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Fun Race & Parkour - Graphics Algorithms")
        self.clock = pygame.time.Clock()

        self.fonts = self._load_fonts()
        self.sm = st.StateMachine(st.MENU)

        self.selected_level_index = 0
        self.track = None

        self.race_time = 0.0
        self.race_started = False
        self.countdown = COUNTDOWN_TIME
        self.winner = None
        self.coin_count = [0]

        self.camera_x = 0.0
        self.camera_y = 0.0

        self.demo = DemoMode(self.screen, self.fonts, self.clock)

        self.menu_buttons = []
        self.level_buttons = []
        self.pause_buttons = []
        self.result_buttons = []
        self._build_buttons()

    # ---------- fonts ----------
    def _load_fonts(self):
        custom = os.path.join(FONTS_DIR, "game.ttf")
        if os.path.exists(custom):
            def load(sz):
                return pygame.font.Font(custom, sz)
        else:
            def load(sz):
                return pygame.font.Font(None, sz)
        return {
            "title": load(58),
            "big":   load(46),
            "h1":    load(38),
            "body":  load(24),
            "small": load(20),
        }

    # ---------- buttons ----------
    def _build_buttons(self):
        f = self.fonts["body"]
        f_big = self.fonts["big"]
        cx = SCREEN_W // 2

        self.menu_buttons = [
            Button((cx - 150, 250, 300, 50), "PLAY",         "play",         f),
            Button((cx - 150, 310, 300, 50), "LEVEL SELECT", "level_select", f),
            Button((cx - 150, 370, 300, 50), "INSTRUCTIONS", "instructions", f),
            Button((cx - 150, 430, 300, 50), "ALGORITHMS",   "algo_info",    f),
            Button((cx - 150, 490, 300, 50), "CREDITS",      "credits",      f),
            Button((cx - 150, 550, 300, 50), "EXIT",         "quit",         f),
        ]

        self.level_buttons = []
        for i, lvl in enumerate(ALL_LEVELS):
            y = 220 + i * 90
            label = f"{lvl.display_name}   [{lvl.difficulty}]"
            self.level_buttons.append(
                Button((cx - 280, y, 560, 60), label, f"lvl:{lvl.key}",
                       f_big, color=lvl.difficulty_color)
            )
        self.level_buttons.append(
            Button((cx - 150, 560, 300, 50), "BACK", "menu", f)
        )

        self.pause_buttons = [
            Button((cx - 150, 280, 300, 50), "RESUME",    "resume",  f),
            Button((cx - 150, 340, 300, 50), "RESTART",   "restart", f),
            Button((cx - 150, 400, 300, 50), "MAIN MENU", "menu",    f),
            Button((cx - 150, 460, 300, 50), "QUIT",      "quit",    f),
        ]

        self.result_buttons = [
            Button((cx - 150, 470, 300, 50), "RACE AGAIN", "restart", f),
            Button((cx - 150, 530, 300, 50), "NEXT LEVEL", "next",    f),
            Button((cx - 150, 590, 300, 50), "MAIN MENU",  "menu",    f),
        ]

    # --------------------------------------------------------
    # State helpers
    # --------------------------------------------------------
    def set_state(self, new_state):
        self.sm.set(new_state)

    # --------------------------------------------------------
    # Level start / restart
    # --------------------------------------------------------
    def start_level(self, level_key: str):
        spec = get_level(level_key)
        if spec is None:
            return
        self.track = Track(spec)
        self.selected_level_index = ALL_LEVELS.index(spec)
        self.race_time = 0.0
        self.race_started = False
        self.countdown = COUNTDOWN_TIME
        self.winner = None
        self.coin_count = [0]

        sx, sy = self.track.world_position(0.0)
        self.camera_x = sx - SCREEN_W // 2
        self.camera_y = sy - SCREEN_H // 2

        self.set_state(st.PLAYING)

    def restart_level(self):
        if self.track is None:
            return
        self.track.reset()
        self.race_time = 0.0
        self.race_started = False
        self.countdown = COUNTDOWN_TIME
        self.winner = None
        self.coin_count = [0]
        sx, sy = self.track.world_position(0.0)
        self.camera_x = sx - SCREEN_W // 2
        self.camera_y = sy - SCREEN_H // 2
        self.set_state(st.PLAYING)

    # --------------------------------------------------------
    # Main loop
    # --------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif self._handle_event(ev) == "quit":
                    running = False

            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # --------------------------------------------------------
    # Event dispatch
    # --------------------------------------------------------
    def _handle_event(self, event):
        s = self.sm.current
        if s == st.MENU:
            return self._handle_menu(event)
        if s == st.LEVEL_SELECT:
            return self._handle_level_select(event)
        if s == st.PLAYING:
            return self._handle_playing(event)
        if s == st.PAUSED:
            return self._handle_pause(event)
        if s in (st.LEVEL_COMPLETE, st.GAME_OVER):
            return self._handle_result(event)
        if s in (st.INSTRUCTIONS, st.CREDITS):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.set_state(st.MENU)
            return None
        if s == st.DEMO:
            r = self.demo.handle_event(event)
            if r == "menu":
                self.set_state(st.MENU)
            return None
        return None

    def _handle_menu(self, event):
        for b in self.menu_buttons:
            r = b.handle_event(event)
            if r:
                return self._menu_action(r)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "quit"
            if event.key == pygame.K_RETURN:
                return self._menu_action("play")
        return None

    def _menu_action(self, action):
        if action == "play":
            self.start_level(ALL_LEVELS[self.selected_level_index].key)
        elif action == "level_select":
            self.set_state(st.LEVEL_SELECT)
        elif action == "instructions":
            self.set_state(st.INSTRUCTIONS)
        elif action == "algo_info":
            self.set_state(st.DEMO)
        elif action == "credits":
            self.set_state(st.CREDITS)
        elif action == "quit":
            return "quit"
        return None

    def _handle_level_select(self, event):
        for b in self.level_buttons:
            r = b.handle_event(event)
            if r:
                if r.startswith("lvl:"):
                    self.start_level(r.split(":", 1)[1])
                elif r == "menu":
                    self.set_state(st.MENU)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.set_state(st.MENU)
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = event.key - pygame.K_1
                if idx < len(ALL_LEVELS):
                    self.start_level(ALL_LEVELS[idx].key)
        return None

    def _handle_playing(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.set_state(st.PAUSED)
            elif event.key == pygame.K_r:
                self.restart_level()
        return None

    def _handle_pause(self, event):
        for b in self.pause_buttons:
            r = b.handle_event(event)
            if r:
                if r == "resume":
                    self.set_state(st.PLAYING)
                elif r == "restart":
                    self.restart_level()
                elif r == "menu":
                    self.set_state(st.MENU)
                elif r == "quit":
                    return "quit"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.set_state(st.PLAYING)
        return None

    def _handle_result(self, event):
        for b in self.result_buttons:
            r = b.handle_event(event)
            if r:
                if r == "restart":
                    self.restart_level()
                elif r == "next":
                    idx = self.selected_level_index + 1
                    if idx < len(ALL_LEVELS):
                        self.start_level(ALL_LEVELS[idx].key)
                    else:
                        self.set_state(st.MENU)
                elif r == "menu":
                    self.set_state(st.MENU)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.set_state(st.MENU)
            elif event.key == pygame.K_r:
                self.restart_level()
        return None

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------
    def _update(self, dt):
        s = self.sm.current
        if s == st.DEMO:
            self.demo.update(dt)
        elif s == st.PLAYING:
            self._update_playing(dt)

    def _update_playing(self, dt):
        t = self.track
        if t is None:
            return

        if not self.race_started:
            self.countdown -= dt
            if self.countdown <= -GO_DISPLAY_TIME:
                self.countdown = 0.0
                self.race_started = True
            return

        if self.winner is not None:
            return

        self.race_time += dt
        player = t.racers[0]

        keys = pygame.key.get_pressed()
        accel = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        brake = keys[pygame.K_LEFT] or keys[pygame.K_a]

        if player.stun_timer > 0:
            player.stun_timer -= dt
            player.speed = 0.0
        else:
            if player.speed_bump_timer > 0:
                player.speed_bump_timer -= dt
                if accel:
                    player.speed = SPEED_BUMP_SPEED
                elif brake:
                    player.speed = -SPEED_BUMP_SPEED
                else:
                    player.speed = 0.0
            else:
                if accel:
                    player.speed = t.player_speed
                elif brake:
                    player.speed = -t.max_reverse
                else:
                    player.speed = 0.0

            player.position += player.speed * dt
            player.position = max(0.0,
                                  min(player.position, t.finish_position))
            t._update_checkpoint(player)
            t._handle_collision(player)
            t.collect_coins(player, self.coin_count)

        for r in t.racers[1:]:
            t.update_ai(r, dt)

        for o in t.obstacles:
            o.update(dt)

        for r in t.racers:
            if not r.finished and r.position >= t.finish_position:
                r.finished = True
                r.finish_time = self.race_time
                if self.winner is None:
                    self.winner = r
                    self.set_state(st.LEVEL_COMPLETE if r.is_player
                                   else st.GAME_OVER)

        px, py = t.world_position(player.position)
        tx = px - SCREEN_W // 2
        ty = py - SCREEN_H // 2
        self.camera_x += (tx - self.camera_x) * min(1.0, 7.0 * dt)
        self.camera_y += (ty - self.camera_y) * min(1.0, 7.0 * dt)

    # --------------------------------------------------------
    # Draw
    # --------------------------------------------------------
    def _draw(self):
        s = self.sm.current
        if s == st.MENU:
            self._draw_menu()
        elif s == st.LEVEL_SELECT:
            self._draw_level_select()
        elif s in (st.PLAYING, st.PAUSED):
            self._draw_playing()
            if s == st.PAUSED:
                self._draw_pause()
        elif s in (st.LEVEL_COMPLETE, st.GAME_OVER):
            self._draw_playing()
            self._draw_result()
        elif s == st.INSTRUCTIONS:
            self._draw_instructions()
        elif s == st.CREDITS:
            self._draw_credits()
        elif s == st.DEMO:
            self.demo.draw()

    def _draw_menu(self):
        scr = self.screen
        scr.fill((12, 12, 20))

        for i in range(0, SCREEN_W, 40):
            ga.bresenham_line(i, SCREEN_H, SCREEN_W // 2,
                              SCREEN_H // 2 - 200, (25, 25, 45), scr)

        draw_text(scr, "FUN RACE & PARKOUR", self.fonts["title"], YELLOW,
                  center=(SCREEN_W // 2, 90))
        draw_text(scr, "- Graphics Algorithms Edition -",
                  self.fonts["body"], CYAN,
                  center=(SCREEN_W // 2, 150))

        car = _make_racer_sprite(RED, 22, 15)
        scr.blit(car, car.get_rect(center=(SCREEN_W // 2, 200)))

        for b in self.menu_buttons:
            b.draw(scr)

        draw_text(scr, "Arrow keys / Mouse to navigate",
                  self.fonts["small"], (160, 160, 180),
                  center=(SCREEN_W // 2, SCREEN_H - 30))

    def _draw_level_select(self):
        scr = self.screen
        scr.fill((12, 12, 20))
        draw_text(scr, "SELECT LEVEL", self.fonts["title"], YELLOW,
                  center=(SCREEN_W // 2, 100))
        for b in self.level_buttons:
            b.draw(scr)

    def _draw_playing(self):
        scr = self.screen
        t = self.track
        if t is None:
            return

        scr.fill(t.spec.grass_color)
        scr.blit(t.road_surface,
                 (int(t.road_origin[0] - self.camera_x),
                  int(t.road_origin[1] - self.camera_y)))

        self._draw_marker(0.0, "START", GREEN)
        self._draw_marker(t.finish_position, "FINISH", YELLOW)

        coin_spr = _make_coin_sprite()
        for c in t.coins:
            if c.collected:
                continue
            if abs(c.position - t.racers[0].position) > 900:
                continue
            x, y = t.world_position(c.position, c.lane * LANE_WIDTH)
            sx, sy = int(x - self.camera_x), int(y - self.camera_y)
            scr.blit(coin_spr, coin_spr.get_rect(center=(sx, sy)))

        for o in t.obstacles:
            if abs(o.position - t.racers[0].position) > 1500:
                continue
            x, y = t.world_position(o.position, o.offset)
            sx, sy = int(x - self.camera_x), int(y - self.camera_y)
            _, _, tx, ty = t.road_position(o.position)
            angle = math.degrees(math.atan2(ty, tx))
            spr = _make_obstacle_sprite(angle)
            scr.blit(spr, spr.get_rect(center=(sx, sy)))

        for b in t.speed_bumps:
            if abs(b.position - t.racers[0].position) > 1500:
                continue
            x, y = t.world_position(b.position, 0.0)
            sx, sy = int(x - self.camera_x), int(y - self.camera_y)
            _, _, tx, ty = t.road_position(b.position)
            angle = math.degrees(math.atan2(ty, tx))
            spr = _make_speed_bump_sprite(angle)
            scr.blit(spr, spr.get_rect(center=(sx, sy)))

        self._draw_clipped_poles(t)

        for r in t.racers:
            if r.is_player:
                continue
            x, y = t.world_position(r.position, r.lane * LANE_WIDTH)
            sx, sy = int(x - self.camera_x), int(y - self.camera_y)
            spr = _make_racer_sprite(r.color, 15, 10)
            scr.blit(spr, spr.get_rect(center=(sx, sy)))

        p = t.racers[0]
        px, py = t.world_position(p.position)
        sx, sy = int(px - self.camera_x), int(py - self.camera_y)
        spr = _make_racer_sprite(p.color, 16, 11)
        scr.blit(spr, spr.get_rect(center=(sx, sy)))

        self._draw_hud()

        if not self.race_started and self.countdown > -GO_DISPLAY_TIME:
            label = str(int(math.ceil(self.countdown))) \
                if self.countdown > 0 else "GO!"
            big = self.fonts["title"]
            txt = big.render(label, True, YELLOW)
            shadow = big.render(label, True, BLACK)
            r1 = txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            r2 = shadow.get_rect(center=(SCREEN_W // 2 + 3,
                                         SCREEN_H // 2 + 3))
            scr.blit(shadow, r2)
            scr.blit(txt, r1)

    def _draw_marker(self, position, label, color):
        t = self.track
        x, y, tx, ty = t.road_position(position)
        nx, ny = -ty, tx
        left = ga.translate_point(x, y, nx * ROAD_HALF_WIDTH,
                                  ny * ROAD_HALF_WIDTH)
        right = ga.translate_point(x, y, -nx * ROAD_HALF_WIDTH,
                                   -ny * ROAD_HALF_WIDTH)
        ga.bresenham_line(left[0] - self.camera_x, left[1] - self.camera_y,
                          right[0] - self.camera_x, right[1] - self.camera_y,
                          color, self.screen)

        sx = int(x - self.camera_x)
        sy = int(y - self.camera_y)
        draw_text(self.screen, label, self.fonts["h1"], color,
                  center=(sx, sy - ROAD_HALF_WIDTH - 28))

    def _draw_clipped_poles(self, t: Track):
        """
        Sutherland-Hodgman clipping applied to actual gameplay objects
        (decorative race poles) as they enter the internal view
        frustum. The clip rectangle is mathematical - never drawn.
        """
        clip_x0 = CLIP_MARGIN
        clip_y0 = CLIP_MARGIN
        clip_x1 = SCREEN_W - CLIP_MARGIN
        clip_y1 = SCREEN_H - CLIP_MARGIN

        spacing = 200.0
        player_pos = t.racers[0].position
        start = max(0.0, (player_pos // spacing) * spacing - spacing)
        end = min(t.total_length, player_pos + 1200)

        pos = start
        while pos <= end:
            for side_offset in (-ROAD_HALF_WIDTH - 22,
                                ROAD_HALF_WIDTH + 22):
                x, y = t.world_position(pos, side_offset)
                sx = x - self.camera_x
                sy = y - self.camera_y

                if sx < clip_x0 - 40 or sx > clip_x1 + 40:
                    continue

                s = 10
                poly = [
                    (sx - s, sy - s * 2),
                    (sx + s, sy - s * 2),
                    (sx + s, sy + s),
                    (sx - s, sy + s),
                ]

                clipped = clip_polygon(poly, clip_x0, clip_y0,
                                       clip_x1, clip_y1)
                if polygon_is_degenerate(clipped):
                    continue

                n = len(clipped)
                for i in range(n):
                    p1 = clipped[i]
                    p2 = clipped[(i + 1) % n]
                    ga.bresenham_line(p1[0], p1[1], p2[0], p2[1],
                                      YELLOW, self.screen)

                xs = [p[0] for p in clipped]
                ys = [p[1] for p in clipped]
                mid_x = int(sum(xs) / len(xs))
                mid_y = int(sum(ys) / len(ys))
                if (clip_x0 + 1 < mid_x < clip_x1 - 1 and
                        clip_y0 + 1 < mid_y < clip_y1 - 1):
                    ga.flood_fill(self.screen, mid_x, mid_y,
                                  (200, 60, 60), YELLOW)

            pos += spacing

    def _draw_hud(self):
        scr = self.screen
        t = self.track
        if t is None:
            return

        panel = pygame.Surface((SCREEN_W, 108), pygame.SRCALPHA)
        panel.fill((10, 10, 10, 220))
        scr.blit(panel, (0, 0))

        draw_text(scr, "Fun Race & Parkour", self.fonts["h1"], WHITE,
                  topleft=(14, 10))
        draw_text(scr, t.spec.display_name, self.fonts["small"],
                  t.spec.difficulty_color, topleft=(14, 46))

        draw_text(scr, f"TIME {self.race_time:05.1f}s",
                  self.fonts["body"], YELLOW,
                  center=(SCREEN_W // 2, 30))

        draw_text(scr, f"COINS {self.coin_count[0]}/{len(t.coins)}",
                  self.fonts["body"], YELLOW,
                  topleft=(SCREEN_W - 180, 18))

        player = t.racers[0]
        prog = min(1.0, player.position / max(1.0, t.finish_position))
        bar_x, bar_y = 14, 78
        bar_w, bar_h = SCREEN_W - 28, 14
        pygame.draw.rect(scr, (40, 40, 55),
                         (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(scr, GREEN,
                         (bar_x, bar_y, int(bar_w * prog), bar_h))
        ga.bresenham_line(bar_x, bar_y, bar_x + bar_w, bar_y, WHITE, scr)
        ga.bresenham_line(bar_x + bar_w, bar_y, bar_x + bar_w,
                          bar_y + bar_h, WHITE, scr)
        ga.bresenham_line(bar_x + bar_w, bar_y + bar_h, bar_x,
                          bar_y + bar_h, WHITE, scr)
        ga.bresenham_line(bar_x, bar_y + bar_h, bar_x, bar_y, WHITE, scr)

        positions = sorted(t.racers, key=lambda r: -r.position)
        for i, r in enumerate(positions, start=1):
            draw_text(scr, f"{i}. {r.name}", self.fonts["small"], r.color,
                      topleft=(SCREEN_W - 130, 46 + (i - 1) * 18))

    def _draw_pause(self):
        overlay(self.screen, 170)
        draw_text(self.screen, "PAUSED", self.fonts["title"], YELLOW,
                  center=(SCREEN_W // 2, 150))
        draw_text(self.screen, "P or ESC to resume",
                  self.fonts["small"], WHITE,
                  center=(SCREEN_W // 2, 210))
        for b in self.pause_buttons:
            b.draw(self.screen)

    def _draw_result(self):
        scr = self.screen
        t = self.track
        if t is None:
            return

        overlay(scr, 170)

        if self.winner is not None:
            if self.winner.is_player:
                title, col = "YOU WIN!", GREEN
            else:
                title, col = f"{self.winner.name} WINS", RED
        else:
            title, col = "RACE OVER", YELLOW

        draw_text(scr, title, self.fonts["title"], col,
                  center=(SCREEN_W // 2, 150))

        sorted_r = sorted(t.racers,
                          key=lambda r: r.finish_time
                          if r.finish_time is not None else 9e9)
        y = 230
        for i, r in enumerate(sorted_r, start=1):
            ft = f"{r.finish_time:.2f}s" if r.finish_time is not None else "--"
            line = f"{i}.  {r.name:<6}  {ft}   hits: {r.collision_count}"
            draw_text(scr, line, self.fonts["body"], r.color,
                      center=(SCREEN_W // 2, y))
            y += 40

        draw_text(scr,
                  f"Coins collected: {self.coin_count[0]}/{len(t.coins)}",
                  self.fonts["body"], YELLOW,
                  center=(SCREEN_W // 2, y + 10))

        for b in self.result_buttons:
            if b.text == "NEXT LEVEL" and \
               self.selected_level_index >= len(ALL_LEVELS) - 1:
                continue
            b.draw(scr)

    def _draw_instructions(self):
        scr = self.screen
        scr.fill((12, 12, 20))
        draw_text(scr, "INSTRUCTIONS", self.fonts["title"], YELLOW,
                  center=(SCREEN_W // 2, 80))

        lines = [
            "RIGHT ARROW / D   - Accelerate",
            "LEFT  ARROW / A   - Brake / Reverse",
            "P or ESC          - Pause",
            "R                 - Restart the level",
            "",
            "Collect coins to increase your score.",
            "Avoid the moving red barriers - they bounce you back",
            "to your last checkpoint.",
            "Yellow speed bumps slow everyone down equally.",
            "Beat the AI racers to the finish line.",
        ]
        for i, line in enumerate(lines):
            draw_text(scr, line, self.fonts["body"], WHITE,
                      center=(SCREEN_W // 2, 180 + i * 34))

        draw_text(scr, "ESC - back to menu", self.fonts["small"],
                  (160, 160, 180),
                  center=(SCREEN_W // 2, SCREEN_H - 40))

    def _draw_credits(self):
        scr = self.screen
        scr.fill((12, 12, 20))
        draw_text(scr, "CREDITS", self.fonts["title"], YELLOW,
                  center=(SCREEN_W // 2, 100))

        lines = [
            "Fun Race & Parkour - Graphics Algorithms",
            "",
            "Design and Programming   : Student Project",
            "Rendering Pipeline       : Custom Pygame",
            "Algorithms               : Bresenham, Flood Fill,",
            "                           Rotation, Translation,",
            "                           Sutherland-Hodgman Clipping",
            "",
            "Built with Python 3 and Pygame 2.5",
        ]
        for i, line in enumerate(lines):
            draw_text(scr, line, self.fonts["body"], WHITE,
                      center=(SCREEN_W // 2, 200 + i * 32))

        draw_text(scr, "ESC - back to menu", self.fonts["small"],
                  (160, 160, 180),
                  center=(SCREEN_W // 2, SCREEN_H - 40))


# ============================================================
# Entry
# ============================================================
def main():
    try:
        game = Game()
        game.run()
    except Exception as exc:
        print("FATAL:", exc)
        pygame.quit()
        raise