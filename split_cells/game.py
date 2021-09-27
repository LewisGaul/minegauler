__all__ = ("GameMode",)

import enum


class GameMode(enum.Enum):
    """Minesweeper game mode."""

    REGULAR = enum.auto()
    SPLIT_CELL = enum.auto()
