# At the most basic level, all the minefield needs to do is choose where mines
# are going to be in the available cells. The simplest way to implement this
# (and therefore easiest to make generic) is to pass in a list of coordinates
# that can contain mines, and the minefield then just places mines in those
# coordinates.
# The responsibility of calculating properties of the minefield (e.g. 3bv, final
# board, ...) can go in mode-specific implementations (e.g. subclasses).

__all__ = ("Minefield", "RegularMinefield")

import random
from typing import Generic, Iterable, List, Optional, Set

from minegauler.core.board import RegularBoard
from minegauler.shared.types import CellContents

from .coord import Coord, RegularCoord


class Minefield(Generic[Coord]):
    """Representation of a minesweeper minefield."""

    def __init__(
        self, all_coords: Iterable[Coord], *, mines: int, per_cell: int = 1,
    ):
        """
        :param all_coords:
            Iterable of coords where mines may lie.
        :param mines:
            The number of mines to randomly place.
        :param per_cell:
            Maximum number of mines per cell.
        :raise ValueError:
            If the number of mines is too high.
        """
        self.all_coords: Set[Coord] = set(all_coords)
        self.mines: int = mines
        self.per_cell: int = per_cell
        self.mine_coords: List[Coord] = []

        # Perform some checks on the args.
        if self.per_cell < 1:
            raise ValueError(
                f"Max mines per cell must be at least 1, got {self.per_cell}"
            )
        if self.mines < 1:
            raise ValueError(f"Number of mines must be at least 1, got {self.mines}")
        mine_spaces = len(self.all_coords) - 1
        if self.mines > mine_spaces * self.per_cell:
            raise ValueError(
                f"Number of mines too high: {self.mines} in {mine_spaces} "
                f"spaces with max {self.per_cell} per cell"
            )

    @classmethod
    def from_coords(
        cls,
        all_coords: Iterable[Coord],
        *,
        mine_coords: Iterable[Coord],
        per_cell: int = 1,
    ) -> "Minefield":
        """
        :param all_coords:
            Iterable of coords where mines may lie.
        :param mine_coords:
            Iterable of coords containing mines.
        :param per_cell:
            Maximum number of mines per cell.
        :raise ValueError:
            If the number of mines is too high.
        """
        mine_coords = list(mine_coords)
        if any(mine_coords.count(c) > per_cell for c in mine_coords):
            raise ValueError(
                f"Max number of mines per cell is {per_cell}, too many in: "
                + ", ".join(c for c in mine_coords if mine_coords.count(c) > per_cell)
            )
        self = cls(all_coords, mines=len(mine_coords), per_cell=per_cell)
        self.mine_coords = mine_coords
        return self

    def __repr__(self):
        return f"<Minefield with {len(self.all_coords)} coords, {self.mines} mines>"

    def __getitem__(self, coord: Coord) -> int:
        if coord not in self.all_coords:
            raise ValueError(f"Invalid coord '{coord}'")
        return self.mine_coords.count(coord)

    def populate(self, safe_coords: Optional[Iterable[Coord]] = None) -> None:
        """
        Randomly place mines in the available coordinates.

        :param safe_coords:
            Optional iterable of coords that should not contain a mine when
            filling the minefield.
        :return:
            A list of randomly chosen mine coords.
        :raise ValueError:
            If the number of mines is too high.
        """
        safe_coords = set(safe_coords) if safe_coords else None
        mine_spaces = len(self.all_coords) - (len(safe_coords) if safe_coords else 1)

        if self.mines > mine_spaces * self.per_cell:
            raise ValueError(
                f"Number of mines too high: {self.mines} in {mine_spaces} "
                f"spaces with max {self.per_cell} per cell"
            )

        # Get a list of coordinates which can have mines placed in them.
        # Make sure there is at least one safe cell.
        avble_coords = set(self.all_coords)
        if safe_coords:
            avble_coords -= safe_coords
        else:
            avble_coords.remove(random.choice(tuple(avble_coords)))

        avble_coords = list(avble_coords) * self.per_cell
        random.shuffle(avble_coords)
        self.mine_coords = avble_coords[: self.mines]


class RegularMinefield(Minefield[RegularCoord]):
    """A regular minesweeper minefield."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x_size: int = max({c[0] for c in self.all_coords}) + 1
        self.y_size: int = max({c[1] for c in self.all_coords}) + 1
        self._bbbv: Optional[int] = None
        self._openings: Optional[List[List[RegularCoord]]] = None
        self._completed_board: Optional[RegularBoard] = None

    def __str__(self):
        max_nr_mines = max(self[c] for c in self.all_coords)
        cell_size = len(repr(max_nr_mines))

        cell = "{:>%d}" % cell_size
        ret = ""
        for y in range(self.y_size):
            for x in range(self.x_size):
                ret += cell.format(self[RegularCoord((x, y))]) + " "
            ret = ret[:-1]  # Remove trailing space
            ret += "\n"
        ret = ret[:-1]  # Remove trailing newline

        return ret

    @classmethod
    def from_dimensions(
        cls, x_size: int, y_size: int, *, mines: int, per_cell: int = 1
    ) -> "RegularMinefield":
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
        all_coords = [
            RegularCoord((x, y)) for x in range(x_size) for y in range(y_size)
        ]
        return cls(all_coords, mines=mines, per_cell=per_cell)

    @property
    def bbbv(self) -> int:
        if not self.mine_coords:
            raise AttributeError("Unitialised minefield has no 3bv")
        if self._bbbv is None:
            self._bbbv = self._calc_3bv()
        return self._bbbv

    @property
    def openings(self) -> List[List[RegularCoord]]:
        if not self.mine_coords:
            raise AttributeError("Unitialised minefield has no openings")
        if self._openings is None:
            self._openings = self._find_openings()
        return self._openings

    @property
    def completed_board(self) -> RegularBoard:
        if not self.mine_coords:
            raise AttributeError("Unitialised minefield has no openings")
        if self._completed_board is None:
            self._completed_board = self._find_completed_board()
        return self._completed_board

    def _get_nbrs(
        self, coord: RegularCoord, *, include_origin=False
    ) -> Iterable[RegularCoord]:
        """
        Get coordinates of neighbouring cells.
        """
        x, y = coord
        nbrs = []
        for i in range(max(0, x - 1), min(self.x_size, x + 2)):
            for j in range(max(0, y - 1), min(self.y_size, y + 2)):
                nbrs.append(RegularCoord((i, j)))
        if not include_origin:
            nbrs.remove(coord)
        return nbrs

    def _find_completed_board(self) -> RegularBoard:
        """
        Create the completed board with the flags and numbers that should be
        seen upon game completion.
        """
        completed_board = RegularBoard(self.x_size, self.y_size)
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

    def _find_openings(self) -> List[List[RegularCoord]]:
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

    def _calc_3bv(self) -> int:
        """Calculate the 3bv of the board."""
        clicks = len(self.openings)
        exposed = len({c for opening in self.openings for c in opening})
        clicks += self.x_size * self.y_size - len(set(self.mine_coords)) - exposed
        return clicks
