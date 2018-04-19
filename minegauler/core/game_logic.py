"""
game_logic.py - The core game logic

April 2018, Lewis Gaul
"""

from minegauler.utils import Grid, GameCellMode
from .utils import Board, CellState


class Processor:
    """
    Class for processing all game logic. Any 'clicks' are received here, and a
    """
    def __init__(self, x_size, y_size, game_mode=GameCellMode.NORMAL):
        self.x_size = x_size
        self.y_size = y_size
        self.game_mode = game_mode
        self.grid = Grid(x_size, y_size, fill=None)
        self.board = Board(x_size, y_size)
        self.ui = None
        self.mf_ui = None
    
    def leftclick_received(self, x, y):
        if self.board[y][x] == CellState.UNCLICKED:
            self.mf_ui.set_cell_image(x, y, CellState.NUM11)
            self.board[y][x] = CellState.NUM11
    
    def rightclick_received(self, x, y):
        if self.board[y][x] == CellState.UNCLICKED:
            self.mf_ui.split_cell(x, y)
            self.board[y][x] = CellState.SPLIT



if __name__ == '__main__':
    from .stubs import StubUI, StubMinefieldUI
    procr = Processor(3, 5)
    ui = StubUI(procr)
    mf_ui = StubMinefieldUI(procr)