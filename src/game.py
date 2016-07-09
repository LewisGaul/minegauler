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
from resources import direcs, get_neighbours, where_coords



class Minefield(object):
    def __init__(self, settings, mine_coords=None, auto_create=True):
        self.settings = dict()
        # Store relevant settings.
        for s in ['dims', 'mines', 'per_cell', 'detection']:
            setattr(self, s, settings[s])
            self.settings[s] = settings[s]
        # Create empty numpy array of integers to represent mine positions.
        self.mines_grid = np.zeros(self.dims, int)
        # Origin is assumed to be regular, which may be changed later.
        self.origin = REGULAR
        self.all_coords = [(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]

        if mine_coords:
            self.generate_from_list(mine_coords)
            self.setup()
        elif auto_create:
            self.generate_random()
            self.get_mine_coords()
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

    def generate_from_list(self, coords):
        self.origin = KNOWN
        self.mine_coords = mine_coords
        self.mines = len(mine_coords)
        # Use the list to fill the array representing mine positions.
        # May not be the quickest way...
        for coord in set(self.mine_coords):
            self.mines_grid.itemset(coord, self.mine_coords.count(coord))

    def generate_random(self, open_coord=None):
        # Get cells to be left free if first_success is True.
        opening_coords = get_neighbours(open_coord, self.dims, self.detection,
            include=True) if open_coord else set()
        avble_coords = list(set(self.all_coords) - opening_coords)
        # Can't give opening on first click if too many mines, so compensate
        # by giving a safe click.
        if len(avble_coords) < self.mines/self.per_cell + 1:
            avble_coords = list(set(self.all_coords) - {open_coord})
        np.random.shuffle(avble_coords)
        # Assign a one to the mines_grid where the mines should be.
        for i in range(self.mines):
            np.mines_grid.itemset(avble_coords[i], 1)

    def get_mine_coords(self):
        """Get a list of the coordinates of the mines using mines_grid."""
        self.mine_coords = get_nonzero_coords(self.mines_grid)
        # Include double mines in the list twice etc.
        if self.per_cell > 1:
            repeats = []
            for coord in [c for c in self.mine_coords
                if self.mines_grid.item(c) > 1]:
                repeats += [coord]*(self.mines_grid.item(coord) - 1)
            self.mine_coords += repeats
            self.mine_coords.sort()

    def setup(self):
        self.get_completed_grid()
        self.get_openings()
        self.get_3bv()

    def get_completed_grid(self):
        self.completed_grid = MINE * self.mines_grid.copy()
        for coord in np.transpose(np.nonzero(self.mines_grid==0)):
            nbrs = get_neighbours(tuple(coord), self.dims, self.detection)
            self.completed_grid.itemset(tuple(coord),
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
                opening |= get_neighbours(coord, self.dims, self.detection)
                check |= get_neighbours(coord, self.dims, self.detection) & (opening_coords - found)
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
            # If list given, assume it's a list of mine coordinates, catching
            # any error that arises.
            try:
                self.mf = Minefield(settings, minefield)
            except:
                pass
        else:
            # Create a new minefield
            self.mf = Minefield(settings)

        self.settings = settings
        for s in settings:
            setattr(self, s, settings[s])

        self.grid = UNCLICKED * np.ones(self.dims, int)
        self.state = READY

        self.start_time, self.finish_time = None, None
        self.lives_remaining = self.lives

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