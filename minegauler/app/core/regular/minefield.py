# October 2021, Lewis Gaul

__all__ = ("Minefield", "RegularMinefieldBase")

import abc
from typing import Any, Iterable, List, Mapping, Optional, TypeVar

from ...shared import utils
from ...shared.types import CellContents
from ...shared.types import Coord as CoordBase
from ..board import BoardBase
from ..minefield import MinefieldBase
from .board import Board
from .types import Coord


C = TypeVar("C", bound=CoordBase)
B = TypeVar("B", bound=BoardBase)


class RegularMinefieldBase(MinefieldBase[C, B], metaclass=abc.ABCMeta):
    """The base for a minefield with regular coords."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x_size: int = max({c.x for c in self.all_coords}) + 1
        self.y_size: int = max({c.y for c in self.all_coords}) + 1

    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} minefield with {self.mines} mines>"

    def __str__(self):
        max_nr_mines = max(self[c] for c in self.all_coords)
        cell_size = len(repr(max_nr_mines))

        cell = "{:>%d}" % cell_size
        ret = ""
        for y in range(self.y_size):
            for x in range(self.x_size):
                ret += cell.format(self[Coord(x, y)]) + " "
            ret = ret[:-1]  # Remove trailing space
            ret += "\n"
        ret = ret[:-1]  # Remove trailing newline

        return ret

    @classmethod
    def from_dimensions(
        cls, x_size: int, y_size: int, *, mines: int, per_cell: int = 1
    ) -> "RegularMinefieldBase":
        """
        :param x_size:
            Number of columns in the grid.
        :param y_size:
            Number of rows in the grid.
        :param mines:
            The number of mines to randomly place.
        :param per_cell:
            Maximum number of mines per cell.
        :raise ValueError:
            If the number of mines is too high.
        """
        all_coords = [Coord(x, y) for x in range(x_size) for y in range(y_size)]
        return cls(all_coords, mines=mines, per_cell=per_cell)

    @classmethod
    def from_grid(
        cls, grid: utils.Grid, *, per_cell: int = 1
    ) -> "RegularMinefieldBase":
        """
        :param grid:
            A `Grid` instance containing int number of mines in each cell.
        :param per_cell:
            Maximum number of mines per cell.
        :raise ValueError:
            If any of the number of mines is too high.
        """
        mine_coords = []
        for c in grid.all_coords:
            for _ in range(grid[c]):
                mine_coords.append(Coord(*c))
        return cls.from_coords(
            (Coord(*c) for c in grid.all_coords),
            mine_coords=mine_coords,
            per_cell=per_cell,
        )

    @classmethod
    def from_2d_array(cls, array, *, per_cell: int = 1) -> "RegularMinefieldBase":
        """
        :param array:
            2D array containing int number of mines in each cell.
        :param per_cell:
            Maximum number of mines per cell.
        :raise ValueError:
            If any of the number of mines is too high.
        """
        return cls.from_grid(utils.Grid.from_2d_array(array), per_cell=per_cell)


class Minefield(RegularMinefieldBase[Coord, Board]):
    """A regular minesweeper minefield."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._openings: Optional[List[List[Coord]]] = None

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> "Minefield":
        """
        Create a minefield instance from a JSON encoding.

        :param obj:
            The dictionary obtained from decoding JSON. Must contain the
            following fields: 'x_size', 'y_size', 'mine_coords'.
        :raise ValueError:
            If the dictionary is missing required fields.
        """
        try:
            return cls.from_coords(
                (
                    Coord(x, y)
                    for x in range(obj["x_size"])
                    for y in range(obj["y_size"])
                ),
                mine_coords=[Coord(*c) for c in obj["mine_coords"]],
                per_cell=obj.get("per_cell", 1),
            )
        except KeyError as e:
            raise ValueError(
                "Missing key in dictionary when trying to create minefield"
            ) from e

    def to_json(self) -> Mapping[str, Any]:
        return dict(
            type="regular",
            x_size=self.x_size,
            y_size=self.y_size,
            mine_coords=self.mine_coords,
            per_cell=self.per_cell,
        )

    def _get_nbrs(self, coord: Coord, *, include_origin=False) -> Iterable[Coord]:
        """Get coordinates of neighbouring cells."""
        x, y = coord
        nbrs = []
        for i in range(max(0, x - 1), min(self.x_size, x + 2)):
            for j in range(max(0, y - 1), min(self.y_size, y + 2)):
                nbrs.append(Coord(i, j))
        if not include_origin:
            nbrs.remove(coord)
        return nbrs

    def _calc_3bv(self) -> int:
        """Calculate the 3bv of the board."""
        clicks = len(self.openings)
        exposed = len({c for opening in self.openings for c in opening})
        clicks += self.x_size * self.y_size - len(set(self.mine_coords)) - exposed
        return clicks

    def _calc_completed_board(self) -> Board:
        """
        Create the completed board with the flags and numbers that should be
        seen upon game completion.
        """
        completed_board = Board(self.x_size, self.y_size)
        completed_board.fill(CellContents.Num(0))
        for c in self.all_coords:
            mines = self[c]
            if mines > 0:
                completed_board[c] = CellContents.Flag(mines)
                for nbr in self._get_nbrs(c):
                    # For neighbouring cells that don't contain mines, increment
                    # their number.
                    if nbr not in self.mine_coords:
                        completed_board[nbr] += mines
        return completed_board

    def _find_openings(self) -> List[List[Coord]]:
        """
        Find the openings of the board.

        A list of openings is stored, each represented as a list of
        coordinates belonging to that opening. Note that each cell
        cannot belong to multiple openings.
        """
        openings = []
        blanks_to_check = {
            c for c in self.all_coords if self.completed_board[c] is CellContents.Num(0)
        }
        while blanks_to_check:
            orig_coord = blanks_to_check.pop()
            # If the coordinate is part of an opening and hasn't already been
            # considered, start a new opening.
            opening = {orig_coord}  # Coords belonging to the opening
            check = {orig_coord}  # Coords whose neighbours need checking
            while check:
                coord = check.pop()
                nbrs = set(self._get_nbrs(coord))
                check |= {
                    c
                    for c in nbrs - opening
                    if self.completed_board[c] is CellContents.Num(0)
                }
                opening |= nbrs
            openings.append(sorted(opening))
            blanks_to_check -= opening
        return openings
