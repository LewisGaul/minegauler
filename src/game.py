# Button states are:
#     UNCLICKED
#     MINE

# Game states
#     READY
#     ACTIVE
#     INACTIVE
#     COLOURED
#     CREATE

# Minefield origins
#     OFFICIAL
#     REGULAR
#     KNOWN

import time as tm
import json

import numpy as np

from constants import *
from resources import direcs, where_coords



class Minefield(object):
    def __init__(self, settings, auto_create=True, mine_coords=None):
        self.settings = dict()
        # Store relevant settings.
        for s in ['dims', 'mines', 'per_cell', 'detection']:
            setattr(self, s, settings[s])
            self.settings[s] = settings[s]
        # Origin is assumed to be regular, which may be changed later.
        self.origin = REGULAR
        self.all_coords = [(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]
        self.mines_grid = self.mine_coords = self.completed_grid = None

        if mine_coords:
            self.generate_from_list(mine_coords)
            self.setup()
        elif auto_create:
            self.generate_rnd()
            self.setup()

    def __repr__(self):
        return "<{d[0]}x{d[1]} minefield with {} mines>".format(
            self.mines, d=self.dims)

    def __str__(self):
        return (
            "Minefield with dimensions {d[0]} x {d[1]}, "
            "{} mines and 3bv of {}.\n").format(self.mines, self.get_3bv(),
                d=self.dims) + str(self.completed_grid)

    def get_size(self):
        return self.dims[0]*self.dims[1]

    def get_nbrs(self, coord, include=False):
        # Also belongs in GUI classes...
        dist = self.detection
        d = dist if dist % 1 == 0 else int(dist) + 1
        x, y = coord
        row = [u for u in range(x-d, x+1+d) if u in range(self.dims[0])]
        col = [v for v in range(y-d, y+1+d) if v in range(self.dims[1])]
        # Extra feature removed.
        if dist % 1 == 0:
            nbrs = {(u, v) for u in row for v in col}
        if not include:
            #The given coord is not included.
            nbrs.remove(coord)
        return nbrs

    def generate_from_list(self, coords):
        self.origin = KNOWN
        self.mine_coords = list(set(coords)) #per_cell=1
        self.mines = len(self.mine_coords)
        # Create empty numpy array of integers to represent mine positions.
        self.mines_grid = np.zeros(self.dims, int)
        # Use the list to fill the array representing mine positions.
        # May not be the quickest way...
        for coord in set(self.mine_coords):
            self.mines_grid.itemset(coord, 1)
        # self.per_cell = max(self.per_cell, self.mines_grid.max())

    def generate_rnd(self, open_coord=None):
        # Get cells to be left free if first_success is True.
        if open_coord:
            opening_coords = self.get_nbrs(open_coord, include=True)
            avble_coords = list(set(self.all_coords) - opening_coords)
        else:
            avble_coords = self.all_coords[:]
        # Can't give opening on first click if too many mines, so compensate
        # by giving a safe click.
        if len(avble_coords) < self.mines/self.per_cell + 1:
            avble_coords = list(set(self.all_coords) - {open_coord})
        np.random.shuffle(avble_coords)
        # Create empty numpy array of integers to represent mine positions.
        self.mines_grid = np.zeros(self.dims, int)
        # Assign a one to the mines_grid where the mines should be.
        for i in range(self.mines):
            self.mines_grid.itemset(avble_coords[i], 1)
        self.mine_coords = where_coords(self.mines_grid)

    def setup(self):
        self.get_completed_grid()
        self.get_openings()
        self.get_3bv()

    def get_completed_grid(self):
        self.completed_grid = MINE * self.mines_grid.copy()
        for coord in where_coords(self.mines_grid==0):
            nbrs = self.get_nbrs(coord)
            self.completed_grid.itemset(coord,
                sum(map(lambda k: self.mines_grid[k], nbrs)))

    def get_openings(self):
        opening_coords = set(map(tuple,
            np.transpose(np.nonzero(self.completed_grid==0))))
        check = set()
        found = set()
        openings = []
        while len(opening_coords.difference(found)) > 0:
            opening = set()
            check.add(list(opening_coords.difference(found))[0])
            while len(check) > 0:
                found.update(check) #Same as |= (below)
                coord = check.pop()
                opening.add(coord)
                opening |= self.get_nbrs(coord)
                check |= self.get_nbrs(coord) & (opening_coords - found)
            openings.append(opening)
        self.openings = openings

    def get_3bv(self):
        clicks = len(self.openings)
        exposed = len({c for opening in self.openings for c in opening})
        clicks += self.get_size() - len(set(self.mine_coords)) - exposed
        self.bbbv = clicks
        return self.bbbv

    # Check this out at some point..
    def change_settings(self, new_settings, generate):
        for s in ['dims', 'mines', 'per_cell', 'detection', 'distance_to']:
            setattr(self, s, new_settings[s])
            self.settings[s] = new_settings[s]
        if generate and not self.origin:
            self.generate() #In case first_success was changed
        else:
            self.setup()


class Game(object):
    def __init__(self, settings, minefield=None):
        if type(minefield) is Minefield:
            self.mf = minefield
            # As the minefield is passed in it is known.
            self.mf.origin = KNOWN
        elif type(minefield) is list:
            # If a list is given assume it's a list of mine coordinates.
            try:
                self.mf = Minefield(settings, minefield)
            except:
                # Catch any error that this generous assumption causes.
                pass
        else:
            # No need to generate board yet if first_success is True.
            auto_create = not settings['first_success']
            # Create a new minefield.
            self.mf = Minefield(settings, auto_create)

        # Settings may have changed if there is a discrepancy.
        self.settings = self.mf.settings
        for s in settings:
            setattr(self, s, settings[s])

        self.grid = UNCLICKED * np.ones(self.dims, int)
        self.state = READY
        self.start_time, self.finish_time = None, None
        self.left_clicks, self.right_clicks = dict(), dict()
        self.both_clicks = dict()

    def __repr__(self):
        return "<Game object%s>" % (", started at %s" % tm.strftime(
            '%H:%M, %d %b %Y', tm.localtime(self.start_time))
            if self.start_time else "")

    def __str__(self):
        ret = "Game with " + str(self.mf).lower()
        if self.start_time:
            ret += " Started at %s." % tm.strftime('%H:%M, %d %b %Y', tm.localtime(self.start_time))
        return ret

    def get_time_passed(self):
        """Return the time that has passed since the game was started."""
        if not self.start_time:
            return None
        elif self.finish_time:
            return self.finish_time - self.start_time
        else:
            return tm.time() - self.start_time

    def get_rem_3bv(self):
        """Calculate the minimum remaining number of clicks needed to solve."""
        if self.state == WON:
            return 0
        elif self.state == READY:
            return self.mf.bbbv
        else:
            t = tm.time()
            lost_mf = Minefield(self.settings, auto_create=False)
            lost_mf.mine_coords = self.game.minefield.mine_coords
            # Replace any openings already found with normal clicks (ones).
            lost_mf.completed_grid = np.where(self.game.grid<0,
                self.game.minefield.completed_grid, 1)
            # Find the openings which remain.
            lost_mf.get_openings()
            rem_opening_coords = [c for opening in lost_mf.openings
                for c in opening]
            # Count the number of essential clicks that have already been
            # done by counting clicked cells minus the ones at the edge of
            # an undiscovered opening.
            completed_3bv = len({c for c in where_coords(self.grid >= 0)
                if c not in rem_opening_coords})
            print "Calculating remaining 3bv took {:.2f}s.".format(
                tm.time() - t)
            return lost_mf.get_3bv() - completed_3bv

    def get_prop_complete(self):
        """Calculate the progress of solving the board using 3bv."""
        float(self.mf.bbbv - self.get_rem_3bv())/self.mf.bbbv

    def get_3bvps(self):
        """Return the 3bv/s."""
        if self.start_time:
            return self.get_prop_complete()/self.get_time_passed()

    def get_prop_flagged(self):
        """Calculate the proportion of mines which are being flagged."""



if __name__ == '__main__':
    pass