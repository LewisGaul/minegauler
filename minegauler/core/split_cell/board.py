# October 2021, Lewis Gaul

from typing import Iterable, List, Tuple

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
        self._unsplit_coords = {
            Coord(2 * x, 2 * y, False): CellContents.Unclicked
            for x in range(self.x_size // 2)
            for y in range(self.y_size // 2)
        }
        self._split_coords = {}

    def __eq__(self, other) -> bool:
        if not isinstance(other, Board):
            return False
        if (self.x_size, self.y_size) != (other.x_size, other.y_size):
            return False
        return self.all_coords == other.all_coords

    def __getitem__(self, coord: Coord) -> CellContents:
        if coord.is_split:
            return self._split_coords[coord]
        else:
            return self._unsplit_coords[coord]

    @property
    def all_coords(self) -> List[Coord]:
        return sorted({*self._unsplit_coords, *self._split_coords})

    def get_nbrs(self, coord, *, include_origin: bool = False) -> Iterable[Coord]:
        return []

    def get_coord_at(self, x: int, y: int) -> Coord:
        if Coord(x, y, True) in self._split_coords:
            return Coord(x, y, True)
        else:
            coord = Coord(x // 2 * 2, y // 2 * 2, False)
            assert coord in self._unsplit_coords
            return coord

    def split_coord(self, coord: Coord) -> None:
        self._unsplit_coords.pop(coord)
        self._split_coords.update({c: CellContents.Unclicked for c in coord.split()})
        # TODO: Recalculate numbers in surrounding cells
