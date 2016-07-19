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
from utils import direcs, where_coords



class Minefield(object):
    def __init__(self, mine_coords=None, auto_create=True, **kwargs):
        self.settings = dict()
        # Store relevant settings.
        self.per_cell = self.detection = 1
        for s in ['diff', 'dims', 'mines']:
            setattr(self, s, kwargs[s])
            self.settings[s] = kwargs[s]
        # Origin is assumed to be regular - may be changed later.
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

    def serialise(self, path):
        # No need to be secure.
        obj = {'coords': self.mine_coords}
        for attr in ['diff', 'dims', 'mines']:
            obj[attr] = getattr(self, attr)
        with open(path, 'w') as f:
            json.dump(obj, f)

    @classmethod
    def deserialise(cls, path):
        with open(path, 'r') as f:
            obj = json.load(f)
        obj['dims'] = tuple(obj['dims'])
        settings = dict()
        for s in ['diff', 'dims', 'mines']:
            settings[s] = obj[s]
        # json stores tuples in list format.
        mine_coords = map(tuple, obj['coords'])
        return cls(mine_coords, **settings)



class Game(object):
    def __init__(self, **kwargs):
        # Check if a minefield is passed in.
        if 'minefield' in kwargs and type(kwargs['minefield']) is Minefield:
            self.mf = kwargs['minefield']
            self.mf.origin = KNOWN
        elif 'mine_coords' in kwargs and type(kwargs['mine_coords']) is list:
            self.mf = Minefield(**kwargs)
        else:
            if 'first_success' in kwargs:
                # No need to generate board yet if first_success is True.
                auto = not kwargs['first_success']
            else:
                auto = True
            # Create a new minefield.
            self.mf = Minefield(auto_create=auto, **kwargs)

        self.settings = dict()
        for s in [i for i in kwargs if i in default_settings]:
            self.settings[s] = kwargs[s]
        # Overwrite settings that may have changed if there was a discrepancy
        # with coords passed in.
        self.settings.update(self.mf.settings)
        for s in self.settings:
            setattr(self, s, self.settings[s])
        # Get defaults for any missing settings.
        for s, val in default_settings.items():
            if not hasattr(self, s):
                setattr(self, s, val)

        self.grid = UNCLICKED * np.ones(self.dims, int)
        self.state = READY
        self.start_time = self.finish_time = None

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
            return (self.mf.get_3bv() * self.get_prop_complete() / self.get_time_passed())

    def get_prop_flagged(self):
        """Calculate the proportion of mines which are being flagged."""




if __name__ == '__main__':
    pass