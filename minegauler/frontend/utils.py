"""
utils.py - Utilities for the frontend.

December 2018, Lewis Gaul
"""

import pathlib
from typing import Dict

import attr

from minegauler import ROOT_DIR
from minegauler.utils import StructConstructorMixin
from minegauler.types import *


IMG_DIR: pathlib.Path = ROOT_DIR / "images"
