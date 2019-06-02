"""
grid.py - 2D grid implementation

June 2019, Lewis Gaul

Exports:
Grid (class)
    Representation of a 2D grid using nested lists.
"""

class Grid(list):
    """
    Grid representation using a list of lists (2D array).

    Attributes:
    x_size (int > 0)
        The number of columns.
    y_size (int > 0)
        The number of rows.
    all_coords ([(int, int), ...])
        List of all coordinates in the grid.
    """
    def __init__(self, x_size, y_size, *, fill=0):
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
        #@@@LG Some attention please :)

        # Use max length of object representation if no cell size given.
        if cell_size is None:
            cell_size = max(
                           [len(obj.__repr__()) for row in self for obj in row])

        cell = '{:>%d}' % cell_size
        ret = ''
        for row in self:
            for obj in row:
                if isinstance(mapping, dict):
                    rep = str(mapping[obj]) if obj in mapping else repr(obj)
                elif mapping is not None:
                    rep = str(mapping(obj))
                else:
                    rep = repr(obj)
                ret += cell.format(rep[:cell_size]) + ' '
            ret = ret[:-1]  # Remove trailing space
            ret += '\n'
        ret = ret[:-1]  # Remove trailing newline

        return ret

    def __getitem__(self, key):
        if type(key) is tuple and len(key) == 2:
            return self[key[1]][key[0]]
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        if type(key) is tuple and len(key) == 2:
            self[key[1]][key[0]] = value
        else:
            super().__setitem__(key, value)

    @classmethod
    def from_2d_array(cls, array):
        """
        Create an instance using a 2-dimensional array.

        Arguments:
        array ([[object, ...], ...])
            The array to use in creating the grid instance.

        Return: Grid
            The resulting grid.
        """
        x_size = len(array[0])
        y_size = len(array)
        grid = cls(x_size, y_size)
        for coord in grid.all_coords:
            x, y = coord
            grid[coord] = array[y][x]
        return grid

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

    def get_nbrs(self, coord, *, include_origin=False):
        """
        Get a list of the coordinates of neighbouring cells.

        Arguments:
        coord ((int, int), within grid boundaries)
            The coordinate to check.
        include_origin=False (bool)
            Whether to include the original coordinate, coord, in the list.

        Return: [(int, int), ...]
            List of coordinates within the boundaries of the grid.
        """
        x, y = coord
        nbrs = []
        for i in range(max(0, x - 1), min(self.x_size, x + 2)):
            for j in range(max(0, y - 1), min(self.y_size, y + 2)):
                nbrs.append((i, j))
        if not include_origin:
            nbrs.remove(coord)
        return nbrs