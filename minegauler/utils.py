"""
utils.py - General utils

March 2018, Lewis Gaul
"""

from os.path import dirname, abspath, join
import enum


def get_curdir(fpath):
    return dirname(abspath(fpath))

root_dir = dirname(get_curdir(__file__))
files_dir = join(root_dir, 'files')


def ASSERT(condition, message):
    """
    The built-in assert as a function.
    """
    assert condition, message


class EnumLiteral(enum.Enum):
    """
    
    """
    def __eq__(self, obj):
        return super().__eq__(obj) or self.value == obj
    def __hash__(self):
        return hash(self.value)
    def __add__(self, obj):
        if type(obj) is int:
            return getattr(self,
                self.name[:-1] + str(int(self.value[-1]) + obj))
        else:
            return super().__add__(obj)

#@@@
CellState = EnumLiteral('CellState',
                        {'UNCLICKED': '#',
                         **{'NUM%d' % i : i for i in range(21)},
                         **{'FLAG%d' % i : 'F%d' % i for i in range(1, 11)},
                         **{'CROSS%d' % i : 'X%d' % i for i in range(1, 11)},
                         **{'MINE%d' % i : 'M%d' % i for i in range(1, 11)},
                         **{'HIT%d' % i : 'H%d' % i for i in range(1, 11)},
                         # **{'LIFE%d' % i : 'L%d' % i for i in range(1, 11)},
                         'SPLIT': '+'
                        })
CellState.NUMS    = {i: getattr(CellState, 'NUM%d' % i) for i in range(21)}
CellState.FLAGS   = {i: getattr(CellState, 'FLAG%d' % i) for i in range(1, 11)}
CellState.CROSSES = {i: getattr(CellState, 'CROSS%d' % i) for i in range(1, 11)}
CellState.MINES   = {i: getattr(CellState, 'MINE%d' % i) for i in range(1, 11)}
CellState.HITS    = {i: getattr(CellState, 'HIT%d' % i) for i in range(1, 11)}
# CellState.LIVES   = {i: getattr(CellState, 'LIFE%d' % i) for i in range(1, 11)}


class GameCellMode(enum.Enum):
    """
    The layout and behaviour modes for the cells.
    """
    NORMAL = 'Original style'
    SPLIT = 'Cells split instead of flagging'
    SPLIT1 = SPLIT
    SPLIT2 = 'Cells split twice'


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

