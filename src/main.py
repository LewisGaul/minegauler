"""
Entry point for playing the game.

The following character representations are used:
    'U' - unclicked
    'F' - flag
    'M' - mine
    '!' - hit mine (game over)
    'L' - life lost (mine hit but not game over)
    'X' - incorrect flag
"""

import sys
import time as tm

from minefield import Minefield
from cli import GameCLI
from gui import GameGUI
from utils import get_nbrs, prettify_grid, diff_settings
# from solver import ProbsGrid


# Import settings here.
imported_settings = {}
default_settings = {
    'x_size': 8,
    'y_size': 8,
    'nr_mines': 10,
    'first_success': True,
    'max_per_cell': 1,
    # 'detection': 1,    # Implement later
    # 'drag_select': False,     # Belongs in game_gui
    # 'btn_size': 16, #pixels   # ...and this too
    # 'name': '',               # Ignore for now
    # 'styles': {               # Also belongs in game_gui
    #     'buttons': 'standard',
    #     'numbers': 'standard',
    #     'images': 'standard'
    #     }
    }


# GameUI = GameCLI         # [Determine which UI to use with argv]
GameUI = GameGUI

class Processor:
    def __init__(self, **settings):
        self.settings = dict()
        for attr in ['x_size', 'y_size', 'nr_mines', 'first_success',
                     'max_per_cell']:
            setattr(self, attr, settings[attr])
            self.settings[attr] = settings[attr]
        self.nr_flags = 0
        for d in diff_settings:
            if diff_settings[d] == (self.x_size, self.y_size, self.nr_mines):
                self.diff = d
                break
        else:
            self.diff = 'c'
        self.ui = GameUI(self)
        self.prepare_new_game()
        self.ui.start()
    def update_settings(self):
        for attr in self.settings:
            self.settings[attr] = getattr(self, attr)
    def change_difficulty(self, diff, x_size=None, y_size=None, nr_mines=None):
        """Change difficulty, creating a new game with new settings. Arguments
        x_size, y_size, nr_mines are ignored unless diff=='c'."""
        if diff == 'c':
            for d in diff_settings:
                if diff_settings[d] == (x_size, y_size, nr_mines):
                    self.change_difficulty(d)
                    return
            self.x_size, self.y_size = x_size, y_size
            self.nr_mines = nr_mines
            self.diff = 'c'
        elif diff in diff_settings:
            self.x_size, self.y_size, self.nr_mines = diff_settings[diff]
            self.diff = diff
        else:
            raise ValueError('Invalid difficulty character, {}.'.format(diff))
        self.update_settings()
        self.prepare_new_game()
    def prepare_new_game(self):
        self.game = Game(**self.settings)
        self.nr_flags = 0
        self.ui.prepare_new_game()
    def click(self, x, y, check_for_win=True):
        if self.game.board[y][x] != 'U':
            return
        if self.game.state == Game.READY:
            safe_coords = (get_nbrs(x, y, self.x_size, self.y_size)
                           if self.first_success else [])
            self.game.create_minefield(safe_coords)
            self.game.state = Game.ACTIVE
            self.game.start_time = tm.time()
            self.ui.start_game()
        cell = self.game.mf.completed_board[y][x]
        if type(cell) is str:   # Mine hit, game over
            self.game.board[y][x] = '!' + str(self.game.mf[y][x])
            # self.ui.reveal_cell(x, y)
            self.finalise_loss()
            return      # No need to check for win
        elif cell == 0:         # Opening hit
            for opening in self.game.mf.openings:
                if (x, y) in opening:
                    break # Work with this set of coords
            for (x, y) in opening:
                if self.game.board[y][x] == 'U':
                    self.game.board[y][x] = self.game.mf.completed_board[y][x]
                    self.ui.reveal_cell(x, y)
        else:                   # Number revealed
            self.game.board[y][x] = self.game.mf.completed_board[y][x]
            self.ui.reveal_cell(x, y)
        if check_for_win and self.check_is_game_won():
            self.finalise_win()
    def toggle_flag(self, x, y):
        """The given cell must either be unclicked or flagged (otherwise it is
        unclickable)."""
        val = self.game.board[y][x]
        if val == 'U':
            self.game.board[y][x] = 'F1'
            self.nr_flags += 1
            self.ui.flag(x, y, 1)
        elif val == 'F' + str(self.max_per_cell):
            self.game.board[y][x] = 'U'
            self.nr_flags -= self.max_per_cell
            self.ui.unflag(x, y)
        else:
            flags = int(val[1]) + 1
            self.game.board[y][x] = 'F' + str(flags)
            self.nr_flags += 1
            self.ui.flag(x, y, flags)
    def chord(self, x, y):
        """Receive an attempt to chord at (x, y). If the number of flags is
        correct, return True and send the required signals to the UI, otherwise
        return False."""
        state = self.game.board[y][x]
        if type(state) is not int:
            return False
        nbrs = get_nbrs(x, y, self.x_size, self.y_size)
        nbr_flags = sum([int(self.game.board[j][i][1]) for (i, j) in nbrs
                         if str(self.game.board[j][i])[0] in ['F', 'L']])
        if nbr_flags == state:
            for (i, j) in nbrs:
                if self.game.board[j][i] == 'U':
                    self.click(i, j, check_for_win=False)
                    if self.check_is_game_won():
                        self.finalise_win()
                    # self.ui.reveal_cell(i, j)
            return True
        else:
            return False
    def check_is_game_won(self):
        for (x, y) in self.game.mf.all_coords:
            if self.game.board[y][x] == 'U' and self.game.mf[y][x] == 0:
                return False
        return True
    def finalise_loss(self):
        self.game.state = Game.LOST
        self.game.finalise()
        for (x, y) in self.game.mf.all_coords:
            board_cell = self.game.board[y][x]
            mines = self.game.mf[y][x]
            if mines > 0 and board_cell == 'U':
                self.game.board[y][x] = 'M' + str(mines)
            elif (str(board_cell)[0] == 'F'
                  and board_cell != self.game.mf.completed_board[y][x]):
                self.game.board[y][x] = 'X' + board_cell[1]
        # print(prettify_grid(self.game.board))
        self.ui.finalise_loss()
    def finalise_win(self):
        self.game.state = Game.WON
        self.game.finalise()
        for (x, y) in self.game.mf.all_coords:
            mines = self.game.mf[y][x]
            if mines > 0 and self.game.board[y][x][0] in ['U','F']:
                self.game.board[y][x] = 'F' + str(mines)
        self.nr_flags = self.nr_mines #all flags displayed
        self.ui.finalise_win()
    def calculate_probs(self):
        print(ProbsGrid(board, **settings))


class Game:
    """Store attributes of a game such as the minefield, the start and end time
    etc.""" ###### Needs tidying up.
    READY = 'ready'
    ACTIVE = 'active'
    LOST = 'lost'
    WON = 'won'
    def __init__(self, **settings):
        for attr in ['x_size', 'y_size', 'nr_mines', 'first_success',
                     'max_per_cell']:
            setattr(self, attr, settings[attr])
            self.settings = settings[attr]
        self.board = []
        for j in range(self.y_size):
            self.board.append(self.x_size*['U'])
        # Instantiate a new minefield
        self.mf = Minefield(self.x_size, self.y_size)
        self.state = Game.READY
    def __repr__(self):
        return "<Game object%s>" % (", started at %s" % tm.strftime(
            '%H:%M, %d %b %Y', tm.localtime(self.start_time))
            if self.start_time else "")
    def __str__(self):
        ret = "Game with " + str(self.mf).lower()
        if self.start_time:
            ret += " Started at %s." % tm.strftime('%H:%M, %d %b %Y', tm.localtime(self.start_time))
        return ret
    def print_board(self):
        replace = {0:'-', 'U':'#'}
        if self.max_per_cell == 1:
            for char in ['M', 'F', '!', 'X', 'L']:
                replace[char + '1'] = char
        print(prettify_grid(self.board, replace))
    def finalise(self):
        """Game should be either lost or won to get a finish time."""
        self.end_time = tm.time()
        self.elapsed = self.end_time - self.start_time

    def create_minefield(self, safe_coords=[]):
        self.mf.create(self.nr_mines, self.max_per_cell, safe_coords)
    def get_rem_3bv(self):
        """Calculate the minimum remaining number of clicks needed to solve."""
        if self.state == Game.WON:
            return 0
        elif self.state == Game.READY:
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
            return (self.mf.bbbv *
                self.get_prop_complete() / self.get_time_passed())




if __name__ == '__main__':
    settings = dict()
    for attr in ['x_size', 'y_size', 'nr_mines', 'first_success',
                 'max_per_cell']:
        settings[attr] = (imported_settings[attr] if attr in imported_settings
                          else default_settings[attr])
    p = Processor(**settings)
