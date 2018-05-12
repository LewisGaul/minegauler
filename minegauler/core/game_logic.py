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

from minegauler.utils import Grid, GameCellMode, CellState
from .utils import Board, GameState
from .minefield import Minefield


mines = 10
per_cell = 2


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
        self.mf = Minefield(self.x_size, self.y_size)
        self.board = Board(x_size, y_size)
        self.set_cell_fn = None
        self.split_cell_fn = None
        self.new_game_fn = None
        self.end_game_fn = None
        # Whether the minefield been created yet.
        self.game_state = GameState.READY
    
    def new_game_cb(self):
        """
        
        """
        self.game_state = GameState.READY
        self.mf = Minefield(self.x_size, self.y_size)
        if self.new_game_fn:
            self.new_game_fn()
        
    def leftclick_cb(self, x, y):
        """
        
        """
        if (self.game_state not in [GameState.READY, GameState.ACTIVE]
            or self.board[y][x] != CellState.UNCLICKED):
            return
            
        # Check if first click.
        if self.game_state == GameState.READY:
            self.mf.create(mines, per_cell, [(x, y)])
            self.game_state = GameState.ACTIVE
        # Mine hit.
        if self.mf.cell_contains_mine(x, y):
            self.set_cell(x, y, CellState.HITS[self.mf[y][x]])
            for coord in self.mf.all_coords:
                p, q = coord
                if self.mf.cell_contains_mine(p, q) and coord != (x, y):
                    self.set_cell(p, q, CellState.MINES[self.mf[q][p]])
            self.end_game()
            self.game_state = GameState.LOST
        # Opening hit.
        elif self.mf.completed_board[y][x] == 0:
            for opening in self.mf.openings:
                if (x, y) in opening:
                    # Found the opening, quit the loop here.
                    break
            for coord in opening:
                x, y = coord
                self.set_cell(x, y, self.mf.completed_board[y][x])
        # Cell with single number to reveal.
        else:
            self.set_cell(x, y, self.mf.completed_board[y][x])
        
        self.check_for_completion()
    
    def rightclick_cb(self, x, y):
        """
        
        """
        if self.game_state not in [GameState.READY, GameState.ACTIVE]:
            return
        if self.board[y][x] == CellState.UNCLICKED:
            self.split_cell(x, y)
            self.board[y][x] = CellState.SPLIT
            
    def set_cell(self, x, y, state):
        """
        
        """
        self.board[y][x] = state
        if self.set_cell_fn:
            self.set_cell_fn(x, y, state)
            
    def split_cell(self, x, y):
        """
        
        """
        if self.split_cell_fn:
            self.split_cell_fn(x, y)
            
    def check_for_completion(self):
        """
        
        """
        # Assume (for contradiction) that game is complete.
        is_complete = True
        for coord in self.mf.all_coords:
            x, y = coord
            exp_val = self.mf.completed_board[y][x]
            if exp_val in CellState.NUMS and exp_val != self.board[y][x]:
                is_complete = False
                break
        if is_complete:
            self.game_state = GameState.WON
            for coord in self.mf.all_coords:
                x, y = coord
                if self.mf.cell_contains_mine(x, y):
                    self.set_cell(x, y, CellState.FLAGS[self.mf[y][x]])
    
    def end_game(self):
        if self.end_game_fn:
            self.end_game_fn()


if __name__ == '__main__':
    from .stubs import StubUI, StubMinefieldUI
    ctrlr = Controller(3, 5)
    # ui = StubUI(procr)
    # mf_ui = StubMinefieldUI(procr)

