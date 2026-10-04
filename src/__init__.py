"""
Fun Race & Parkour - Graphics Algorithms

Source package for the game.

Contents
--------
game.py                 - Game loop, state machine, rendering, HUD
states.py               - State constants and StateMachine helper
levels.py               - Data-driven level definitions (TrackSpec)
graphics_algorithms.py  - Bresenham line, Bresenham circle, Flood Fill,
                          Translation, Rotation, Polyline rasterization
clipping.py             - Sutherland-Hodgman polygon clipping
collision.py            - Circle-circle and point-segment collision tests
ui.py                   - Buttons, text helpers, overlays
demo.py                 - Interactive Graphics Algorithms demo mode
resources.py            - Frozen-safe asset path helpers
"""

__version__ = "1.0.0"
__all__ = [
    "game",
    "states",
    "levels",
    "graphics_algorithms",
    "clipping",
    "collision",
    "ui",
    "demo",
    "resources",
]