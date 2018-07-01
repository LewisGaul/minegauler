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

import logging

from PyQt5.QtCore import pyqtSlot

from minegauler.utils import ASSERT
from .callbacks import cb_core
from .types import Grid, GameCellMode, CellState, GameState, Board
from .minefield import Minefield


logger = logging.getLogger(__name__)


class Controller:
    """
    Class for processing all game logic. Implements callback functions for
    'clicks'.
    """
    def __init__(self, opts):
        for kw in ['x_size', 'y_size', 'mines', 'first_success', 'per_cell']:
            ASSERT(hasattr(opts, kw), f"Missing option {kw}")
        self.opts = opts
        self.mines_remaining = self.opts.mines
        # Initialise game board.
        self.board = Board(opts.x_size, opts.y_size)
        # Callbacks from the UI.
        cb_core.leftclick.connect(self.leftclick_cb)
        cb_core.rightclick.connect(self.rightclick_cb)
        cb_core.bothclick.connect(self.bothclick_cb)
        cb_core.new_game.connect(self.new_game_cb)
        cb_core.end_game.connect(self.end_game_cb)
        cb_core.resize_board.connect(self.resize_board)
        # Keeps track of whether the minefield has been created yet.
        self.game_state = GameState.READY
    
    # @pyqtSlot(tuple)
    def leftclick_cb(self, coord):
        """Callback for a left-click on a cell."""
        if (self.game_state not in [GameState.READY, GameState.ACTIVE]
            or self.board[coord] != CellState.UNCLICKED):
            return
            
        logger.info("Valid leftclick received on cell %s", coord)
        # Check if first click.
        if self.game_state == GameState.READY:
            # Create the minefield.
            if self.opts.first_success:
                safe_coords = self.mf.get_nbrs(*coord, include_origin=True)
            else:
                safe_coords = []
            self.mf.create(self.opts.mines, self.opts.per_cell, safe_coords)
            self.game_state = GameState.ACTIVE
            cb_core.start_game.emit()
            
        self.leftclick_action(coord)
        
        if self.game_state == GameState.LOST:
            logger.info("Game lost")
            cb_core.end_game.emit(GameState.LOST)
        else:
            self.check_for_completion()

    def leftclick_action(self, coord):
        if self.board[coord] != CellState.UNCLICKED:
            return
        if self.mf.cell_contains_mine(*coord):
            logger.debug("Mine hit")
            self.set_cell(coord, CellState.HITS[self.mf[coord]])
            for c in self.mf.all_coords:
                if (self.mf.cell_contains_mine(*c) and
                    c != coord and
                    self.board[c] == CellState.UNCLICKED):
                    self.set_cell(c, CellState.MINES[self.mf[c]])
                elif (self.board[c] in CellState.FLAGS and
                      self.board[c] != self.mf.completed_board[c]):
                    self.set_cell(c, CellState.CROSSES[self.board[c].num])
            # if self.lives_remaining == 0:
            self.game_state = GameState.LOST
        elif self.mf.completed_board[coord] == CellState.NUM0:
            for opening in self.mf.openings:
                if coord in opening:
                    # Found the opening, quit the loop here.
                    break
            logger.debug("Opening hit: %s", opening)
            for c in opening:
                if self.board[c] == CellState.UNCLICKED:
                    self.set_cell(c, self.mf.completed_board[c])
        else:
            logger.debug("Regular cell revealed")
            self.set_cell(coord, self.mf.completed_board[coord])
    
    # @pyqtSlot(tuple)
    def rightclick_cb(self, coord):
        """Callback for a right-click on a cell."""
        if self.game_state not in [GameState.READY, GameState.ACTIVE]:
            return
            
        logger.info("Valid rightclick received on cell %s", coord)
        if self.game_mode == GameCellMode.NORMAL:
            if self.board[coord] == CellState.UNCLICKED:
                self.set_cell(coord, CellState.FLAG1)
                self.mines_remaining -= 1
            elif self.board[coord] in CellState.FLAGS:
                if self.board[coord] == CellState.FLAGS[per_cell]:
                    self.set_cell(coord, CellState.UNCLICKED)
                    self.mines_remaining += per_cell
                else:
                    self.set_cell(coord, self.board[coord] + 1)
                    self.mines_remaining -= 1
            cb_core.set_mines_counter.emit(self.mines_remaining)
        
        elif self.game_mode == GameCellMode.SPLIT:
            if self.board[coord] == CellState.UNCLICKED:
                self.split_cell(coord)
    
    # @pyqtSlot(tuple)
    def bothclick_cb(self, coord):
        """Callback for a left-and-right-click on a cell."""
        
        if (self.game_state not in [GameState.READY, GameState.ACTIVE]
            or self.board[coord] not in CellState.NUMS):
            return
            
        logger.info("Valid bothclick received on cell %s", coord)
        nbrs = self.board.get_nbrs(*coord)
        num_flagged_nbrs = sum(
            [self.board[c].num for c in nbrs
                                           if self.board[c] in CellState.FLAGS])
        logger.debug("%s flagged mine(s) around clicked cell showing number %s",
                     num_flagged_nbrs, self.board[coord].num)
        if num_flagged_nbrs == self.board[coord].num:
            unclicked_nbrs = [c for c in nbrs
                                        if self.board[c] == CellState.UNCLICKED]
            logger.info("Successful chording, selecting cells %s",
                        unclicked_nbrs)
            for c in unclicked_nbrs:
                self.leftclick_action(c)
                
            if self.game_state == GameState.LOST:
                logger.info("Game lost")
                cb_core.end_game.emit(GameState.LOST)
            else:
                self.check_for_completion()
            
    def set_cell(self, coord, state):
        """
        Set a cell to be in the given state, calling registered callbacks.
        """
        self.board[coord] = state
        cb_core.set_cell.emit(coord)
                        
    def check_for_completion(self):
        """
        Check if game is complete by comparing self.board to
        self.mf.completed_board, and if it is call relevent 'end game' methods.
        """
        # Assume (for contradiction) that game is complete.
        is_complete = True
        for c in self.mf.all_coords:
            exp_val = self.mf.completed_board[c]
            if exp_val in CellState.NUMS and exp_val != self.board[c]:
                is_complete = False
                break
        if is_complete:
            logger.info("Game won")
            for c in self.mf.all_coords:
                if self.mf.cell_contains_mine(*c):
                    self.set_cell(c, CellState.FLAGS[self.mf[c]])
            cb_core.end_game.emit(GameState.WON)
    
    # @pyqtSlot()
    def new_game_cb(self):
        """Create a new game."""
        self.game_state = GameState.READY
        self.mines_remaining = self.opts.mines
        cb_core.set_mines_counter.emit(self.opts.mines)
        self.mf = Minefield(self.opts.x_size, self.opts.y_size)
        for c in self.board.all_coords:
            self.set_cell(c, CellState.UNCLICKED)
            
    # @pyqtSlot(GameState)
    def end_game_cb(self, game_state):
        """
        End a game.
        Arguments:
          game_state (GameState)
            GameState.WON or GameState.LOST.
        """
        self.game_state = game_state
        if game_state == GameState.WON:
            cb_core.set_mines_counter.emit(0)
    
    def resize_board(self, x_size, y_size, mines):
        logger.info("Resizing board from %sx%s with %s mines to "
                    "%sx%s with %s mines",
                    self.opts.x_size, self.opts.y_size, self.opts.mines,
                    x_size, y_size, mines)
        self.opts.x_size, self.opts.y_size = x_size, y_size
        self.opts.mines = mines
        self.board = Board(x_size, y_size)
        cb_core.resize_minefield.emit(self.board)
        cb_core.new_game.emit()


if __name__ == '__main__':
    # from .stubs import StubUI, StubMinefieldUI
    ctrlr = Controller(3, 5)
    # ui = StubUI(procr)
    # mf_ui = StubMinefieldUI(procr)

