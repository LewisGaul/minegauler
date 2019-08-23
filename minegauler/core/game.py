"""
game.py - Game logic

March 2018, Lewis Gaul

Exports:
Board (class)
    Representation of a minesweeper board.
Game (class)
    Representation of a minesweeper game.
"""

import logging

from minegauler.shared.grid import Grid
from minegauler.shared.internal_types import *


logger = logging.getLogger(__name__)
        
        
class Board(Grid):
    """
    Representation of a minesweeper board. Can only be filled with objects that
    inherit CellContentsType.
    """
    def __init__(self, x_size, y_size):
        """
        Arguments:
        x_size (int > 0)
            The number of columns.
        y_size (int > 0)
            The number of rows.
        """
        super().__init__(x_size, y_size, fill=CellUnclicked())
        
    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} board>"

    def __str__(self):
        return super().__str__(mapping={CellNum(0): '.'})

    def __setitem__(self, key, value):
        if not isinstance(value, CellContentsType):
            raise TypeError("Board can only contain CellContentsType instances")
        else:
            super().__setitem__(key, value)

    @classmethod
    def from_2d_array(cls, array):
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
        grid = Grid.from_2d_array(array)
        board = cls(grid.x_size, grid.y_size)
        for c in grid.all_coords:
            if type(grid[c]) is int:
                board[c] = CellNum(grid[c])
            elif type(grid[c]) is str and len(grid[c]) == 2:
                char, num = grid[c]
                board[c] = CellMineType.get_class_from_char(char)(int(num))
            elif grid[c] != CellUnclicked.char:
                raise ValueError(
                    f"Unknown cell contents representation in cell {c}: "
                    f"{grid[c]}")
        return board


class Game:
    def __init__(self, *, x_size, y_size, mines, per_cell=1):
        self.x_size, self.y_size = x_size, y_size
        self.mines = mines
        self.per_cell = per_cell
        self.mf = None
        self.board = Board(x_size, y_size)
        self.start_time = None
        self.end_time = None
        self.state = GameState.READY

    def get_rem_3bv(self):
        """Calculate the minimum remaining number of clicks needed to solve."""
        if self.state == Game.WON:
            return 0
        elif self.state == Game.READY:
            return self.mf.bbbv
        else:
            lost_mf = Minefield(auto_create=False, **self.settings)
            lost_mf.mine_coords = self.mf.mine_coords
            # Replace any openings already found with normal clicks (ones).
            lost_mf.completed_grid = np.where(self.grid<0,
                                              self.mf.completed_grid, 1)
            # Find the openings which remain.
            lost_mf.get_openings()
            rem_opening_coords = [c for opening in lost_mf.openings
                                  for c in opening]
            # Count the number of essential clicks that have already been
            # done by counting clicked cells minus the ones at the edge of
            # an undiscovered opening.
            completed_3bv = len({c for c in where_coords(self.grid >= 0)
                                 if c not in rem_opening_coords})
            return lost_mf.get_3bv() - completed_3bv

    def get_prop_complete(self):
        """Calculate the progress of solving the board using 3bv."""
        return float(self.mf.bbbv - self.get_rem_3bv())/self.mf.bbbv

    def get_3bvps(self):
        """Return the 3bv/s."""
        if self.start_time:
            return (self.mf.bbbv *
                    self.get_prop_complete() / self.get_time_passed())
