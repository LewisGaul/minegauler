"""
grid.py - Grid functionality for minesweeper boards

March 2018, Lewis Gaul
"""

from .utils import *
from .enums import *


class Grid(list):
    """Grid representation using a list of lists (2D array)."""
    def __init__(self, x_size, y_size, fill=0):
        """
        Arguments:
          x_size (int > 0)
            The number of columns.
          y_size (int > 0)
            The number of rows.
          fill=0 (object)
            What to fill the grid with.
        """
        super().__init__()
        for j in range(y_size):
            row = x_size * [fill]
            self.append(row)
        self.x_size, self.y_size = x_size, y_size
        self.all_coords = [(x, y) for x in range(x_size) for y in range(y_size)]

    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} grid>"

    def __str__(self, mapping=None, cell_size=None):
        """
        Convert the grid to a string in an aligned format. The __repr__ method
        is used to display the objects inside the grid unless the mapping
        argument is given.
        Arguments:
          mapping=None (dict | callable | None)
            A mapping to apply to all objects contained within the grid. The
            result of the mapping will be converted to a string and displayed.
            If a mapping is specified, a cell size should also be given.
          cell_size=None (int | None)
            The size to display a grid cell as. Defaults to the maximum size of
            the representation of all the objects contained in the grid.
        """
        # Convert dict mapping to function.
        if type(mapping) is dict:
            mapping = lambda obj: mapping[obj] if obj in mapping else obj
        # Use max length of object representation if no cell size given.
        if cell_size is None:
            cell_size = max(
                           [len(obj.__repr__()) for row in self for obj in row])
        cell = '{:>%d}' % cell_size
        ret = ''
        for row in self:
            for obj in row:
                if mapping is not None:
                    repr = str(mapping(obj))
                else:
                    repr = obj.__repr__()
                ret += cell.format(repr[:cell_size]) + ' '
            ret = ret[:-1] # Remove trailing space
            ret += '\n'
        ret = ret[:-1] # Remove trailing newline
        return ret

    def fill(self, item):
        """
        Fill the grid with a given object.
        Arguments:
          item (object)
            The item to fill the grid with.
        """
        for row in self:
            for i in range(len(row)):
                row[i] = item

    def get_nbrs(self, x, y, include_origin=False):
        """
        Get a list of the coordinates of neighbouring cells.
        Arguments:
          x (int, 0 <= x <= self.x_size)
            x-coordinate
          y (int, 0 <= y <= self.y_size)
            y-coordinate
          include_origin=False (bool)
            Whether to include the original coordinate, (x, y), in the list.
        Return: [(int, int), ...]
            List of coordinates within the boundaries of the grid.
        """
        nbrs = []
        for i in range(max(0, x - 1), min(self.x_size, x + 2)):
            for j in range(max(0, y - 1), min(self.y_size, y + 2)):
                nbrs.append((i, j))
        if not include_origin:
            nbrs.remove((x, y))
        return nbrs


class Board(Grid):
    """Board representation for handling displaying flags and openings."""
    def __init__(self, x_size, y_size):
        super().__init__(x_size, y_size)
        self.per_cell = 0
    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} board>"
    def __str__(self):
        def mapping(c):
            # Display openings with dashes.
            if c == 0:
                return '-'
            # Display the value from CellContents enum if it belongs to that class.
            if type(c) is CellContents:
                if self.per_cell == 1:
                    return c.value[0]
                else:
                    return c.value
            return c
        return super().__str__(mapping, cell_size=2)


class ProbBoard(Grid):
    """ProbBoard class for handling displaying board probabilities."""
    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} probability board>"
    def __str__(self):
        mapping = {}
        return super().__str__(mapping, cell_size=4)
