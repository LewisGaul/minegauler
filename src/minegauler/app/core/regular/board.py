# October 2021, Lewis Gaul

import logging
import subprocess
from typing import Iterable, List, Mapping, Union

import zig_minesolver as minesolver  # TODO: Rename the package

from ...shared import utils
from ...shared.types import CellContents, GameMode, ReachSetting
from ..board import BoardBase
from .types import Coord


logger = logging.getLogger(__name__)


class Board(BoardBase):
    """A regular minesweeper board."""

    mode = GameMode.REGULAR

    def __init__(
        self, x_size: int, y_size: int, *, reach: ReachSetting = ReachSetting.NORMAL
    ):
        self._grid = utils.Grid(x_size, y_size, fill=CellContents.Unclicked)
        self._reach = reach

    @classmethod
    def from_2d_array(cls, array: List[List[Union[str, int]]]) -> "Board":
        """
        Create an instance from a 2-dimensional array.

        Cell representations:
         - Numbers are represented by ints
         - Unclicked cells are represented by '#'
         - Flags are represented by e.g. 'F1'
         - Mines are represented by e.g. 'M1'
         - Wrong flags are represented by e.g. 'X1'
         - Hit mines are represented by e.g. '!1'
        """
        grid = utils.Grid.from_2d_array(array)
        board = cls(grid.x_size, grid.y_size)
        for c in grid.all_coords:
            if type(grid[c]) is int:
                board[c] = CellContents.Num(grid[c])
            elif type(grid[c]) is str and len(grid[c]) == 2:
                char, num = grid[c]
                board[c] = CellContents.from_char(char)(int(num))
            elif grid[c] != CellContents.Unclicked.char:
                raise ValueError(
                    f"Unknown cell contents representation in cell {c}: {grid[c]}"
                )
        return board

    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} board>"

    def __str__(self):
        return self._grid.__str__(mapping={CellContents.Num(0): "."})

    def __eq__(self, other) -> bool:
        if not isinstance(other, Board):
            return False
        return self._grid == other._grid

    def __getitem__(self, coord: Coord) -> CellContents:
        return self._grid[coord]

    def __setitem__(self, coord: Coord, value: CellContents):
        if not isinstance(value, CellContents):
            raise TypeError("Board can only contain CellContents instances")
        self._grid[coord] = value

    def __contains__(self, coord: Coord) -> bool:
        return coord in self.all_coords

    @property
    def x_size(self) -> int:
        return self._grid.x_size

    @property
    def y_size(self) -> int:
        return self._grid.y_size

    @property
    def reach(self) -> ReachSetting:
        return self._reach

    @property
    def all_coords(self) -> List[Coord]:
        return [Coord(*c) for c in self._grid.all_coords]

    def fill(self, value: CellContents) -> None:
        for c in self.all_coords:
            self[c] = value

    def get_nbrs(self, coord: Coord, *, include_origin=False) -> Iterable[Coord]:
        return [
            Coord(*c)
            for c in self._grid.get_nbrs(
                coord, include_origin=include_origin, reach=self.reach
            )
        ]

    def get_coord_at(self, x: int, y: int) -> Coord:
        if x < 0 or x >= self.x_size or y < 0 or y >= self.y_size:
            raise ValueError(f"Position out of bounds: ({x}, {y})")
        return Coord(x, y)

    def calculate_probs(
        self, mines: int, *, per_cell: int = 1
    ) -> Mapping[Coord, float]:
        """Calculate mine probabilities for the board."""
        if self._reach is not ReachSetting.NORMAL:
            raise NotImplementedError

        def cell_repr(cell: CellContents):
            if isinstance(cell, CellContents.MineBase):
                return CellContents.Unclicked
            else:
                return cell

        try:
            probs = minesolver.get_board_probs(
                self._grid.__str__(mapping=cell_repr), mines=mines, per_cell=per_cell
            )
        except subprocess.CalledProcessError as e:
            logger.debug("Output from zig_minesolver:\n%s%s", e.stderr, e.stdout)
            raise RuntimeError("Unable to calculate probabilities") from e

        return {
            c: probs[c.y][c.x]
            for c in self.all_coords
            if self[c] is CellContents.Unclicked
        }

    def reset(self):
        """Reset the board to the initial state."""
        for c in self.all_coords:
            self[c] = CellContents.Unclicked
