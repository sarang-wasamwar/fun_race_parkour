"""
Level definitions.

A TrackSpec fully describes a level as *data*:
  - road generation commands
  - obstacle placement
  - AI opponent tuning
  - visual palette

This replaces the 3 duplicated level1.py / level2.py / level3.py files.
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# ============================================================
# Colour palettes
# ============================================================
BLACK = (10, 10, 10)
WHITE = (235, 235, 235)
RED = (230, 45, 45)
BLUE = (55, 130, 255)
GREEN = (50, 210, 100)
YELLOW = (255, 220, 0)
CYAN = (50, 205, 255)
ORANGE = (255, 140, 30)
ROAD_COLOR = (68, 68, 68)
ROAD_EDGE_COLOR = (210, 210, 210)
GRASS_COLOR = (25, 80, 35)
DARK_GRASS_COLOR = (18, 60, 26)


# ============================================================
# Road generation commands
#   ("straight", distance)
#   ("turn", angle_deg, radius)
# ============================================================
RoadCommand = Tuple


@dataclass
class ObstacleSpec:
    position: float
    speed: float
    start_side: int           # +1 -> left,  -1 -> right


@dataclass
class SpeedBumpSpec:
    position: float


@dataclass
class AISpec:
    name: str
    color: Tuple[int, int, int]
    lane: int                 # -1 / 0 / +1
    ai_speed: float
    reaction: float
    risk: float


@dataclass
class TrackSpec:
    key: str
    display_name: str
    difficulty: str
    difficulty_color: Tuple[int, int, int]

    road_commands: List[RoadCommand]
    player_speed: float
    max_reverse: float
    default_ai_speed: float

    obstacles: List[ObstacleSpec] = field(default_factory=list)
    speed_bumps: List[SpeedBumpSpec] = field(default_factory=list)
    ai_opponents: List[AISpec] = field(default_factory=list)

    # Coin generation
    coin_spacing: float = 180.0
    coin_start: float = 350.0
    coin_end_margin: float = 120.0

    # Optional custom palette
    grass_color: Tuple[int, int, int] = GRASS_COLOR


# ============================================================
# Level 1 - Straight beginner track
# ============================================================
LEVEL_1 = TrackSpec(
    key="level1",
    display_name="Level 1 - Rookie Straight",
    difficulty="EASY",
    difficulty_color=GREEN,
    road_commands=[("straight", 2500)],
    player_speed=120.0,
    max_reverse=45.0,
    default_ai_speed=110.0,
    obstacles=[
        ObstacleSpec(650, 25, 1),
        ObstacleSpec(950, 30, -1),
        ObstacleSpec(1250, 28, 1),
        ObstacleSpec(1750, 35, -1),
        ObstacleSpec(1900, 32, 1),
        ObstacleSpec(2250, 40, -1),
    ],
    ai_opponents=[
        AISpec("BLUE",  BLUE,  -1, ai_speed=115, reaction=0.55, risk=0.25),
        AISpec("GREEN", GREEN, +1, ai_speed=115, reaction=0.75, risk=0.25),
    ],
    coin_spacing=180.0,
    coin_start=350.0,
    coin_end_margin=120.0,
)


# ============================================================
# Level 2 - Curved medium track
# ============================================================
LEVEL_2 = TrackSpec(
    key="level2",
    display_name="Level 2 - Curve Master",
    difficulty="MEDIUM",
    difficulty_color=BLUE,
    road_commands=[
        ("straight", 650),
        ("turn", 90, 180),
        ("straight", 650),
        ("turn", -90, 180),
        ("straight", 800),
        ("turn", -90, 180),
        ("straight", 650),
        ("turn", 90, 180),
        ("straight", 850),
    ],
    player_speed=180.0,
    max_reverse=70.0,
    default_ai_speed=175.0,
    obstacles=[
        ObstacleSpec(650, 55, 1),
        ObstacleSpec(1250, 60, -1),
        ObstacleSpec(1900, 65, 1),
        ObstacleSpec(2550, 70, -1),
        ObstacleSpec(3200, 75, 1),
        ObstacleSpec(3850, 80, -1),
        ObstacleSpec(4500, 85, 1),
    ],
    ai_opponents=[
        AISpec("BLUE",  BLUE,  -1, ai_speed=175, reaction=0.35, risk=0.45),
        AISpec("GREEN", GREEN, +1, ai_speed=175, reaction=0.45, risk=0.50),
    ],
    coin_spacing=180.0,
    coin_start=350.0,
    coin_end_margin=120.0,
)


# ============================================================
# Level 3 - Hard track with speed bumps
# ============================================================
LEVEL_3 = TrackSpec(
    key="level3",
    display_name="Level 3 - Chaos Circuit",
    difficulty="HARD",
    difficulty_color=RED,
    road_commands=[
        ("straight", 650),
        ("turn", 90, 180),
        ("straight", 650),
        ("turn", -90, 180),
        ("straight", 800),
        ("turn", -90, 180),
        ("straight", 650),
        ("turn", 90, 180),
        ("straight", 850),
        ("turn", 90, 180),
        ("straight", 650),
        ("turn", -90, 180),
        ("straight", 800),
        ("turn", -90, 180),
        ("straight", 750),
    ],
    player_speed=210.0,
    max_reverse=70.0,
    default_ai_speed=205.0,
    obstacles=[
        ObstacleSpec(650, 55, 1),
        ObstacleSpec(1250, 60, -1),
        ObstacleSpec(1900, 65, 1),
        ObstacleSpec(2550, 70, -1),
        ObstacleSpec(3200, 75, 1),
    ],
    speed_bumps=[
        SpeedBumpSpec(1000),
        SpeedBumpSpec(2200),
        SpeedBumpSpec(2900),
    ],
    ai_opponents=[
        AISpec("BLUE",  BLUE,  -1, ai_speed=215, reaction=0.45, risk=0.55),
        AISpec("GREEN", GREEN, +1, ai_speed=215, reaction=0.55, risk=0.60),
    ],
    coin_spacing=180.0,
    coin_start=350.0,
    coin_end_margin=120.0,
    grass_color=DARK_GRASS_COLOR,
)


ALL_LEVELS: List[TrackSpec] = [LEVEL_1, LEVEL_2, LEVEL_3]


def get_level(key: str) -> Optional[TrackSpec]:
    for lvl in ALL_LEVELS:
        if lvl.key == key:
            return lvl
    return None