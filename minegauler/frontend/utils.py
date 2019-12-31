"""
utils.py - Utilities for the frontend.

December 2018, Lewis Gaul
"""

__all__ = ("FILES_DIR", "IMG_DIR")

import pathlib

from minegauler import ROOT_DIR


IMG_DIR: pathlib.Path = ROOT_DIR / "images"
FILES_DIR: pathlib.Path = ROOT_DIR / "files"
