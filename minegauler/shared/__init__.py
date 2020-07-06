# December 2019, Lewis Gaul

"""
Code not belonging to another specific sub-package.

"""

__all__ = (
    "AllOptsStruct",
    "GameOptsStruct",
    "GUIOptsStruct",
    "HighscoreSettingsStruct",
    "HighscoreStruct",
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
    read_settings_from_file,
    write_settings_to_file,
)
