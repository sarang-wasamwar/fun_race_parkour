# Fun Race & Parkour — Graphics Algorithms

A 2.5-D top-down racing / parkour game built entirely with **Pygame**
and **custom Computer Graphics algorithms**.

Every visible object — road, coins, cars, obstacles, race poles — is
rasterized with our own implementations of Bresenham line drawing,
Bresenham circle drawing, flood fill, translation, rotation, and
Sutherland–Hodgman polygon clipping. No external images are used.

---

## Features

- Three data-driven levels (Easy / Medium / Hard)
- Player vs. two AI opponents with individual reaction / risk profiles
- Coins, moving barriers, speed bumps
- 3-2-1-GO countdown, race timer, progress bar, live position ranking
- Pause, restart, level select, results screen
- Interactive **Graphics Algorithms Demo** from the main menu
- Bresenham + Flood Fill pre-baked road surface for stable 60 FPS

---

## Graphics Algorithms Used

| Algorithm | What it does | Where it's used |
|-----------|-------------|-----------------|
| **Bresenham Line** | Integer-only incremental line rasterization | Road edges, lane dashes, race markers, HUD frame, poles |
| **Bresenham Circle** | 8-way symmetric midpoint circle | Player, AI cars, coins |
| **Flood Fill** | 4-connected stack-based region fill | Road interior, coin interior, obstacle / speed-bump interior, clipped poles |
| **Translation** | `x' = x + tx, y' = y + ty` | Camera, road segment stepping, marker placement |
| **Rotation** | 2-D rotation matrix about a pivot | Curved road generation, rotated obstacle & speed-bump surfaces |
| **Sutherland–Hodgman Clipping** | Clip a polygon to a rectangle | Race poles crossing the internal view frustum before being drawn |
| **Circle–Circle Collision** | Sum-of-radii distance test | Racer ↔ obstacle, racer ↔ coin |

---

## Gameplay

Race down a procedurally generated track. Reach the finish line before
two AI opponents. Collect coins for bonus score. Moving red barriers
knock you back to your last checkpoint. Yellow speed bumps slow every
racer equally.

---

## Controls

| Key | Action |
|-----|--------|
| **Right Arrow / D** | Accelerate |
| **Left Arrow / A** | Brake / Reverse |
| **P** or **ESC** | Pause |
| **R** | Restart level |
| **Mouse** | Menu navigation |
| **Arrow Keys** | Demo navigation |

---

## Installation

Tested with **Python 3.11** and **pygame 2.5.2**.
Works with Python 3.10+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt