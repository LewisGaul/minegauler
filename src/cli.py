"""
Command-line user interface.
"""

from utils import prettify_grid


class GameCLI:
    extra_game_settings = []
    def __init__(self, processor, **settings):
        self.procr = processor
    def choose_settings(self):
        diff = None
        while diff not in ['', 'b', 'i', 'e', 'm', 'c', 'beginner',
                           'intermediate', 'expert', 'master', 'custom']:
            if diff is not None:
                print("Invalid entry. The options are as follows:\n" +
                      "  b - beginner,      8 x  8 grid with  10 mines\n"
                      "  i - intermediate, 16 x 16 grid with  40 mines\n"
                      "  e - expert,       30 x 16 grid with  99 mines\n"
                      "  m - master,       30 x 30 grid with 200 mines\n"
                      "  c - custom (you will be prompted to enter dimensions" +
                          " and a number of mines)")
            diff = input(
                "Enter your choice of difficulty " +
                "(b, i, e, m, c or hit ENTER for default): ").lower()
        if not diff:
            return      #no change to the setting/use default
        if diff == 'c':
            prompt = "Invalid size."
            print("Input custom dimensions (x_size, y_size): ", end='')
            x, y = self.get_coord(2, 1, 50, 50, prompt)
            mines = None
            while type(mines) is not int or mines < 1 or mines > x*y - 1:
                if mines is not None:
                    print("Must be between 1 and", x*y - 1,
                          "for board with dimensions ({} x {}).".format(x, y))
                mines = input("Number of mines: ").strip()
                if mines.isdigit():
                    mines = int(mines)
            self.procr.change_difficulty('c', x, y, mines)
        else:
            self.procr.change_difficulty(diff[0])
    def start(self):
        """This is the CLI equivalent of 'mainloop'."""
        self.choose_settings()
        while self.procr.game.state in [self.procr.game.READY,
                                        self.procr.game.ACTIVE]:
            self.procr.game.print_board()
            self.get_click()
    def prepare_new_game(self):
        pass
    def get_click(self):
        """Get the user to choose a coordinate to be clicked."""
        print("Enter a coordinate in the form (x, y)," +
              " where the top-left is (1, 1): ", end='')
        prompt = "Invalid coordinate entered."
        coord = self.get_coord(1, 1, self.procr.x_size, self.procr.y_size,
                               prompt)
        self.perform_click(*coord)
    def get_coord(self, x_min, y_min, x_max, y_max, prompt):
        """Get user to enter a coordinate/dimensions between given bounds."""
        ####### Add in validation.
        coord_input = input()
        return map(int, coord_input.split())
    def perform_click(self, x, y):
        """Provides callable for performing a click (top-left is (1, 1))."""
        self.procr.click(x-1, y-1)
    def start_game(self):
        """Not needed for CLI, this is called when the first click is made."""
        pass
    def reveal_cell(self, x, y):
        """Not needed for a CLI, cells are revealed as they are chosen."""
        pass
    def flag(self, x, y):
        pass
    def unflag(self, x, y):
        pass
    def finalise_loss(self):
        print("\nYou hit a mine!")
        self.procr.game.print_board()
        print("Game over")
    def finalise_win(self):
        print("\nYou won!")
        self.procr.game.print_board()
    def highscore_added(self, h):
        pass


# Dummy highscore facilities
class HighscoresModel:
    def __init__(self, *args, **kwargs):
        pass
    def update_hscores_group(self, settings):
        pass

def save_all_highscores():
    pass
