


from utils import prettify_grid, get_nbrs


class ProbsGrid(list):
    def __init__(self, board, ignore_flags=False, **settings):
        super().__init__()
        self.x_size, self.y_size = len(board[0]), len(board)
        for j in range(self.y_size):
            row = self.x_size*[0]
            self.append(row)
        self.board = board
        self.ignore_flags = ignore_flags
        for attr in ['nr_mines', 'max_per_cell']:
            setattr(self, attr, settings[attr])
        self.all_coords = [(x, y) for x in range(self.x_size)
                           for y in range(self.y_size)]
        self.get_displayed_numbers()
        self.get_groups()
    def __str__(self):
        print_grid = []
        for row in self:
            print_grid.append(list(map(lambda p: round(100*p, 1), row)))
        return prettify_grid(print_grid, {0:' 0  ', 100:'100 '}, cell_size=4)
    def get_displayed_numbers(self):
        """Put the displayed numbers in a dictionary with coordinate as key,
        storing their neighbouring clickable cells."""
        self.numbers = dict()
        for (x, y) in self.all_coords:
            contents = self.board[y][x]
            if type(contents) is str or contents == 0:
                continue
            nr = contents
            nbrs = get_nbrs(x, y, self.x_size, self.y_size)
            clickable_nbrs = []
            for (i, j) in nbrs:
                c = self.board[j][i]
                if str(c)[0] == 'L':
                    nr -= int(c[1])
                elif str(c)[0] == 'F':
                    if self.ignore_flags:
                        clickable_nbrs.append((i, j))
                    else:
                        nr -= int(c[1])
                elif type(c) is str:
                    # Include displayed mines for state before game was lost
                    clickable_nbrs.append((i, j))
            if nr > len(clickable_nbrs) * self.max_per_cell:
                msg = "Error: number {} in cell {} is too high"
                raise ValueError(msg.format(contents, (x, y)))
            clickable_nbrs.sort() # To help with debugging
            self.numbers[(x, y)] = {'nr':nr, 'nbrs':clickable_nbrs, 'groups':[]}
        # # All coords that are unclicked and next to a number.
        # self.edge_coords = sorted(list(edge_coords))
    def get_groups(self):
        """Find the equivalence groups and store in a list."""
        self.groups = []
        # Switch from a dictionary of displayed numbers with their neighbours
        # (self.numbers) to a dictionary of unclicked cells with their
        # neighbouring displayed numbers (nr_nbrs_of_unclicked)
        nr_nbrs_of_unclicked = dict()
        for nr_coord, nr_info in self.numbers.items():
            for clickable in nr_info['nbrs']:
                nr_nbrs_of_unclicked.setdefault(clickable, []).append(nr_coord)
                nr_nbrs_of_unclicked[clickable].sort() # for comparison
        # Convert lists to tuples which are hashable and loop once for each
        # equivalence group. Could be sped up..?
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
        pass




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
