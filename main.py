"""
Fun Race & Parkour - Graphics Algorithms
Entry point. Delegates to src.game.

    python main.py
"""
import sys
import os

# Make `src` importable even when frozen by PyInstaller.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.game import main

if __name__ == "__main__":
    main()