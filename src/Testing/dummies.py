
from utils import diff_values


class DummyProcessor:
    def __init__(self, **settings):
        self.x_size, self.y_size = 8, 8
        self.nr_mines = self.nr_flags = 0
        self.diff = None
        self.first_success = False
        for attr in settings:
            setattr(self, attr, settings[attr])
        self.game = DummyGame(self)
    def change_difficulty(self, diff):
        if diff in diff_values:
            self.x_size, self.y_size, self.nr_mines = diff_settings[diff]
            self.diff = diff
    def prepare_new_game(self):
        pass
    def click(self, x, y):
        pass
    def toggle_flag(self, x, y):
        pass
    def chord(self, x, y):
        pass
    def check_is_game_won(self):
        pass
    def finalise_loss(self):
        pass
    def finalise_win(self):
        pass
    def calculate_probs(self):
        pass
    def save_settings(self):
        pass
    def close_game(self):
        pass

class DummyGame:
    def __init__(self, processor):
        self.board = processor.y_size*[processor.x_size*[0]]
        self.mf = processor.y_size*[processor.x_size*[0]]
        self.state = None
