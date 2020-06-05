from resources import *

#Game state
LOST = -3
WON = -2
INACTIVE = -1
READY = 0
COLOURED = 1
ACTIVE = 2
CREATE = 3

#Minefield origin
OFFICIAL = -1
NORMAL = 0
KNOWN = 1


class Minefield(object):
    def __init__(self, settings, create=True):
        self.settings = dict()
        #Store relevant settings.
        for s in ['dims', 'mines', 'per_cell', 'detection', 'distance_to']:
            setattr(self, s, settings[s])
            self.settings[s] = settings[s]
        self.mines_grid = np.zeros(self.dims, int)
        if not create:
            self.origin = NORMAL
            return
        elif type(create) == list:
            self.origin = KNOWN
            self.mine_coords = create
            for coord in set(self.mine_coords):
                self.mines_grid.itemset(coord, self.mine_coords.count(coord))
            self.setup()
        else:
            self.origin = NORMAL
            self.generate()
            self.get_mine_coords()
            self.setup()


    def __repr__(self):
        return "<{d[0]}x{d[1]} minefield with {} mines>".format(
            self.mines, d=self.dims)

    def __str__(self):
        return (
            "Minefield with dimensions {d[0]} x {d[1]}, "
            "{} mines and 3bv of {}.\n").format(self.mines, self.bbbv,
                d=self.dims) + str(self.completed_grid)

    def generate(self, open_coord=None):
        # Get cells to be left free if first_success is True.
        opening_coords = get_neighbours(open_coord, self.dims, self.detection,
            include=True) if open_coord else set()
        available_coords = list(set([(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]) - opening_coords)
        # Can't give opening on first click if too many mines.
        if len(available_coords) < self.mines/self.per_cell + 1:
            available_coords = list(set([(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]) - {open_coord})
        if self.per_cell == 1:
            # This is quicker? (check) Only works for one per cell.
            permute = np.ones(self.mines, int)
            permute.resize(self.dims[0]*self.dims[1]) # Adds zeros
            self.mines_grid = np.random.permutation(permute).reshape(self.dims)
            for c in opening_coords:
                self.mines_grid.itemset(c, 0)
        while self.mines_grid.sum() < self.mines:
            replace = True if self.per_cell > 1 else False
            coord_indices = list(np.random.choice(
                np.array(range(len(available_coords))),
                    size=self.mines - self.mines_grid.sum(), replace=replace))
            for i in set(coord_indices):
                coord = available_coords[i]
                self.mines_grid.itemset(coord, min(self.per_cell,
                    self.mines_grid.item(coord) + coord_indices.count(i)))

    def get_mine_coords(self):
        """Get a list of the coordinates of the mines."""
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
        self.completed_grid = -10 * self.mines_grid.copy()
        if self.distance_to:
            pass
        else:
            for coord in np.transpose(np.nonzero(self.mines_grid==0)):
                self.completed_grid.itemset(tuple(coord),
                    sum(map(lambda k: self.mines_grid[k],
                        get_neighbours(tuple(coord), self.dims, self.detection))))

    def get_openings(self):
        if self.distance_to:
            opening_coords = set(map(tuple,
                np.transpose(np.nonzero(self.final_grid>0))))
        else:
            opening_coords = set(map(tuple,
                np.transpose(np.nonzero(self.completed_grid==0))))
        if self.distance_to:
            pass
        else:
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
        clicks += self.dims[0]*self.dims[1] - len(set(self.mine_coords)) - exposed
        self.bbbv = clicks

    def change_settings(self, new_settings, generate):
        for s in ['dims', 'mines', 'per_cell', 'detection', 'distance_to']:
            setattr(self, s, new_settings[s])
            self.settings[s] = new_settings[s]
        if generate and not self.origin:
            self.generate() #In case first_success was changed
        else:
            self.setup()


class Game(object):
    def __init__(self, settings, field=None):
        if type(field) is Minefield:
            self.minefield = field
            self.minefield.origin = KNOWN # Repeat... needed?
        elif not field:
            self.minefield = Minefield(settings, False)
        else:
            self.minefield = Minefield(settings)
        self.settings = settings
        for s in settings:
            setattr(self, s, settings[s])

        self.grid = -BIG * np.ones(self.dims, int)
        self.state = READY

        self.start_time, self.finish_time = None, None
        self.time_passed, self.bbbv_s = None, None
        self.prop_complete, self.rem_3bv = None, None
        self.flagging = None
        self.lives_remaining = self.lives

        self.left_clicks, self.right_clicks = dict(), dict()
        self.both_clicks = dict()

    def __repr__(self):
        return "<Game object%s>" % (", started at %s" % tm.strftime(
            '%H:%M, %d %b %Y', tm.localtime(self.start_time))
            if self.start_time else "")

    def __str__(self):
        ret = "Game with " + str(self.minefield).lower()
        if self.start_time:
            ret += " Started at %s." % tm.strftime('%H:%M, %d %b %Y', tm.localtime(self.start_time))
        return ret

    def change_settings(self, new_settings):
        for k, v in new_settings.items():
            setattr(self, k, v)
            self.settings[k] = v
        self.minefield.change_settings(new_settings,
            generate=not(bool(self.first_success)))

    def serialize(self, path):
        if not hasattr(self.minefield, 'mine_coords'):
            grid = (self.grid!=-BIG) * (self.grid<0)
            self.minefield.mines_grid = np.where(grid, -self.grid/10, 0)
            self.minefield.get_mine_coords()
            # self.minefield.setup()
        obj = {
            'name':         self.name,
            'coords':       self.minefield.mine_coords}
        for attr in ['diff', 'dims', 'mines', 'first_success', 'lives',
            'per_cell', 'detection', 'drag_select', 'distance_to', 'flagging',
            'lives_remaining', 'button_size', 'left_clicks', 'right_clicks',
            'both_clicks']:
            obj[attr] = getattr(self, attr)
        if self.state in [WON, LOST]:
            obj.update({
                'time':         '%.2f' % (self.time_passed+0.01),
                '3bv':          self.minefield.bbbv,
                '3bv/s':        '%.2f' % self.bbbv_s,
                'date':         self.finish_time,
                'proportion':   round(self.prop_complete, 4)})
            obj['key'] = encode_highscore(obj)
        print "Saved board to\n" + path
        with open(path, 'w') as f:
            json.dump(obj, f)

    @staticmethod
    def deserialize(obj):
        # if encode_highscore(obj) != obj['key']:
        #     return
        settings = dict()
        for s in ['diff', 'dims', 'mines', 'first_success', 'lives',
            'per_cell', 'detection', 'drag_select', 'distance_to',
            'button_size']:
            settings[s] = obj[s]
        coords = map(tuple, obj['coords'])
        field = Minefield(settings, coords)
        game = Game(settings, field)
        # So far only retrieves the board and settings.
        # for s in ['left_clicks', 'right_clicks', 'both_clicks']:
        #     setattr(game, s, obj[s])
        return game



if __name__ == '__main__':
    pass