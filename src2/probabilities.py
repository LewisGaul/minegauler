# =====================
# Improvements
# ---------------------
# ---------------------

# Button states are:
#     UNCLICKED
#     CLICKED
#     FLAGGED
#     MINE

# Drag-and-select flagging types are:
#     FLAG
#     UNFLAG
#     REFRESH

import Tkinter as tk
from PIL import Image as PILImage, ImageTk
from math import log, exp, factorial as fac
import time as tm

import numpy as np

from constants import *
from utils import direcs, get_nbrs, blend_colours
from gui import CreateGui
from gen_probs import prob as get_unsafe_prob, combs as get_combs

__version__ = VERSION

default_settings = {
    'diff': 'c',
    'dims': (10, 10),
    'mines': 20,
    'per_cell': 1,
    'detection': 1,
    'drag_select': False,
    'btn_size': 25, #pixels
    'styles': {
        'buttons': 'standard',
        'numbers': 'standard',
        'images': 'standard'
        }
}


class ProbGui(CreateGui):
    def __init__(self, **kwargs):
        # Defaults which may be overwritten below.
        settings = default_settings.copy()
        # Overwrite with any given settings.
        for s, val in kwargs.items():
            settings[s] = val
        super(ProbGui, self).__init__(default_btn_size=25, **settings)
        self.title('Probability Calculator')
        self.cfg = None
        self.set_mines_counter()

    def __repr__(self):
        return "<Probability GUI>".format()

    def make_menubar(self):
        super(ProbGui, self).make_menubar()
        menu = self.menubar
        per_cell_menu = tk.Menu(menu)
        menu.add_item('options', 'cascade', 'Per cell', menu=per_cell_menu)
        self.per_cell_var = tk.IntVar()
        self.per_cell_var.set(self.per_cell)
        for i in range(1, 4):
            per_cell_menu.add_radiobutton(label=i, variable=self.per_cell_var,
                value=i, command=lambda: setattr(
                    self, 'per_cell', self.per_cell_var.get()))

    def make_panel(self):
        super(ProbGui, self).make_panel()
        # Create and place the mines counter.
        self.mines_var = tk.StringVar()
        self.mines_label = tk.Label(self.panel, bg='black', fg='red', bd=5,
            relief='sunken', font=('Verdana',11,'bold'),
            textvariable=self.mines_var)
        self.mines_label.grid(row=0, padx=(6, 0))
        self.add_to_bindtags(self.mines_label, 'panel')

    def left_release(self, coord):
        super(ProbGui, self).left_release(coord)
        if self.drag_select:
            self.show_probs()

    def right_press(self, coord):
        super(ProbGui, self).right_press(coord)
        self.set_mines_counter()
        if not self.drag_select:
            self.show_probs()

    def right_release(self, coord):
        super(ProbGui, self).right_release(coord)
        if self.drag_select:
            self.show_probs()

    def right_motion(self, coord, prev_coord):
        super(ProbGui, self).right_motion(coord, prev_coord)
        self.set_mines_counter()

    def click(self, coord):
        b = self.buttons[coord]
        if b.nr == min(18, 8*self.per_cell):
            return
        elif b.nr is None:
            b.nr = 0
            b.state = CLICKED
        else:
            b.nr += 1
        self.board.delete(b.fg)
        b.fg = self.set_cell_image(coord, self.btn_images[b.nr])
        if not self.left_btn_down:
            self.show_probs()

    def set_mines_counter(self):
        nr_found = sum([b.mines for b in self.buttons.values()])
        nr_rem = self.mines - nr_found
        self.mines_var.set('{:03d}'.format(abs(nr_rem)))
        if nr_rem < 0:
            self.mines_label.config(bg='red', fg='black')
        else:
            self.mines_label.config(bg='black', fg='red')

    def show_probs(self):
        # First reset buttons
        for b in self.buttons.values():
            if b.state == UNCLICKED:
                b.refresh()
            else:
                b.prob_mine = None
        self.cfg = NrConfig(self.buttons, self.mines, self.per_cell)
        # print self.cfg
        # self.cfg.print_info()
        probs = self.cfg.probs
        for coord in self.cfg.edge_coords:
            b = self.buttons[coord]
            p = probs[coord]
            if p is not None:
                if p in [0, 1]:
                    text = int(p)
                else:
                    text = "{:.2f}".format(round(p, 2))
            density = float(self.mines) / self.get_size()
            if p >= density:
                ratio = (p - density) / (1 - density)
                colour = blend_colours(ratio)
            else:
                ratio = (density - p) / density
                colour = blend_colours(ratio, high_colour=(0, 255, 0))
            y0, x0 = ((i + 1.0/16) * self.btn_size for i in coord)
            y1, x1 = ((i + 15.0/16) * self.btn_size for i in coord)
            b.prob_fg = self.board.create_rectangle(x0, y0, x1, y1, width=0,
                fill=colour, tag='overlay')
            b.text = self.board.create_text((x0 + x1)/2, (y0 + y1)/2 - 1,
                font=('Times', int(0.2*self.btn_size + 3.5), 'normal'),
                text=text, tag='overlay')

    def refresh_board(self, event=None):
        super(ProbGui, self).refresh_board()
        self.is_coloured = False
        n = min(3, self.lives)
        self.face_button.config(image=self.face_images['ready%s'%n])
        self.set_mines_counter()



class NrConfig(object):
    def __init__(self, grid, mines, per_cell=1, ignore_flags=False):
        """The grid is a dictionary containing Cell objects."""
        self.grid = grid
        self.dims = tuple(i + 1 for i in max(grid)) #biggest key
        self.size = self.dims[0] * self.dims[1]
        self.per_cell = per_cell
        if ignore_flags:
            self.flag_coords = [c for c in grid if self.grid[c].state == MINE]
            self.unclicked_coords = [c for c in grid
                if grid[c].state in [UNCLICKED, FLAGGED]]
        else:
            self.flag_coords = [c for c in grid if self.grid[c].mines]
            self.unclicked_coords = [c for c in grid
                if grid[c].state == UNCLICKED]
        self.mines = mines
        self.flags = sum([grid[c].mines for c in self.flag_coords])
        self.density = float(self.mines) / self.size
        self.edge_coords = []
        self.numbers = dict()
        self.groups = []
        self.configs = []
        self.probs = dict()
        self.get_numbers()
        self.get_groups()
        if self.groups:
            t = tm.time()
            self.get_configs()
            elapsed = tm.time() - t
            if elapsed > 0.1:
                print "Getting configs took {:.2f}s.".format(elapsed)
            # print self.configs
            self.get_probs()
        else:
            for coord in self.grid:
                self.probs[coord] = get_unsafe_prob(self.size, self.mines,
                    self.per_cell)

    def __repr__(self):
        return "<Board with {} groups>".format(len(self.groups))

    def get_numbers(self):
        """Put the displayed numbers in a dictionary with coordinate as key."""
        edge_coords = set()
        nr_coords = [c for c in self.grid if self.grid[c].nr]
        for coord in nr_coords:
            nr = self.grid[coord].nr
            nbrs = get_nbrs(coord, self.dims)
            # Adjust to number of remaining neighbours that could contain mines.
            nr -= len(set(self.flag_coords) & nbrs)
            empty_nbrs = set(self.unclicked_coords) & nbrs
            # Coords next to a number. The need for this should be removed..?
            edge_coords |= empty_nbrs
            if nr > len(empty_nbrs) * self.per_cell:
                print (self.per_cell, empty_nbrs,
                    map(lambda x: self.grid[x].state, nbrs))
                raise ValueError(
                    "Error: number {} in cell {} is too high.".format(nr, coord))
            self.numbers[coord] = {'nr':nr, 'nbrs':empty_nbrs, 'groups':[]}
        # All coords that are unclicked and next to a number.
        self.edge_coords = sorted(list(edge_coords))

    def get_groups(self):
        """Find the equivalence groups and store in a list."""
        space_nr_nbrs = dict()
        for nr_coord, nr_info in self.numbers.items():
            for space_coord in nr_info.pop('nbrs'):
                space_nr_nbrs.setdefault(space_coord, []).append(nr_coord)
                space_nr_nbrs[space_coord].sort() #allow for comparison
        # Convert lists to tuples which are hashable and loop once for each
        # equivalence group. Could be sped up..?
        for nr_nbrs in set(map(tuple, space_nr_nbrs.values())):
            # Get all coords that share the same number neighbours and are
            # therefore in an equivalence group.
            coords = [sp for (sp, nbrs) in space_nr_nbrs.items()
                if tuple(nbrs) == nr_nbrs]
            # Store the equivalence group referencing its coords and the shared
            # number coordinates (this is used to reference the dictionary
            # self.numbers which is defined in method get_numbers).
            grp = {'coords':coords, 'nrs':nr_nbrs}
            min_nr = min(map(lambda c: self.numbers[c]['nr'], nr_nbrs))
            grp['max'] = min(len(coords)*self.per_cell, min_nr)
            self.groups.append(grp)
        # Sort the groups by coordinate (top, left). Could be improved...
        self.groups.sort(key=lambda g: min(g['coords']))
        # Store the indices of the groups which neighbour each number.
        for i, g in enumerate(self.groups):
            for nr in g['nrs']:
                self.numbers[nr]['groups'].append(i)

    def get_configs(self):
        ttotal = t1 = t2 = t3 = 0
        ttotalstart = tm.time()
        # Initialise the list of configurations for the number of mines in each
        # group, with the index within each configuration corresponding to the
        # group index in self.groups.
        cfgs = [[0]*len(self.groups)]
        # Loop through the groups/along the configurations.
        for i, g in enumerate(self.groups):
            t1start = tm.time()
            subcfgs = cfgs[:] #configurations filled in up to index i
            t1 += tm.time() - t1start
            cfgs = []
            # For each configuration branch off with new configurations
            # after filling a number of mines for the next group.
            for cfg in subcfgs:
                g_min = 0
                g_max = g['max'] #obtained by taking min of neighbouring nrs
                # new_nrs = [n.copy() for n in nrs]
                t2start = tm.time()
                for index in g['nrs']:
                    nr = self.numbers[index]
                    # Group indices are stored in each nr dict. Get the index of
                    # the current group within the current nr.
                    grp_index = nr['groups'].index(i)
                    prev_grps = nr['groups'][:grp_index]
                    next_grps = nr['groups'][grp_index+1:]
                    # The effective value of the number 'nr', after mines have
                    # been placed in the current cfg.
                    new_nr = (nr['nr'] -
                        reduce(lambda x, j: x + cfg[j], prev_grps, 0))
                    g_max = min(g_max, new_nr)
                    space = reduce(lambda x, y: x + self.groups[y]['max'],
                        next_grps, 0)
                    g_min = max(g_min, new_nr - space)
                t2 += tm.time() - t2start
                t3start = tm.time()
                for j in range(g_min, g_max + 1):
                    new_cfg = cfg[:]
                    new_cfg[i] = j
                    cfgs.append(new_cfg)
                t3 += tm.time() - t3start
            # print len(g['coords']), cfgs
        self.configs = sorted(map(tuple, cfgs))
        ttotal += tm.time() - ttotalstart
        print '{:.2f}, {:.2f}, {:.2f}. Total: {:.2f}'.format(t1, t2, t3, ttotal)
        self.get_configs2()

    def get_configs2(self):
        ttotal = t1 = t2 = t3 = 0
        ttotalstart = tm.time()
        # Initialise the list of configurations for the number of mines in each
        # group, with the index within each configuration corresponding to the
        # group index in self.groups.
        cfgs = [[0 for i in self.groups]]
        # Loop through the groups/along the configurations.
        for i, g in enumerate(self.groups):
            nbr_grps = set() #groups with smaller index that affect group g
            t1start = tm.time()
            for index in g['nrs']:
                nr = self.numbers[index]
                # Group indices are stored in each nr dict. Get the index of
                # the current group within the current nr.
                grp_index = nr['groups'].index(i)
                nbr_grps |= set(nr['groups'][:grp_index])
            nbr_grps = sorted(list(nbr_grps))
            # g['nbr_grps'] = nbr_grps
            # print i, len(g['coords']), nbr_grps
            # The unique values in the relevant groups of all cfgs.
            relvnt_slices = []
            mins = dict()
            maxs = dict()
            cfgs_copy = cfgs[:] #can be removed for speed optimisation
            t1 += tm.time() - t1start
            cfgs = []
            for cfg in cfgs_copy:
                t2start = tm.time()
                cfg_slice = tuple(cfg[j] for j in nbr_grps) #taking time
                if cfg not in relvnt_slices:
                    relvnt_slices.append(cfg_slice)
                    # print cfg_slice
                    g_min, g_max = 0, g['max']
                    for index in g['nrs']:
                        nr = self.numbers[index]
                        # Group indices are stored in each nr dict. Get the
                        # index of the current group within the current nr.
                        grp_index = nr['groups'].index(i)
                        prev_grps = nr['groups'][:grp_index]
                        next_grps = nr['groups'][grp_index+1:]
                        new_nr = nr['nr']
                        for j in prev_grps:
                            new_nr -= cfg_slice[nbr_grps.index(j)]
                        g_max = min(g_max, new_nr)
                        space = 0
                        for j in next_grps:
                            space += self.groups[j]['max']
                        g_min = max(g_min, new_nr - space)
                    mins[cfg_slice] = g_min
                    maxs[cfg_slice] = g_max
                    # print g_min, g_max
                t2 += tm.time() - t2start
                t3start = tm.time()
                for j in range(mins[cfg_slice], maxs[cfg_slice] + 1):
                    new_cfg = cfg[:]
                    new_cfg[i] = j
                    cfgs.append(new_cfg)
                # print cfgs
                t3 += tm.time() - t3start
            # print cfgs, len(g['coords'])
        self.configs2 = sorted(map(tuple, cfgs))
        ttotal += tm.time() - ttotalstart
        if self.configs != self.configs2:
            print 'UHOHOHOH'
            print self.configs
            print self.configs2
        print '{:.2f}, {:.2f}, {:.2f}. Total: {:.2f}'.format(t1, t2, t3, ttotal)

    def get_probs(self):
        # Number of remaining unclicked cells.
        n = len(self.unclicked_coords)
        # Number of remaining mines.
        k = self.mines - self.flags
        # Number of cells which are next to a revealed number.
        S = len(self.edge_coords)
        # Probabilities associated with each configuration in self.configs.
        cfg_probs = []
        for cfg in self.configs:
            # print cfg
            # Total mines in cfg.
            M = sum(cfg)
            if M > k: #too many mines
                cfg_probs.append(0)
                continue
            # Initiate the number of combinations.
            combs = fac(k) / fac(k - M)
            # This is the product term in xi(cfg).
            for i, m_i in enumerate(cfg):
                g_size = len(self.groups[i]['coords'])
                combs *= get_combs(g_size, m_i, self.per_cell)
                combs /= fac(m_i)
            if k - M > self.per_cell * (n - S): #not enough outer space
                cfg_probs.append(0)
                continue
            cfg_probs.append(combs * get_combs(n - S, k - M, self.per_cell))
            # print n, k, S, M, combs
        # print cfg_probs
        weight = log(sum(cfg_probs))
        for i, p in enumerate(cfg_probs):
            if p == 0:
                print "Zero probability for cfg:"
                print self.configs[i]
                continue
            cfg_probs[i] = exp(log(p) - weight)
        # print self.configs
        # print cfg_probs
        expected = 0
        unsafe_probs = dict()
        for i, g in enumerate(self.groups):
            g_size = len(g['coords'])
            probs = []
            unsafe_prob = 0
            for j in range(g_size * self.per_cell + 1):
                probs.append(sum(
                    [cfg_probs[k] for k, c in enumerate(self.configs)
                     if c[i]==j]))
                # print probs[j], get_unsafe_prob(g_size, j, self.per_cell)
                unsafe_prob += probs[j] * get_unsafe_prob(g_size, j, self.per_cell)
                if unsafe_prob > 1.0001:
                    print "Invalid configuration."
                    print self.configs
                    print cfg_probs
                    print probs
                    return
            # Probability of the group containing 0, 1, 2,... mines, where the
            # number corresponds to the index.
            g['probs'] = tuple(probs)
            g['exp'] = reduce(
                lambda n, x: n + x[0]*x[1], enumerate(g['probs']), 0)
            expected += g['exp']
            for coord in g['coords']:
                # Avoid rounding errors.
                unsafe_probs[coord] = round(unsafe_prob, 5)
        rem_coords = set(self.unclicked_coords) - set(self.edge_coords)
        if rem_coords:
            outer = get_unsafe_prob(len(rem_coords), self.mines - int(expected),
                self.per_cell)
        for coord in rem_coords:
            unsafe_probs[coord] = outer
        self.probs = unsafe_probs
        # for c, b in sorted(self.grid.items()):
        #     print c, b.prob_mine

        # self.print_info()

    def print_info(self):
        # print "\n%d number group(s):"%len(self.numbers)
        # for n in self.numbers.values():
        #     print n

        print "\n%d equivalence group(s):"%len(self.groups)
        for g in self.groups:
            print g

        print "\n%d mine configuration(s):"%len(self.configs)
        for c in self.configs:
            print c#, c.prob

        # print "\n", self, self.expected



if __name__ == '__main__':
    gui = ProbGui(dims=(10, 10), btn_size=25)
    gui.mainloop()
    # c = NrConfig(gui.grid)
    # nrs = c.numbers
    # grps = c.groups
##    cfgs = c.configs


    if 0:
        subcfgs = [len(self.groups)*[0]]
        while subcfgs:
            cfg = subcfgs.pop()
            # Default, overwritten below.
            keep_cfg = True
            for i, g in enumerate(grps):
                new_max = g['max'] - cfg[i]
                for coord in g['nrs']:
                    nr = self.numbers[coord]
                    new_nr = (nr['nr'] -
                        reduce(lambda x, j: x + cfg[j], nr['groups'], 0))
                    new_max = min(new_max, new_nr)
                # If more mines can be placed carry on.
                if new_max > 0:
                    keep_cfg = False
                    new_cfg = cfg[:]
                    new_cfg[i] += 1
                    subcfgs.append(new_cfg)
                # Check numbers are actually satisfied.
                elif new_nr > 0:
                    keep_cfg = False
            if keep_cfg:
                self.configs.append(tuple(cfg))
        self.configs = sorted(set(self.configs))

    # for c1 in cfgs:
    #     print c1
