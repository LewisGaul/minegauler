__all__ = ("GameMode", "RegularCoord")

import enum
from typing import NamedTuple


class RegularCoord(NamedTuple):
    """Regular coord, an (x, y) tuple."""

    x: int
    y: int


class GameMode(enum.Enum):
    """Minesweeper game mode."""

    REGULAR = enum.auto()
    SPLIT_CELL = enum.auto()
