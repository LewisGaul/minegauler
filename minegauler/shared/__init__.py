"""
__init__.py - Code shared between core and frontend

December 2019, Lewis Gaul
"""

__all__ = (
    "AllOptsStruct",
    "GameOptsStruct",
    "GUIOptsStruct",
    "HighscoreSettingsStruct",
    "HighscoreStruct",
    "get_difficulty",
    "highscores",
    "read_settings_from_file",
    "write_settings_to_file",
)

from . import highscores
from .highscores import HighscoreSettingsStruct, HighscoreStruct
from .utils import (
    AllOptsStruct,
    GameOptsStruct,
    GUIOptsStruct,
    get_difficulty,
    read_settings_from_file,
    write_settings_to_file,
)
