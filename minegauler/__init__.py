"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""

__all__ = ("IN_EXE", "ROOT_DIR", "SETTINGS_FILE")

import pathlib
import sys


IN_EXE: bool = hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS")

ROOT_DIR: pathlib.Path
if IN_EXE:
    ROOT_DIR = pathlib.Path(__file__).parent.parent
else:
    ROOT_DIR = pathlib.Path(__file__).parent

SETTINGS_FILE: pathlib.Path = ROOT_DIR / "settings.cfg"
