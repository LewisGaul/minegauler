# June 2018, Lewis Gaul

"""
Types used throughout the project.

Exports
-------
.. class:: CellContents
    An ADT-like class providing cell contents types.

.. class:: CellImageType
    An enum of cell image types.

.. class:: Coord
    A base coordinate class.

.. class:: Difficulty
    An enum of board difficulties.

.. class:: FaceState
    An enum of possible face states.

.. class:: GameState
    An enum of states a game can be in.

.. class:: GameMode
    An enum of game modes.

.. class:: PathLike
    A more permissive version of the `os.PathLike` type alias.

.. class:: UIMode
    An enum of supported UI modes.

"""

__all__ = (
    "CellContents",
    "CellImageType",
    "Coord",
    "Difficulty",
    "FaceState",
    "GameMode",
    "GameState",
    "PathLike",
    "UIMode",
)

import abc
import enum
import functools
import os
from typing import Union


PathLike = Union[str, bytes, os.PathLike]


# ------------------------------------------------------------------------------
# Coordinate types
# ------------------------------------------------------------------------------


class Coord(metaclass=abc.ABCMeta):
    fields = ("x", "y")

    x: int
    y: int

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(f"{x}={getattr(self, x)}" for x in self.fields),
        )

    def __eq__(self, other):
        try:
            return all(getattr(self, x) == getattr(other, x) for x in self.fields)
        except AttributeError:
            return False

    def __hash__(self):
        return hash(tuple(getattr(self, x) for x in self.fields))

    def __lt__(self, other):
        if not isinstance(other, Coord):
            return NotImplemented
        return (self.x, self.y) < (other.x, other.y)


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
    UnclickedSunken = NotImplemented
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

    @staticmethod
    def from_char(char: str) -> "CellContents":
        return NotImplemented  # Implemented below, after subclasses

    @staticmethod
    def from_str(string: str) -> "CellContents":
        return NotImplemented  # Implemented below, after subclasses

    def is_type(self, item: "CellContents") -> bool:
        if item in [self.Unclicked, self.UnclickedSunken]:
            return self is item
        elif item in self.items:
            return type(self) is item
        else:
            raise ValueError(f"Unrecognised type {item!r}")

    def is_mine_type(self) -> bool:
        return False  # Overridden by subclasses as required


class _CellUnclicked(CellContents):
    """Unclicked cell on a minesweeper board."""

    char = "#"


class _CellUnclickedSunken(_CellUnclicked):
    """Unclicked sunken cell on a minesweeper board."""


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
CellContents.UnclickedSunken = _CellUnclickedSunken()
CellContents.Num = _CellNum
CellContents.Mine = _CellMine
CellContents.HitMine = _CellHitMine
CellContents.Flag = _CellFlag
CellContents.WrongFlag = _CellWrongFlag

CellContents.items = [
    CellContents.Unclicked,
    CellContents.UnclickedSunken,
    CellContents.Num,
    CellContents.Mine,
    CellContents.HitMine,
    CellContents.Flag,
    CellContents.WrongFlag,
]


def _from_char(char: str) -> CellContents:
    """
    Get the class of mine-like cell contents using the character
    representation.

    :param char:
        The character representation of a cell contents type.
    :return:
        The cell contents enum item.
    """
    for item in CellContents.items:
        if item.char == char:
            return item


def _from_str(string: str) -> CellContents:
    if string.isnumeric():
        return CellContents.Num(int(string))
    elif len(string) == 2:
        char, num = string
        return CellContents.from_char(char)(int(num))
    elif string == CellContents.Unclicked.char:
        return CellContents.Unclicked
    else:
        raise ValueError(f"Unknown cell contents representation {string!r}")


CellContents.from_char = _from_char
CellContents.from_str = _from_str


# ------------------------------------------------------------------------------
# Game enums
# ------------------------------------------------------------------------------


class Difficulty(str, enum.Enum):
    """Enum of difficulty settings."""

    BEGINNER = "B"
    INTERMEDIATE = "I"
    EXPERT = "E"
    MASTER = "M"
    LUDICROUS = "L"
    CUSTOM = "C"

    @classmethod
    def from_str(cls, value: str) -> "Difficulty":
        """Create an instance from a string representation."""
        if value.upper() in [x.name for x in cls]:
            value = value[0].upper()
        elif value.upper() in [x.value for x in cls]:
            value = value.upper()
        return cls(value)


class GameState(str, enum.Enum):
    """Enum representing the state of a game."""

    READY = "READY"
    ACTIVE = "ACTIVE"
    WON = "WON"
    LOST = "LOST"

    def started(self) -> bool:
        return self is not self.READY

    def finished(self) -> bool:
        return self in [self.WON, self.LOST]


class GameMode(str, enum.Enum):
    """Minesweeper game mode."""

    REGULAR = "REGULAR"
    SPLIT_CELL = "SPLIT_CELL"


# ------------------------------------------------------------------------------
# GUI enums
# ------------------------------------------------------------------------------


class FaceState(enum.Enum):
    """Enum of the 'new game' button face states."""

    READY = "ready"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"


class CellImageType(enum.Flag):
    """Enum of cell image types."""

    BUTTONS = enum.auto()
    NUMBERS = enum.auto()
    MARKERS = enum.auto()
    ALL = BUTTONS | NUMBERS | MARKERS


class UIMode(enum.Enum):
    """Enum of UI modes."""

    GAME = enum.auto()
    CREATE = enum.auto()
