# Fun Race & Parkour

### A 2.5D racing game built from computer-graphics algorithms

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-00A86B)](https://www.pygame.org/)
[![Graphics](https://img.shields.io/badge/Rendering-Custom%20Algorithms-F2C94C)](#graphics-algorithms)

**Fun Race & Parkour** is the final playable game from a semester-long
Computer Graphics and Gaming project. It is a top-down 2.5D racing game made
with Python and Pygame. The road, racers, coins, obstacles, and race markers
are drawn with custom graphics algorithms rather than external image assets.

> **The challenge:** beat two AI racers, collect coins, avoid moving barriers,
> survive speed bumps, and reach the finish line first.

**Repository:** [github.com/sarang-wasamwar/fun_race_parkour](https://github.com/sarang-wasamwar/fun_race_parkour)

---

## Play the game

### Features

- Three data-driven levels: **Easy**, **Medium**, and **Hard**
- Player versus two AI racers with different reaction, speed, and risk profiles
- Coins, moving barriers, speed bumps, checkpoints, and collision recovery
- 3-2-1-GO countdown, race timer, progress bar, and live position ranking
- Pause, restart, level selection, next-level, and results screens
- Interactive **Graphics Algorithms Demo** available from the main menu
- Procedurally generated road surfaces with no external image assets
- Stable rendering using cached Bresenham and flood-fill surfaces

### Controls

| Input | Action |
| --- | --- |
| `Right Arrow` or `D` | Accelerate |
| `Left Arrow` or `A` | Brake / reverse |
| `P` or `ESC` | Pause during a race |
| `R` | Restart the current level |
| Mouse | Navigate menus and buttons |
| `Left` / `Right` or `A` / `D` | Browse the algorithm demo |
| `ESC` in the demo | Return to the menu |

### A quick playthrough

1. Start the game and choose a level.
2. Press `Right Arrow` or `D` to start accelerating.
3. Collect yellow coins for score.
4. Avoid red moving barriers; collisions return you to your last checkpoint.
5. Cross the finish line before the AI racers.
6. Try the next level or open the algorithm demo to see how the visuals are
   rasterized.

---

## Installation

The project is tested with **Python 3.11** and **Pygame 2.5.2**. Python
3.10+ is supported.

### Windows PowerShell

```powershell
git clone https://github.com/sarang-wasamwar/fun_race_parkour.git
cd fun_race_parkour
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, run the game through the virtual environment
directly:

```powershell
.\.venv\Scripts\python.exe main.py
```

### Linux or macOS

```bash
git clone https://github.com/sarang-wasamwar/fun_race_parkour.git
cd fun_race_parkour
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Optional Windows executable

`build_exe.bat` is included for creating a packaged Windows build. Run it
from the project folder after installing the project dependencies and the
required packaging tool in your environment.

---

## Graphics algorithms

The game is designed to make the algorithms visible in actual gameplay.

| Algorithm | What it does | Used for |
| --- | --- | --- |
| **Bresenham line** | Integer-only incremental line rasterization | Road edges, lane dashes, markers, HUD frame, and poles |
| **Bresenham circle** | Eight-way symmetric circle rasterization | Player, AI cars, and coins |
| **Flood fill** | Iterative four-connected region filling | Road interiors, coins, obstacles, speed bumps, and clipped poles |
| **Translation** | `x' = x + tx`, `y' = y + ty` | Camera movement, road stepping, and marker placement |
| **Rotation** | 2D rotation matrix around a pivot | Curved roads and rotated obstacle surfaces |
| **Sutherland-Hodgman clipping** | Clips a polygon against a rectangle | Poles, flags, and banners crossing the view window |
| **Circle collision** | Distance compared with the sum of radii | Racer-obstacle and racer-coin interaction |

Open **Graphics Algorithms Demo** from the game menu to see animated
side-by-side examples of the line, circle, flood-fill, translation, rotation,
and clipping algorithms.

---

## Project structure

```text
fun_race_parkour/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── build_exe.bat              # Optional Windows packaging helper
└── src/
    ├── game.py                # Game loop, simulation, rendering, HUD, results
    ├── levels.py              # Data-driven track and racer definitions
    ├── graphics_algorithms.py # Custom rasterization and transformations
    ├── clipping.py            # Sutherland-Hodgman polygon clipping
    ├── collision.py           # Collision and point-segment helpers
    ├── states.py              # Game-state constants and state machine
    ├── ui.py                  # Buttons, text, and overlays
    ├── resources.py           # Resource-path helpers
    └── demo.py                # Interactive algorithm demonstration
```

### Why the project is split into modules

The final version separates the game into focused modules instead of keeping
all experiments in one file:

- **Rendering algorithms** can be tested and demonstrated independently.
- **Level data** can be changed without duplicating game logic.
- **Collision and clipping** are reusable helpers.
- **Game states and UI** keep menus, pauses, races, and results organized.
- **`game.py`** coordinates the simulation while the other modules provide
  the systems it needs.

---

## Learning journey

This repository is the final stage of the larger `Fun_Race_3D` learning
archive included in the course workspace.

```text
Pixel primitives
      ↓
Lines and circles
      ↓
Transformations and camera
      ↓
Levels, AI, collisions, and obstacles
      ↓
Modular Pygame game with polygon clipping
```

The earlier versions show the progression from:

1. DDA and Bresenham line drawing
2. DDA, midpoint, and Bresenham circle drawing
3. Translation, scaling, rotation, and composite transformations
4. World coordinates, camera movement, levels, AI, and collision systems
5. Python/Pygame integration, flood fill, polygon clipping, and an
   educational demo mode

The final game proves that these algorithms were not only studied separately;
they were combined into a complete interactive experience.

---

## Explore the code

Use this checklist as a guided tour:

- [ ] Run one level and collect a coin.
- [ ] Hit a barrier and observe checkpoint recovery.
- [ ] Compare the Easy and Hard level definitions in `src/levels.py`.
- [ ] Find the custom line and circle functions in
      `src/graphics_algorithms.py`.
- [ ] Open `src/clipping.py` and follow one polygon through its clipping
      edges.
- [ ] Open the algorithm demo and switch between all six demonstrations.
- [ ] Trace one frame from input handling in `src/game.py` through update and
      draw operations.

<details>
<summary><strong>Questions for a presentation or viva</strong></summary>

- Why does Bresenham avoid floating-point calculations while drawing a line?
- How does eight-way symmetry reduce the work needed to draw a circle?
- Why is flood fill performed only after a closed boundary is drawn?
- How does camera translation make the road feel larger than the screen?
- Why must a polygon be clipped before its pixels are filled?
- Which values describe a level, and which values change every frame?
- How do checkpoints make collisions fair instead of ending the race?

</details>

---

## Credits and context

This game was developed as a Computer Graphics and Gaming semester project.
The project focuses on implementing and applying fundamental graphics
algorithms instead of relying on pre-rendered game artwork.

For the complete version-by-version development story, see the `Fun_Race_3D`
archive in the course workspace.
