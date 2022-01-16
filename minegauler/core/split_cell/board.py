# October 2021, Lewis Gaul

from typing import Iterable, List

from ...shared.types import CellContents, GameMode
from ..board import BoardBase
from .types import Coord


class Board(BoardBase):
    """A split-cell minesweeper board."""

    mode = GameMode.SPLIT_CELL

    def __init__(self, x_size: int, y_size: int):
        """
        :param x_size:
            Number of small cells in x direction.
        :param y_size:
            Number of small cells in y direction.
        """
        self.x_size = x_size
        self.y_size = y_size
        self._all_coords = {
            Coord(2 * x, 2 * y, False): CellContents.Unclicked
            for x in range(self.x_size // 2)
            for y in range(self.y_size // 2)
        }

    def __eq__(self, other) -> bool:
        if not isinstance(other, Board):
            return False
        if (self.x_size, self.y_size) != (other.x_size, other.y_size):
            return False
        return self.all_coords == other.all_coords

    def __getitem__(self, coord: Coord) -> CellContents:
        return self._all_coords[coord]

    def __setitem__(self, coord: Coord, obj: CellContents) -> None:
        # TODO: This seems desirable, but is used for displaying hit mines...
        # if coord not in self:
        #     raise KeyError(f"{coord} not in board")
        self._all_coords[coord] = obj

    def __contains__(self, coord: Coord):
        return coord in self._all_coords

    @property
    def all_coords(self) -> List[Coord]:
        return sorted(self._all_coords)

    @property
    def all_underlying_coords(self) -> List[Coord]:
        return [
            Coord(x, y, True) for x in range(self.x_size) for y in range(self.y_size)
        ]

    def copy(self) -> "Board":
        new_board = type(self)(self.x_size, self.y_size)
        new_board._all_coords = self._all_coords.copy()
        return new_board

    def get_nbrs(
        self, coord: Coord, *, include_origin: bool = False
    ) -> Iterable[Coord]:
        if coord not in self.all_coords:
            raise ValueError(f"{coord} not in board")
        x_min = max(0, coord.x - 1)
        y_min = max(0, coord.y - 1)
        if coord.is_split:
            x_max = min(self.x_size - 1, coord.x + 1)
            y_max = min(self.y_size - 1, coord.y + 1)
        else:
            x_max = min(self.x_size - 1, coord.x + 2)
            y_max = min(self.y_size - 1, coord.y + 2)
        nbrs = set()
        for i in range(x_min, x_max + 1):
            for j in range(y_min, y_max + 1):
                nbrs.add(self.get_coord_at(i, j))
        if not include_origin:
            nbrs.remove(coord)
        return sorted(nbrs)

    def get_coord_at(self, x: int, y: int) -> Coord:
        split = Coord(x, y, True)
        unsplit = Coord(x // 2 * 2, y // 2 * 2, False)
        if split in self._all_coords:
            return split
        elif unsplit in self._all_coords:
            return unsplit
        else:
            raise ValueError(f"Position out of bounds: ({x}, {y})")

    def split_coord(self, coord: Coord) -> None:
        self._all_coords.pop(coord)
        self._all_coords.update({c: CellContents.Unclicked for c in coord.split()})
