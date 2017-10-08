


class DummyProcessor:
    def __init__(self):
        self.x_size, self.y_size = 8, 8
        # self.board = self.y_size*[self.x_size*['U']]
        self.game = DummyGame(self)
    def start_new_game(self):
        pass
    def chord(self, x, y):
        pass
    def click(self, x, y):
        pass
    def toggle_flag(self, x, y):
        pass

class DummyGame:
    def __init__(self, processor):
        self.board = processor.y_size*[processor.x_size*['U']]
        self.mf = processor.y_size*[processor.x_size*[0]]
        self.state = None
