"""
utils.py - Utilities for the frontend.

December 2018, Lewis Gaul
"""

import os
from typing import Dict

import attr

from minegauler import ROOT_DIR
from minegauler.core.internal_types import *
from minegauler.core.utils import StructConstructorMixin


IMG_DIR = os.path.join(ROOT_DIR, "images")


@attr.attrs(auto_attribs=True)
class GuiOptsStruct(StructConstructorMixin):
    """
    Structure of GUI options.
    """

    btn_size: int = 16
    drag_select: bool = False
    styles: Dict[CellImageType, str] = {
        CellImageType.BUTTONS: "Standard",
        CellImageType.NUMBERS: "Standard",
        CellImageType.MARKERS: "Standard",
    }
