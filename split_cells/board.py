__all__ = ("Board", "RegularBoard", "SplitCellBoard")

import abc
import sys
from typing import Generic, Iterable, List, TypeVar


if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from minegauler.shared import utils
from minegauler.shared.types import CellContents

from .coord import RegularCoord
from .game import GameMode


M = TypeVar("M", bound=GameMode)


class Board(Generic[M], metaclass=abc.ABCMeta):
    """Representation of a minesweeper board, generic over the game mode."""


class RegularBoard(Board[Literal[GameMode.REGULAR]]):
    """A regular minesweeper board."""

    def __init__(self, x_size: int, y_size: int):
        self._grid = utils.Grid(x_size, y_size, fill=CellContents.Unclicked)

    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} board>"

    def __str__(self):
        return self._grid.__str__(mapping={CellContents.Num(0): "."})

    def __getitem__(self, coord: RegularCoord) -> CellContents:
        return self._grid[coord]

    def __setitem__(self, coord: RegularCoord, value: CellContents):
        if not isinstance(value, CellContents):
            raise TypeError("Board can only contain CellContents instances")
        self._grid[coord] = value

    def __contains__(self, coord: RegularCoord) -> bool:
        return coord in self.all_coords

    @property
    def x_size(self):
        return self._grid.x_size

    @property
    def y_size(self):
        return self._grid.y_size

    @property
    def all_coords(self) -> List[RegularCoord]:
        return [RegularCoord(*c) for c in self._grid.all_coords]

    def fill(self, value: CellContents) -> None:
        for c in self.all_coords:
            self[c] = value

    def get_nbrs(
        self, coord: RegularCoord, *, include_origin=False
    ) -> Iterable[RegularCoord]:
        return [
            RegularCoord(*c)
            for c in self._grid.get_nbrs(coord, include_origin=include_origin)
        ]

    def reset(self):
        """Reset the board to the initial state."""
        for c in self.all_coords:
            self[c] = CellContents.Unclicked

    def get_coord_at(self, x: int, y: int) -> RegularCoord:
        if RegularCoord(x, y) in self:
            return RegularCoord(x, y)
        else:
            raise ValueError("Coord out of bounds")


class SplitCellBoard(Board[Literal[GameMode.SPLIT_CELL]]):
    """A split-cell minesweeper board."""
