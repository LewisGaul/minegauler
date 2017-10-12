
from utils import diff_settings


class DummyProcessor:
    def __init__(self):
        self.x_size, self.y_size = 8, 8
        self.nr_mines = self.nr_flags = 0
        self.diff = None
        self.first_success = False
        self.game = DummyGame(self)
    def prepare_new_game(self):
        pass
    def chord(self, x, y):
        pass
    def click(self, x, y):
        pass
    def toggle_flag(self, x, y):
        pass
    def change_difficulty(self, diff):
        if diff in diff_settings:
            self.x_size, self.y_size, self.nr_mines = diff_settings[diff]
            self.diff = diff

class DummyGame:
    def __init__(self, processor):
        self.board = processor.y_size*[processor.x_size*[0]]
        self.mf = processor.y_size*[processor.x_size*[0]]
        self.state = None
