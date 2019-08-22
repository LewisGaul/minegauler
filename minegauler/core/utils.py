"""
utils.py - Utilities

March 2018, Lewis Gaul

Exports:
Grid (class)
    Representation of a 2D grid using nested lists.
Board (class)
    Representation of a minesweeper board, inheriting from Grid.
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
