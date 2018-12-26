"""
utils.py - Utilities for the frontend.

December 2018, Lewis Gaul
"""


import enum
from os.path import join

from minegauler.shared.utils import root_dir


img_dir = join(root_dir, 'images')


class FaceState(enum.Enum):
    READY  = 'ready'
    ACTIVE = 'active'
    WON    = 'won'
    LOST   = 'lost'