"""
Project types.

June 2018, Lewis Gaul

Exports:

CellContents (class)
    Base class for cell contents types.

GameState (Enum)
    The possible states of a game.
"""

__all__ = ("CellContents", "CellImageType", "FaceState", "GameState", "UIMode")

import enum
import functools

from .typing import CellContentsItem


# ------------------------------------------------------------------------------
# Cell contents types
# ------------------------------------------------------------------------------


class _NumericCellContentsMixin:
    """
    A mixin for numeric cell contents types, allowing adding and subtracting integers.
    """

    char: str

    def __init__(self, num):
        if not isinstance(num, int):
            raise TypeError("Number should be an integer")
        self.num = num

    def __repr__(self):
        return self.char + str(self.num)

    def __add__(self, obj):
        if type(obj) is not int:
            raise TypeError("Can only add integers to cell contents types")
        else:
            return self.__class__(self.num + obj)

    def __sub__(self, obj):
        if type(obj) is not int:
            raise TypeError("Can only subtract integers from cell contents types")
        else:
            return self.__class__(self.num - obj)


class CellContents:
    """Abstract base class for contents of a minesweeper board cell."""

    char: str

    Unclicked = NotImplemented
    Num = NotImplemented
    Mine = NotImplemented
    HitMine = NotImplemented
    Flag = NotImplemented
    WrongFlag = NotImplemented

    items = NotImplemented

    @functools.lru_cache(maxsize=None)
    def __new__(cls, *args):
        if cls is CellContents:
            raise TypeError("Base class should not be instantiated")
        return super().__new__(cls)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return self.char

    def is_mine_type(self) -> bool:
        return False  # Overridden by subclasses as required

    @staticmethod
    def from_char(char: str) -> CellContentsItem:
        return NotImplemented  # Implemented below, after subclasses

    def is_type(self, item) -> bool:
        if item in [self.Unclicked]:
            return self is item
        elif item in self.items:
            return type(self) is item
        else:
            raise ValueError(f"Unrecognised type {item!r}")


class _CellUnclicked(CellContents):
    """Unclicked cell on a minesweeper board."""

    char = "#"


class _CellNum(_NumericCellContentsMixin, CellContents):
    """Number shown in a cell on a minesweeper board."""

    char = ""

    def __init__(self, num):
        super().__init__(num)
        if num < 0:
            raise ValueError("Cell value cannot be negative")


class _CellMineType(_NumericCellContentsMixin, CellContents):
    """Abstract base class for the number of a mine type in a cell."""

    def __new__(cls, num=1):
        if cls is _CellMineType:
            raise TypeError(
                f"{type(cls)} should be used as a base class and not "
                "instantiated directly"
            )
        return super().__new__(cls, num)

    def __init__(self, num=1):
        super().__init__(num)
        if num < 1:
            raise ValueError("Mine-type cell contents must represent one or more mines")

    def is_mine_type(self) -> bool:
        return True


class _CellMine(_CellMineType):
    """Number of mines in a cell shown on a minesweeper board."""

    char = "M"


class _CellHitMine(_CellMineType):
    """Number of hit mines in a cell shown on a minesweeper board."""

    char = "!"


class _CellFlag(_CellMineType):
    """Number of flags in a cell shown on a minesweeper board."""

    char = "F"


class _CellWrongFlag(_CellFlag):
    """Number of incorrect flags in a cell shown on a minesweeper board."""

    char = "X"


# Make the base class act like an ADT, serving as the only external API.
CellContents.Unclicked = _CellUnclicked()
CellContents.Num = _CellNum
CellContents.Mine = _CellMine
CellContents.HitMine = _CellHitMine
CellContents.Flag = _CellFlag
CellContents.WrongFlag = _CellWrongFlag

CellContents.items = [
    CellContents.Unclicked,
    CellContents.Num,
    CellContents.Mine,
    CellContents.HitMine,
    CellContents.Flag,
    CellContents.WrongFlag,
]


def _from_char(char: str):
    """
    Get the class of mine-like cell contents using the character
    representation.

    :param char:
        The character representation of a cell contents type.
    :return:
        The cell contents enum item.
    """
    for item in [
        CellContents.Unclicked,
        CellContents.Num,
        CellContents.Mine,
        CellContents.HitMine,
        CellContents.Flag,
        CellContents.WrongFlag,
    ]:
        if item.char == char:
            return item


CellContents.from_char = _from_char


# ------------------------------------------------------------------------------
# Game enums
# ------------------------------------------------------------------------------


class GameState(str, enum.Enum):
    """
    Enum representing the state of a game.
    """

    READY = "READY"
    ACTIVE = "ACTIVE"
    WON = "WON"
    LOST = "LOST"

    def started(self) -> bool:
        return self is not self.READY

    def finished(self) -> bool:
        return self in [self.WON, self.LOST]


# ------------------------------------------------------------------------------
# GUI enums
# ------------------------------------------------------------------------------


class FaceState(enum.Enum):
    READY = "ready"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"


class CellImageType(enum.Flag):
    BUTTONS = enum.auto()
    NUMBERS = enum.auto()
    MARKERS = enum.auto()
    ALL = BUTTONS | NUMBERS | MARKERS


class UIMode(enum.Enum):
    GAME = enum.auto()
    CREATE = enum.auto()
