# March 2018, Lewis Gaul

"""
Minesweeper board implementation.

Exports
-------
.. class:: Board
    Representation of a minesweeper board.

.. class:: Minefield
    Grid representation of the positions of mines.

"""

__all__ = ("Board", "Minefield")

import random as rnd
from typing import Any, Collection, Dict, Iterable, List, Optional, Union

from ..shared import utils
from ..shared.types import CellContents, Coord_T


class Board(utils.Grid):
    """
    Representation of a minesweeper board. To be filled with instances of
    CellContents.
    """

    def __init__(self, x_size: int, y_size: int):
        """
        Arguments:
        x_size (int > 0)
            The number of columns.
        y_size (int > 0)
            The number of rows.
        """
        super().__init__(x_size, y_size, fill=CellContents.Unclicked)

    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} board>"

    def __str__(self):
        return super().__str__(mapping={CellContents.Num(0): "."})

    def __getitem__(self, item: Coord_T) -> CellContents:
        return super().__getitem__(item)

    def __setitem__(self, key: Coord_T, value: CellContents):
        if not isinstance(value, CellContents):
            raise TypeError("Board can only contain CellContents instances")
        else:
            super().__setitem__(key, value)

    @classmethod
    def from_2d_array(cls, array: List[List[Union[str, int]]]) -> "Board":
        """
        Create a minesweeper board from a 2-dimensional array of string
        representations for cell contents.

        Arguments:
        array ([[str|int, ...], ...])
            The array to create the board from.

        Return:
            The created board.

        Raises:
        ValueError
            - Invalid string representation of cell contents.
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

    def reset(self):
        """Reset the board to the initial state."""
        for c in self.all_coords:
            self[c] = CellContents.Unclicked


class Minefield(utils.Grid):
    """
    Grid representation of a minesweeper minefield, with each cell containing
    an integer representing the number of mines in that cell.
    """

    def __init__(
        self,
        x_size: int,
        y_size: int,
        *,
        mines: Union[int, Iterable[Coord_T]],
        per_cell: int = 1,
        safe_coords: Optional[Iterable[Coord_T]] = None,
    ):
        """
        :param x_size:
            Number of columns in the grid.
        :param y_size:
            Number of rows in the grid.
        :param mines:
            Either the number of mines to randomly place, or an iterable of
            coordinates to place mines at.
        :param per_cell:
            Maximum number of mines per cell.
        :param safe_coords:
            Optionally specify coordinates that should not contain a mine when
            filling the minefield. Ignored if a list of mine coords is passed
            in.
        :raise ValueError:
            If the number of mines is too high to fit in the grid or if a list
            of mine coordinates is supplied and the number of mines in a cell
            exceeds the max per cell value.
        """
        super().__init__(x_size, y_size)
        # Maximum number of mines per cell.
        self.per_cell: int = per_cell
        # Number of mines.
        self.nr_mines: int
        # List of cell coordinates containing mines.
        self.mine_coords: List[Coord_T]
        # The successfully completed board for the minefield.
        self.completed_board: Board
        # Groups of cells that form the board openings.
        self.openings: Collection[Collection[Coord_T]]
        # The 3bv of the minefield.
        self.bbbv: int

        if isinstance(mines, int):
            self.nr_mines = mines
            mine_coords = self._choose_mine_coords(safe_coords)
        else:
            mine_coords = list(mines)
            self.nr_mines = len(mine_coords)

        for c in mine_coords:
            if self[c] == self.per_cell:
                raise ValueError(
                    f"Too many mines at coord {c} with max per cell of {self.per_cell}"
                )
            self[c] += 1
        self.mine_coords = mine_coords
        self.completed_board = self._calc_completed_board()
        self.openings = self._find_openings()
        self.bbbv = self._calc_3bv()

    def __repr__(self):
        mines_str = f" with {self.nr_mines} mines" if self.nr_mines else ""
        return f"<{self.x_size}x{self.y_size} minefield{mines_str}>"

    @classmethod
    def from_grid(cls, grid: utils.Grid, *, per_cell: int = 1) -> "Minefield":
        """
        Create a minefield with a grid showing where mines are to lie.

        :param grid:
            The grid of mines.
        :param per_cell:
            Maximum number of mines per cell. Should not be exceeded by any of
            the values in the grid.
        :return:
            The created minefield.
        """
        mine_coords = []
        for c in grid.all_coords:
            for _ in range(grid[c]):
                mine_coords.append(c)

        return cls(grid.x_size, grid.y_size, mines=mine_coords, per_cell=per_cell)

    @classmethod
    def from_2d_array(cls, array: List[List[int]], *, per_cell: int = 1) -> "Minefield":
        """
        See minegauler.core.utils.Grid and Minefield.from_grid().
        """
        return cls.from_grid(utils.Grid.from_2d_array(array), per_cell=per_cell)

    @classmethod
    def from_json(cls, dict_: Dict[str, Any]) -> "Minefield":
        """
        Create a minefield instance from a JSON encoding.

        :param dict_:
            The dictionary obtained from decoding JSON. Must contain the
            following fields: 'x_size', 'y_size', 'mine_coords'.
        :raise ValueError:
            If the dictionary is missing required fields.
        """
        try:
            return cls(
                dict_["x_size"],
                dict_["y_size"],
                mines=[tuple(c) for c in dict_["mine_coords"]],
                per_cell=dict_.get("per_cell", 1),
            )
        except KeyError as e:
            raise ValueError(
                "Missing key in dictionary when trying to create minefield"
            ) from e

    def to_json(self) -> Dict[str, Any]:
        """Convert to a JSON-serialisable format."""
        return dict(
            x_size=self.x_size,
            y_size=self.y_size,
            mine_coords=self.mine_coords,
            per_cell=self.per_cell,
        )

    def _choose_mine_coords(
        self, safe_coords: Optional[Iterable[Coord_T]] = None
    ) -> List[Coord_T]:
        """
        Randomly choose coordinates for mines to be in.

        :param safe_coords:
            Optionally specify coordinates that should not contain a mine when
            filling the minefield. Ignored if a list of mine coords is passed
            in.
        :return:
            A list of randomly chosen mine coords.
        :raise ValueError:
            If the number of mines is too high to fit in the grid.
        """
        safe_coords = set(safe_coords) if safe_coords else None
        self.check_enough_space(
            x_size=self.x_size,
            y_size=self.y_size,
            mines=self.nr_mines,
            per_cell=self.per_cell,
            nr_safe_cells=len(safe_coords) if safe_coords else 1,
        )

        # Get a list of coordinates which can have mines placed in them.
        if safe_coords is None:
            avble_coords = self.all_coords.copy()
        else:
            avble_coords = [c for c in self.all_coords if c not in safe_coords]
        # Make sure there is at least one safe cell.
        if len(avble_coords) == len(self.all_coords):
            avble_coords.pop(rnd.randint(0, len(avble_coords) - 1))
        avble_coords *= self.per_cell
        rnd.shuffle(avble_coords)
        return avble_coords[: self.nr_mines]

    @staticmethod
    def check_enough_space(
        *, x_size: int, y_size: int, mines: int, per_cell: int, nr_safe_cells: int = 1
    ) -> None:
        """
        Check there is enough space in the grid for the mines.

        :param x_size:
            Number of columns in the grid.
        :param y_size:
            Number of rows in the grid.
        :param mines:
            The number of mines.
        :param per_cell:
            Maximum number of mines per cell.
        :param nr_safe_cells:
            The number of cells to leave safe.
        :raise ValueError:
            If the number of mines is too high to fit in the grid.
        """
        mine_spaces = x_size * y_size - nr_safe_cells
        if mines > mine_spaces * per_cell:
            raise ValueError(
                f"Number of mines too high ({mines}) for grid with {mine_spaces} spaces "
                f"and only up to {per_cell} allowed per cell"
            )

    def cell_contains_mine(self, coord: Coord_T) -> bool:
        """
        Return whether a cell contains at least one mine.

        :param coord:
            The coordinate to check.
        :return:
            Whether the cell contains a mine.
        """
        return self[coord] > 0

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
                for nbr in self.get_nbrs(c):
                    # For neighbouring cells that don't contain mines, increment
                    #  their number.
                    if not self.cell_contains_mine(nbr):
                        completed_board[nbr] += mines
        return completed_board

    def _find_openings(self) -> List[List[Coord_T]]:
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
            #  considered, start a new opening.
            opening = {orig_coord}  # Coords belonging to the opening
            check = {orig_coord}  # Coords whose neighbours need checking
            while check:
                coord = check.pop()
                nbrs = set(self.get_nbrs(coord))
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
        assert self.openings is not None
        clicks = len(self.openings)
        exposed = len({c for opening in self.openings for c in opening})
        clicks += self.x_size * self.y_size - len(set(self.mine_coords)) - exposed
        return clicks
