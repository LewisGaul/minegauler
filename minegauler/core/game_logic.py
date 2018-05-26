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

from minegauler.utils import Grid, GameCellMode, CellState, GameState
from .utils import Board
from .minefield import Minefield


#@@@
mines = 8
per_cell = 2
first_success = True


class Controller:
    """
    Class for processing all game logic. Implements callback functions for
    'clicks'.
    """
    def __init__(self, x_size, y_size, game_mode=GameCellMode.NORMAL):
        self.x_size = x_size
        self.y_size = y_size
        self.game_mode = game_mode
        # Initialise empty minefield and game board.
        self.mf = Minefield(self.x_size, self.y_size)
        self.board = Board(x_size, y_size)
        # Variables to be set to UI methods.
        self.set_cell_cb_list = []
        self.split_cell_cb_list = []
        self.new_game_cb_list = []
        self.end_game_cb_list = []
        # Whether the minefield been created yet.
        self.game_state = GameState.READY
    
    def leftclick(self, x, y):
        """
        Callback for a left-click on a cell.
        """
        if (self.game_state not in [GameState.READY, GameState.ACTIVE]
            or self.board[y][x] != CellState.UNCLICKED):
            return
            
        # Check if first click.
        if self.game_state == GameState.READY:
            if first_success:
                safe_coords = self.mf.get_nbrs(x, y, include_origin=True)
            else:
                safe_coords = []
            self.mf.create(mines, per_cell, safe_coords)
            self.game_state = GameState.ACTIVE
        # Mine hit.
        if self.mf.cell_contains_mine(x, y):
            self.set_cell(x, y, CellState.HITS[self.mf[y][x]])
            for coord in self.mf.all_coords:
                p, q = coord
                if self.mf.cell_contains_mine(p, q) and coord != (x, y):
                    self.set_cell(p, q, CellState.MINES[self.mf[q][p]])
            self.end_game(GameState.LOST)
        # Opening hit.
        elif self.mf.completed_board[y][x] == CellState.NUM0:
            for opening in self.mf.openings:
                if (x, y) in opening:
                    # Found the opening, quit the loop here.
                    break
            for coord in opening:
                x, y = coord
                if self.board[y][x] == CellState.UNCLICKED:
                    self.set_cell(x, y, self.mf.completed_board[y][x])
        # Reveal clicked cell only.
        else:
            self.set_cell(x, y, self.mf.completed_board[y][x])
        
        self.check_for_completion()
    
    def rightclick(self, x, y):
        """
        Callback for a right-click on a cell.
        """
        if self.game_state not in [GameState.READY, GameState.ACTIVE]:
            return
        if self.game_mode == GameCellMode.NORMAL:
            if self.board[y][x] == CellState.UNCLICKED:
                self.set_cell(x, y, CellState.FLAG1)
            elif self.board[y][x] in CellState.FLAGS:
                if self.board[y][x] == CellState.FLAGS[per_cell]:
                    self.set_cell(x, y, CellState.UNCLICKED)
                else:
                    self.set_cell(x, y, self.board[y][x] + 1)
        
        elif self.game_mode == GameCellMode.SPLIT:
            if self.board[y][x] == CellState.UNCLICKED:
                self.split_cell(x, y)
    
    def bothclick(self, x, y):
        """
        Callback for a left-and-right-click on a cell.
        """
        if (self.game_state not in [GameState.READY, GameState.ACTIVE]
            or self.board[y][x] != CellState.UNCLICKED):
            return
            
    def set_cell(self, x, y, state):
        """
        Set a cell to be in the given state, calling registered callbacks.
        """
        self.board[y][x] = state
        for cb in self.set_cell_cb_list:
            cb((x, y), state)
            
    def split_cell(self, x, y):
        """
        Split a cell, calling registered callbacks.
        """
        for cb in self.split_cell_cb_list:
            self.board[y][x] = CellState.SPLIT
            cb((x, y))
            
    def check_for_completion(self):
        """
        Check if game is complete by comparing self.board to
        self.mf.completed_board, and if it is call relevent 'end game' methods.
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
            for coord in self.mf.all_coords:
                x, y = coord
                if self.mf.cell_contains_mine(x, y):
                    self.set_cell(x, y, CellState.FLAGS[self.mf[y][x]])
            self.end_game(GameState.WON)
    
    def new_game(self):
        """
        State a new game, calling registered callbacks.
        """
        self.game_state = GameState.READY
        self.mf = Minefield(self.x_size, self.y_size)
        for coord in self.board.all_coords:
            x, y = coord
            self.set_cell(x, y, CellState.UNCLICKED)
        for cb in self.new_game_cb_list:
            cb()
            
    def end_game(self, game_state):
        """
        End a game, calling registered callbacks.
        Arguments:
          game_state (GameState)
            GameState.WON or GameState.LOST.
        """
        self.game_state = game_state
        for cb in self.end_game_cb_list:
            cb(game_state)


if __name__ == '__main__':
    # from .stubs import StubUI, StubMinefieldUI
    ctrlr = Controller(3, 5)
    # ui = StubUI(procr)
    # mf_ui = StubMinefieldUI(procr)

