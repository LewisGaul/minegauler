# December 2018, Lewis Gaul

"""
Utilities for the frontend.

Exports
-------
.. data:: IMG_DIR
    The directory containing images.

.. data:: FILES_DIR
    The directory containing files.

"""

__all__ = ("FILES_DIR", "IMG_DIR")

import pathlib

from minegauler import ROOT_DIR


IMG_DIR: pathlib.Path = ROOT_DIR / "images"
FILES_DIR: pathlib.Path = ROOT_DIR / "files"
