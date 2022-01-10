# January 2022, Lewis Gaul

__all__ = (
    "BOARDS_DIR",
    "DATA_DIR",
    "FILES_DIR",
    "HIGHSCORES_FILE",
    "IMG_DIR",
    "ROOT_DIR",
    "SETTINGS_FILE",
)

import pathlib
import sys


if hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS"):  # in pyinstaller EXE
    ROOT_DIR = pathlib.Path(__file__).parent.parent
else:
    ROOT_DIR = pathlib.Path(__file__).parent
SETTINGS_FILE: pathlib.Path = ROOT_DIR / "settings.cfg"
DATA_DIR: pathlib.Path = ROOT_DIR / "data"
HIGHSCORES_FILE: pathlib.Path = DATA_DIR / "highscores.db"
IMG_DIR: pathlib.Path = ROOT_DIR / "images"
FILES_DIR: pathlib.Path = ROOT_DIR / "files"
BOARDS_DIR = ROOT_DIR / "boards"
