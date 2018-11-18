"""
game_engine.py - The core game logic

November 2018, Lewis Gaul

Exports:
Controller (class)
    Implementation of game logic and provision of callback functions.
"""

import logging
import time as tm
from abc import ABC, abstractmethod
import functools

from minegauler.backend.minefield import Minefield
from minegauler.backend.utils import Board
from minegauler.shared.internal_types import *


logger = logging.getLogger(__name__)



def ignore_if(game_state=None, cell_state=None):
    """
    @@@
    """
    def decorator(method):
        if cell_state is None:
            @functools.wraps(method)
            def wrapped(self, *args, **kwargs):
                if (game_state is not None and
                    (self.game_state == game_state or
                     self.game_state in game_state)):
                    return
                return method(self, *args, **kwargs)
        else:
            @functools.wraps(method)
            def wrapped(self, coord, *args, **kwargs):
                if ((game_state is not None and
                     (self.game_state == game_state or
                      self.game_state in game_state)) or
                    isinstance(self.board[coord], cell_state)):
                    return
                return method(self, coord, *args, **kwargs)
        
        return wrapped
    return decorator


def ignore_if_not(game_state=None, cell_state=None):
    """
    @@@
    """
    def decorator(method):
        if cell_state is None:
            @functools.wraps(method)
            def wrapped(self, *args, **kwargs):
                if (game_state is not None and
                    self.game_state != game_state and
                    self.game_state not in game_state):
                    return
                return method(self, *args, **kwargs)
        else:
            @functools.wraps(method)
            def wrapped(self, coord, *args, **kwargs):
                if ((game_state is not None and
                     self.game_state != game_state and
                     self.game_state not in game_state) or
                    not isinstance(self.board[coord], cell_state)):
                    return
                return method(self, coord, *args, **kwargs)
        
        return wrapped
    return decorator
    


class SharedInfo:
    cell_updates = {}
    game_state = GameState.INVALID
    mines_remaining = 0
    end_time = None



class AbstractController(ABC):
    """
    """
    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    @abstractmethod
    def new_game(self):
        """
        """
        pass
    # @abstractmethod
    # def restart_game(self):
    #     """
    #     """
    #     pass
    @abstractmethod
    def select_cell(self, coord):
        """
        """
        logger.info("Cell %s selected", coord)
    @abstractmethod
    def chord_on_cell(self, coord):
        """
        """
        logger.info("Cell %s selected for chording", coord)
    @abstractmethod
    def flag_cell(self, coord):
        """
        """
        logger.info("Cell %s selected for flagging", coord)
    # @abstractmethod
    # def remove_cell_flags(self, coord):
    #     """
    #     """
    #     logger.info("Flags in cell %s being removed", coord)
    @abstractmethod
    def resize_board(self, x_size, y_size, mines):
        """
        """
        pass



class Controller(AbstractController):
    """
    Class for processing all game logic. Implements callback functions from UI.
    """
    def __init__(self, opts):
        for kw in ['x_size', 'y_size', 'mines', 'first_success', 'per_cell']:
            if not hasattr(opts, kw):
                raise ValueError(f"Missing option {kw}")
        self.opts = opts
        self.mf = None
        # Initialise game board.
        self.board = Board(opts.x_size, opts.y_size)
        self.game_state = GameState.INVALID
        # Only normal game mode supported.
        self.game_mode = GameFlagMode.NORMAL
        # Keep track of changes made to cell states to be passed to UI.
        self.cell_updates = {}
        # The frontends registered for updates.
        self.frontends = []
        # Game-specific data.
        self.mines_remaining = self.opts.mines
        self.start_time, self.end_time = None, None
    
    @ignore_if_not(game_state=('READY', 'ACTIVE'), cell_state=CellUnclicked)
    def select_cell(self, coord):
        """See AbstractController."""
        
        super().select_cell(coord)
            
        # Check if first click.
        if self.game_state == GameState.READY:
            # Create the minefield.
            if self.opts.first_success:
                safe_coords = self.mf.get_nbrs(coord, include_origin=True)
            else:
                safe_coords = []
            self.mf.create(safe_coords)
            self.game_state = GameState.ACTIVE
            self.start_time = tm.time()
            
        self._select_cell_action(coord)
        
        if self.game_state != GameState.LOST:
            self._check_for_completion()
        
        self._send_ui_updates()
    
    def _select_cell_action(self, coord):
        """
        @@@
        """
        if self.mf.cell_contains_mine(coord):
            logger.debug("Mine hit")
            self._set_cell(coord, CellHit(self.mf[coord]))
            for c in self.mf.all_coords:
                if (self.mf.cell_contains_mine(c) and
                    self.board[c] == CellUnclicked()):
                    self._set_cell(c, CellMine(self.mf[c]))
                elif (type(self.board[c]) is CellFlag and
                      self.board[c] != self.mf.completed_board[c]):
                    self._set_cell(c, CellWrongFlag(self.board[c]))
            # if self.lives_remaining == 0:
            self.end_time = tm.time()
            self.game_state = GameState.LOST
            logger.info("Game lost")
        elif self.mf.completed_board[coord] == CellNum(0):
            for opening in self.mf.openings:
                if coord in opening:
                    # Found the opening, quit the loop here.
                    break
            else:
                logger.error("Coord %s not found in openings %s",
                             coord, self.mf.openings)
                raise RuntimeError(
                    f"Expected there to be an opening containing coord {coord}")
            logger.debug("Opening hit: %s", opening)
            for c in opening:
                if self.board[c] == CellUnclicked():
                    self._set_cell(c, self.mf.completed_board[c])
        else:
            logger.debug("Regular cell revealed")
            self._set_cell(coord, self.mf.completed_board[coord])

    @ignore_if_not(game_state=('READY', 'ACTIVE'),
                   cell_state=(CellFlag, CellUnclicked))
    def flag_cell(self, coord):
        """See AbstractController."""
        
        if self.game_mode == GameFlagMode.NORMAL:
            if self.board[coord] == CellUnclicked():
                self._set_cell(coord, CellFlag(1))
                self.mines_remaining -= 1
            elif type(self.board[coord]) is CellFlag:
                if self.board[coord] == CellFlag(per_cell):
                    self._set_cell(coord, CellUnclicked())
                    self.mines_remaining += per_cell
                else:
                    self._set_cell(coord, self.board[coord] + 1)
                    self.mines_remaining -= 1
            # cb_core.set_mines_counter.emit(self.mines_remaining) @@@
        
        # elif self.game_mode == GameFlagMode.SPLIT:
        #     if self.board[coord] == CellState.UNCLICKED:
        #         self.split_cell(coord)
        
        self._send_ui_updates()
    
    @ignore_if_not(game_state=('READY', 'ACTIVE'), cell_state=CellNum)
    def chord_on_cell(self, coord):
        """See AbstractController."""
        
        nbrs = self.board.get_nbrs(*coord)
        num_flagged_nbrs = sum(
            [self.board[c] for c in nbrs
                if isinstance(self.board[c], CellMineType)])
        logger.debug("%s flagged mine(s) around clicked cell showing number %s",
                     num_flagged_nbrs, self.board[coord].num)
                     
        if self.board[coord] != CellNum(num_flagged_nbrs):
            return
            
        unclicked_nbrs = [c for c in nbrs if self.board[c] == CellUnclicked()]
        logger.info("Successful chording, selecting cells %s", unclicked_nbrs)
        for c in unclicked_nbrs:
            self._select_cell_action(c)
            if self.game_state != GameState.ACTIVE:
                break
            
        if self.game_state != GameState.LOST:
            self._check_for_completion()
            
        self._send_ui_updates()
            
    def _set_cell(self, coord, state):
        """
        Set a cell to be in the given state, storing the change to be sent to
        the UI when _send_ui_updates() is called.
        """
        self.board[coord] = state
        self.cell_updates[coord] = state
    
    def _send_ui_updates(self):
        """
        @@@
        """
        logger.debug("Sending updates to registered front-ends")
        SharedInfo.cell_updates = self.cell_updates
        SharedInfo.game_state = self.game_state
        SharedInfo.mines_remaining = self.mines_remaining
        if self.game_state in ['WON', 'LOST']:
            SharedInfo.end_time = self.end_time - self.start_time
        self.cell_updates = {}
        for fe in self.frontends:
            fe.update(SharedInfo)
                        
    def _check_for_completion(self):
        """
        Check if game is complete by comparing self.board to
        self.mf.completed_board - if it is, call relevant 'end game' methods.
        """
        # Assume (for contradiction) that game is complete.
        is_complete = True
        for c in self.mf.all_coords:
            exp_val = self.mf.completed_board[c]
            if type(exp_val) is CellNum and exp_val != self.board[c]:
                is_complete = False
                break
        if is_complete:
            logger.info("Game won")
            self.game_state = GameState.WON
            for c in self.mf.all_coords:
                if (self.mf.cell_contains_mine(c) and
                    type(self.board[c]) is not CellHit):
                    self._set_cell(c, CellFlag(self.mf[c]))
    
    @ignore_if(game_state='READY')
    def new_game(self):
        """See AbstractController."""
        self.game_state = GameState.READY
        self.mines_remaining = self.opts.mines
        self.mf = Minefield(self.opts.x_size, self.opts.y_size, self.opts.mines,
                            self.opts.per_cell, create=False)
        for c in self.board.all_coords:
            self._set_cell(c, CellUnclicked())
        self._send_ui_updates()
    
    def resize_board(self, x_size, y_size, mines):
        """See AbstractController."""
        if (x_size == self.opts.x_size and
            y_size == self.opts.y_size and
            mines == self.opts.mines):
            return
        logger.info("Resizing board from %sx%s with %s mines to "
                    "%sx%s with %s mines",
                    self.opts.x_size, self.opts.y_size, self.opts.mines,
                    x_size, y_size, mines)
        self.game_state = GameState.INVALID
        self.opts.x_size, self.opts.y_size = x_size, y_size
        self.opts.mines = mines
        self.board = Board(x_size, y_size)
        # cb_core.resize_minefield.emit(self.board)
        # cb_core.new_game.emit()
        self.new_game()

