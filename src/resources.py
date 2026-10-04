"""
Resource-path helper.

Works during development AND after PyInstaller --onefile packaging.
When frozen, assets are extracted to sys._MEIPASS.
"""
import os
import sys


def _base_dir() -> str:
    # PyInstaller sets sys._MEIPASS to the temp extraction dir.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    # __file__ is <project>/src/resources.py  ->  project root is parent of parent
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _base_dir()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")


def asset_path(*parts: str) -> str:
    return os.path.join(ASSETS_DIR, *parts)