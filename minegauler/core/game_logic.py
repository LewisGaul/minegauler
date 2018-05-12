"""
game_logic.py - The core game logic

April 2018, Lewis Gaul

Exports:
  Controller
    Controller class, implementing game logic and providing callback functions.
    Arguments:
      x_size - Number of columns
      y_size - Number of rows
      game_mode (optional) - Mode specifying which game logic to use
    Attributes:
      board - The current board state
"""

from minegauler.utils import Grid, GameCellMode
from .utils import Board, CellState


class Controller:
    """
    Class for processing all game logic. Implements callback functions for
    'clicks'.
    """
    def __init__(self, x_size, y_size, game_mode=GameCellMode.NORMAL):
        self.x_size = x_size
        self.y_size = y_size
        self.game_mode = game_mode
        # self.grid = Grid(x_size, y_size, fill=None)
        self.board = Board(x_size, y_size)
        self.set_cell_fn = None
        self.split_cell_fn = None
    
    def set_cell(self, x, y, state):
        """
        
        """
        if self.set_cell_fn:
            self.set_cell_fn(x, y, state)
    
    def split_cell(self, x, y):
        """
        
        """
        if self.split_cell_fn:
            self.split_cell_fn(x, y)
    
    def leftclick_cb(self, x, y):
        """
        
        """
        if self.board[y][x] == CellState.UNCLICKED:
            self.set_cell(x, y, CellState.NUM11)
            self.board[y][x] = CellState.NUM11
    
    def rightclick_cb(self, x, y):
        """
        
        """
        if self.board[y][x] == CellState.UNCLICKED:
            self.split_cell(x, y)
            self.board[y][x] = CellState.SPLIT



if __name__ == '__main__':
    from .stubs import StubUI, StubMinefieldUI
    ctrlr = Controller(3, 5)
    # ui = StubUI(procr)
    # mf_ui = StubMinefieldUI(procr)