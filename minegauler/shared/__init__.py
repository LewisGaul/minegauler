"""
__init__.py - Code shared between core and frontend

December 2019, Lewis Gaul
"""

__all__ = (
    "AllOptsStruct",
    "GameOptsStruct",
    "GUIOptsStruct",
    "highscores",
    "read_settings_from_file",
    "write_settings_to_file",
)

from . import highscores
from .utils import (
    AllOptsStruct,
    GameOptsStruct,
    GUIOptsStruct,
    read_settings_from_file,
    write_settings_to_file,
)
