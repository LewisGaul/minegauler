__all__ = ("GameMode", "Game", "RegularGame", "SplitCellGame")

import abc
import enum
import sys
from typing import Generic, Iterable, Mapping, Tuple, TypeVar

from minegauler.shared.types import Difficulty


if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class GameMode(enum.Enum):
    """Minesweeper game mode."""

    REGULAR = enum.auto()
    SPLIT_CELL = enum.auto()


_difficulty_pairs: Mapping[
    GameMode, Iterable[Tuple[Difficulty, Tuple[int, int, int]]]
] = {
    GameMode.REGULAR: [
        (Difficulty.BEGINNER, (8, 8, 10)),
        (Difficulty.INTERMEDIATE, (16, 16, 40)),
        (Difficulty.EXPERT, (30, 16, 99)),
        (Difficulty.MASTER, (30, 30, 200)),
        (Difficulty.LUDICROUS, (50, 50, 625)),
    ],
    GameMode.SPLIT_CELL: [
        (Difficulty.BEGINNER, (4, 4, 5)),
        (Difficulty.INTERMEDIATE, (8, 8, 20)),
        (Difficulty.EXPERT, (15, 8, 49)),
        (Difficulty.MASTER, (15, 15, 100)),
        (Difficulty.LUDICROUS, (25, 25, 400)),
    ],
}


def difficulty_to_values(mode: GameMode, diff: Difficulty) -> Tuple[int, int, int]:
    try:
        mapping = dict(_difficulty_pairs[mode])
    except KeyError:
        raise ValueError(f"Unknown game mode: {mode}") from None
    try:
        return mapping[diff]
    except KeyError:
        raise ValueError(f"Unknown difficulty: {diff}") from None


def difficulty_from_values(mode: GameMode, values: Tuple[int, int, int]) -> Difficulty:
    try:
        mapping = dict((x[1], x[0]) for x in _difficulty_pairs[mode])
    except KeyError:
        raise ValueError(f"Unknown game mode: {mode}") from None
    try:
        return mapping[values]
    except KeyError:
        return Difficulty.CUSTOM


M = TypeVar("M", bound=GameMode)


class Game(Generic[M], metaclass=abc.ABCMeta):
    """Representation of a minesweeper game, generic on the game mode."""

    mode: M

    @property
    def difficulty(self) -> Difficulty:
        return difficulty_from_values(self.mode, self.x_size, self.y_size, self.mines)


class RegularGame(Game[Literal[GameMode.REGULAR]]):
    """A regular minesweeper game."""

    mode = GameMode.REGULAR


class SplitCellGame(Game[Literal[GameMode.SPLIT_CELL]]):
    """A split-cell minesweeper game."""

    mode = GameMode.SPLIT_CELL
