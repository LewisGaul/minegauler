"""
minefield.py - Implementation of a minefield object.

March 2018, Lewis Gaul
"""

import random as rnd
import logging

from .shared.utils import *
from .shared.enums import *
from .shared.grid import Grid, Board



class Minefield(Grid):
    """
    Grid representation of a minesweeper minefield, each cell contains an
    integer representing the number of mines at that cell.
    Attributes:
      mines           - number of mines
      per_cell        - maximum number of mines per cell
      mine_coords     - list of mine coordinates in (x, y) format
      completed_board - grid containing the state of the board when completed
      openings        - a list of openings, each of which is a list of
                        coordinates which are part of the opening, i.e. all
                        the cells which would be revealed if one of the cells
                        within the opening was clicked
      bbbv            - the 3bv of the game
    """
    def __init__(self, x_size, y_size):
        """
        See 'utils.grid.Grid'.
        """
        super().__init__(x_size, y_size)
        self.mines = 0
        self.per_cell = 0
        self.mine_coords = None
        self.completed_board = None
        self.openings = None
        self.bbbv = None

    def __repr__(self):
        mines_str = f" with {self.mines} mines" if self.mines else ""
        return f"<{self.x_size}x{self.y_size} minefield{mines_str}>"

    def create_from_list(self, coords, per_cell):
        """
        Fill in the minefield with a list of coordinates of where mines are to
        be hidden. Also get the completed board, openings and 3bv for the
        created minefield.
        Arguments:
          coords ([(int, int), ...])
            List of mine coordinates, which must fit within the dimensions of
            the minefield.
          per_cell (int > 0)
            The maximum number of mines per cell. The number of occurrences of
            any of the coordinates in the list of coordinates must not exceed
            per_cell.
        """
        ASSERT(self.mines == 0, "Minefield already created.")
        self.mine_coords = coords
        self.per_cell = per_cell
        self.mines = len(self.mine_coords)
        for (x, y) in coords:
            self[y][x] += 1
            ASSERT(self[y][x] <= self.per_cell,
                   "Exceeded number of expected mines in single cell")
        self.get_completed_board()
        self.find_openings()
        self.calc_3bv()

    def create(self, mines, per_cell, safe_coords=None):
        """
        Fill in the minefield at random. Also get the completed board and 3bv
        for the created minefield. This is done by making a list of random
        coordinates and passing it to self.create_from_list().
        Arguments:
          mines (int > 0)
            The number of mines to place in the minefield.
          per_cell (int > 0)
            The maximum number of mines allowed in a cell.
          safe_coords ([(int, int), ...] | None)
            List of coordinates which must not contain any mines.
        """
        # Perform some sanity checks.
        ASSERT(self.mines == 0, "Minefield already created.")
        ASSERT(mines < (self.x_size*self.y_size - 1) * per_cell,
               f"Too many mines ({mines}) "
               f"for grid with dimensions {self.x_size} x {self.y_size} "
               f"and only up to {per_cell} allowed per cell.")
        # Get a list of coordinates which can have mines placed in them.
        if safe_coords is None:
            safe_coords = []
            avble_coords = self.all_coords.copy()
        else:
            ASSERT(type(safe_coords) is list, "Expected list of safe coords")
            avble_coords = [c for c in self.all_coords if c not in safe_coords]
        # Can't give opening on first click if too many mines.
        if mines > len(avble_coords) * per_cell:
            logging.warning(
                "Unable to create minefield with requested safe_coords - "
                "too many mines ({} mines, {} cells, {} safe_coords).".format(
                    mines, self.x_size*self.y_size, len(safe_coords)))
            avble_coords = self.all_coords.copy()
        avble_coords *= per_cell
        rnd.shuffle(avble_coords)
        # Pass on the beginning of the shuffled list of coordinates to be used
        #  to fill in the minefield with.
        self.create_from_list(avble_coords[:mines], per_cell)

    def cell_contains_mine(self, x, y):
        """
        Does a cell contain at least one mine.
        Arguments:
          x (int, 0 <= x <= self.x_size)
            x-coordinate
          y (int, 0 <= y <= self.y_size)
            y-coordinate
        Return: bool
            Whether the cell contains a mine.
        """
        return self[y][x] > 0

    def get_completed_board(self):
        """
        Create and fill the completed board with the flags and numbers that
        should be seen upon game completion.
        """
        self.completed_board = Board(self.x_size, self.y_size)
        # Store the per_cell on the completed board for nicer printing.
        self.completed_board.per_cell = self.per_cell
        for (x, y) in self.all_coords:
            mines = self[y][x]
            if mines > 0:
                self.completed_board[y][x] = CellContents.FLAGS[mines]
                for (i, j) in self.get_nbrs(x, y):
                    # For cells that don't contain mines, increment their
                    #  numbers as appropriate.
                    if not self.cell_contains_mine(i, j):
                        self.completed_board[j][i] += mines

    def find_openings(self):
        """
        Find the openings of the board. A list of openings is stored, each
        represented as a list of coordinates belonging to that opening.
        Note that each cell can only belong to up to one opening.
        """
        self.openings = []
        all_found = set()
        for coord in self.all_coords:
            x, y = coord
            # If the coordinate is part of an opening and hasn't already been
            #  considered, start a new opening.
            if self.completed_board[y][x] == 0 and coord not in all_found:
                opening = {coord} # Coords belonging to the opening
                check = {coord}   # Coords whose neighbours need checking
                while check:
                    c = check.pop()
                    nbrs = set(self.get_nbrs(*c))
                    check |= {(i, j) for (i, j) in nbrs - opening
                                             if self.completed_board[j][i] == 0}
                    opening |= nbrs
                self.openings.append(sorted(opening))
                all_found |= opening

    def calc_3bv(self):
        """
        Calculate the 3bv of the board.
        """
        ASSERT(self.openings is not None,
               "Must find openings before 3bv can be calculated.")
        clicks = len(self.openings)
        exposed = len({c for opening in self.openings for c in opening})
        clicks += self.x_size*self.y_size - len(set(self.mine_coords)) - exposed
        self.bbbv = clicks





if __name__ == '__main__':
    print("Running minefield.py")
    dims_str = input("Input dimensions of minefield to create e.g. 8, 10:   ")
    dims = list(map(int, dims_str.replace(',', ' ').split()))
    mf = Minefield(*dims)
    mines = int(input("Input number of mines:   "))
    mf.create(mines, per_cell=1)
    print(mf)
    print("Completed board:")
    print(mf.completed_board)
