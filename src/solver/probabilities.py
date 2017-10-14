

from math import log, exp, factorial as fac
import time as tm

from utils import prettify_grid, get_nbrs
from gen_probs import prob as get_unsafe_prob, combs as get_combs


class ProbsGrid(list):
    def __init__(self, board, ignore_flags=False, **settings):
        super().__init__()
        self.x_size, self.y_size = len(board[0]), len(board)
        for j in range(self.y_size):
            row = self.x_size*[0]
            self.append(row)
        self.all_coords = [(x, y) for x in range(self.x_size)
                           for y in range(self.y_size)]
        if ignore_flags:
            for (x, y) in self.all_coords:
                if board[y][x][0] == 'F':
                    board[y][x] = 'U'
        self.board = board
        for attr in ['nr_mines', 'max_per_cell']:
            setattr(self, attr, settings[attr])
        self.clickable_coords = [(x, y) for (x, y) in self.all_coords
                                 if board[y][x]=='U']
        self.found_mines = sum([int(c[1]) for row in self.board for c in row
                                if str(c)[0] in ['F', 'L']])
        self.get_displayed_numbers()
        self.get_groups()
        self.get_configs()
        self.get_probs()
    def __str__(self):
        print_grid = []
        for row in self:
            print_grid.append(list(map(lambda p: round(100*p, 1), row)))
        return prettify_grid(print_grid, {0:' 0  ', 100:'100 '}, cell_size=4)
    def get_displayed_numbers(self):
        """Put the displayed numbers in a dictionary with coordinate as key,
        storing their neighbouring clickable cells."""
        self.numbers = dict()
        edge_coords = set()
        # Look through all the cells to find the revealed numbers
        for (x, y) in self.all_coords:
            contents = self.board[y][x]
            if type(contents) is str or contents == 0:
                continue
            nr = contents
            nbrs = get_nbrs(x, y, self.x_size, self.y_size)
            clickable_nbrs = []
            for (i, j) in nbrs:
                c = self.board[j][i]
                if str(c)[0] in ['F', 'L']:
                    nr -= int(c[1])
                elif str(c)[0] in ['U', 'M']:
                    # Include displayed mines for state before game was lost
                    clickable_nbrs.append((i, j))
            edge_coords.update(clickable_nbrs)
            # Check number isn't too high for the available space
            if nr > len(clickable_nbrs) * self.max_per_cell:
                msg = "Error: number {} in cell {} is too high"
                raise ValueError(msg.format(contents, (x, y)))
            clickable_nbrs.sort() # To help with debugging
            self.numbers[(x, y)] = {'nr':nr, 'nbrs':clickable_nbrs, 'groups':[]}
        # All coords that are clickable and next to a number
        self.edge_coords = sorted(list(edge_coords))
    def get_groups(self):
        """Find the equivalence groups and store in a list."""
        self.groups = []
        # Switch from a dictionary of displayed numbers with their neighbours
        #  (self.numbers) to a dictionary of unclicked cells with their
        #  neighbouring displayed numbers (nr_nbrs_of_unclicked)
        nr_nbrs_of_unclicked = dict()
        for nr_coord, nr_info in self.numbers.items():
            for clickable in nr_info['nbrs']:
                nr_nbrs_of_unclicked.setdefault(clickable, []).append(nr_coord)
                nr_nbrs_of_unclicked[clickable].sort() # for comparison
        # Convert lists to tuples which are hashable and loop once for each
        #  equivalence group. Could be sped up..?
        for nr_nbrs in set(map(tuple, nr_nbrs_of_unclicked.values())):
            # Get all coords that share the same number neighbours and are
            # therefore in an equivalence group
            coords = [c for (c, nbrs) in nr_nbrs_of_unclicked.items()
                if tuple(nbrs) == nr_nbrs]
            # Store the equivalence group referencing its coords and the shared
            # number coordinates (this is used to reference the dictionary
            # self.numbers which is created in method get_numbers)
            grp = {'coords':coords, 'nr_coords':list(nr_nbrs)}
            # Get smallest neighbouring number from self.numbers
            min_nr = min(map(lambda c: self.numbers[c]['nr'], nr_nbrs))
            # Store upper bound on number of mines that can be in the group
            grp['max'] = min(len(coords)*self.max_per_cell, min_nr)
            self.groups.append(grp)
        # Sort the groups by coordinate closest to the left, then the top
        self.groups.sort(key=lambda g: min(g['coords']))
        # Store the indices of the groups in self.numbers
        for i, g in enumerate(self.groups):
            for nr in g['nr_coords']:
                self.numbers[nr]['groups'].append(i)
    def get_configs(self):
        ttotal = t1 = t2 = t3 = 0
        ttotalstart = tm.time()
        # Initialise the list of configurations for the number of mines in each
        #  group, with the index within each configuration corresponding to the
        #  group index in self.groups. Each list in cfgs will be filled in from
        #  left to right
        cfgs = [[0]*len(self.groups)]
        # Loop through the groups/along the configurations
        for i, g in enumerate(self.groups):
            # Copy configs into temporary list to loop through, reset cfgs
            subcfgs = cfgs[:] #configurations filled in up to index i
            cfgs = []
            # For each configuration branch off with new configurations
            # after filling a number of mines for the next group.
            for cfg in subcfgs:
                g_min = 0
                g_max = g['max'] # obtained by taking min of neighbouring nrs
                t2start = tm.time()
                # Loop through the numbers next to the current group to
                # determine bounds on how many mines the group could contain
                for coord in g['nr_coords']:
                    nr = self.numbers[coord]
                    # Group indices are stored in each nr dict
                    # Get the index of the current group within the current nr
                    grp_index = nr['groups'].index(i)
                    prev_grps = nr['groups'][:grp_index]
                    next_grps = nr['groups'][grp_index+1:]
                    # The effective value of the number 'nr' after mines have
                    # been placed as in the current cfg
                    t1start = tm.time()
                    nr_val = nr['nr']
                    for j in prev_grps:
                        nr_val -= cfg[j]
                    g_max = min(g_max, nr_val)
                    space = 0
                    for j in next_grps:
                        space += self.groups[j]['max']
                    g_min = max(g_min, nr_val - space)
                    t1 += tm.time() - t1start
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
        print('{:.3f}, {:.3f}, {:.3f}. Total: {:.2f}'.format(t1, t2, t3,
                                                             ttotal))
    def get_probs(self):
        # Number of remaining clickable cells
        n = len(self.clickable_coords)
        # Number of remaining mines (subtract found mines)
        k = self.nr_mines - self.found_mines
        # Number of cells which are next to a revealed number
        S = len(self.edge_coords)
        # Probabilities associated with each configuration in self.configs
        cfg_probs = []
        for cfg in self.configs:
            # print(cfg)
            M = sum(cfg) #total mines in cfg
            if M > k: #too many mines
                cfg_probs.append(0)
                continue
            if k - M > self.max_per_cell * (n - S): #not enough outer space
                cfg_probs.append(0)
                continue
            # Initiate the number of combinations
            combs = fac(k) / fac(k - M)
            # This is the product term in xi(cfg)
            for i, m_i in enumerate(cfg):
                g_size = len(self.groups[i]['coords'])
                combs *= get_combs(g_size, m_i, self.max_per_cell)
                combs /= fac(m_i)
            cfg_probs.append(combs * get_combs(n - S, k - M, self.max_per_cell))
            # print(n, k, S, M, combs)
        # print(cfg_probs)
        weight = log(sum(cfg_probs))
        for i, p in enumerate(cfg_probs):
            if p == 0: #...why? error?
                print("Zero probability for cfg:")
                print(self.configs[i])
                continue
            cfg_probs[i] = exp(log(p) - weight)
        # print(self.configs)
        # print(cfg_probs)
        expected = 0
        for i, g in enumerate(self.groups):
            g_size = len(g['coords'])
            probs = [] #index to correspond to the number of mines in the group
            unsafe_prob = 0 #prob of a cell in the group having at least 1 mine
            # Loop through the numbers of mines that can be held by the group
            for j in range(g_size * self.max_per_cell + 1):
                p = sum([cfg_probs[k] for k, c in enumerate(self.configs)
                         if c[i]==j])
                probs.append(p)
                # print(p, get_unsafe_prob(g_size, j, self.per_cell))
                unsafe_prob += p * get_unsafe_prob(g_size, j, self.max_per_cell)
                if unsafe_prob > 1.0001:
                    print("Invalid configuration.")
                    print(self.configs)
                    print(cfg_probs)
                    print(probs)
                    return
            # Probability of the group containing 0, 1, 2,... mines, where the
            #  number corresponds to the index
            g['probs'] = tuple(probs)
            g['exp'] = 0
            for n, p in enumerate(g['probs']):
                g['exp'] += n * p
            expected += g['exp']
            for (x, y) in g['coords']:
                # Round to remove error and allow checking for round probs
                self[y][x] = round(unsafe_prob, 5)
        rem_coords = set(self.clickable_coords) - set(self.edge_coords)
        if len(rem_coords) > 0:
            outer_mines = self.nr_mines - int(expected)
            outer_prob = get_unsafe_prob(len(rem_coords), outer_mines,
                                         self.max_per_cell)
        for (x, y) in rem_coords:
            self[y][x] = outer_prob
        # self.print_info()





if __name__ == '__main__':
    test_board = [
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 2, 2, 1, 1, 2, 'F1', 3, 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 2, 'U', 1, 0, 0, 1, 3, 'F1', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 2, 1, 0, 1, 1, 4, 'F1', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 2, 0, 1, 2, 'F1', 4, 'F1', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 2, 1, 2, 'U', 3, 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'],
        ['U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U']]
    print(prettify_grid(test_board, {0:'-', 'U':'#'}))
    probs = ProbsGrid(test_board, nr_mines=70, max_per_cell=1)
    print(probs)
