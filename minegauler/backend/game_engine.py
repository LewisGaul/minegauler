"""
game_engine.py - The core game logic

November 2018, Lewis Gaul

Exports:
AbstractController (class)
    Outline of functions available to be called by a frontend.
Controller (class)
    Implementation of game logic and provision of functions to be called by a
    frontend implementation.
"""

import logging
import time as tm
import functools
from abc import ABC, abstractmethod

from minegauler.backend.minefield import Minefield
from minegauler.backend.utils import Board
from minegauler.shared.internal_types import *
from minegauler.shared.utils import AbstractStruct


logger = logging.getLogger(__name__)



def _ignore_if(game_state=None, cell_state=None):
    """
    Return a decorator which prevents a method from running if any of the given
    parameters are satisfied.
    
    Arguments:
    game_state=None (GameState | (GameState, ...) | None)
        A game state or iterable of game states to match against.
    cell_state=None (subclass of CellContentsType | (..., ...) | None)
        A cell contents type or iterable of the same to match against. The
        decorated method must take the cell coordinate as the first argument.
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


def _ignore_if_not(game_state=None, cell_state=None):
    """
    Return a decorator which prevents a method from running if any of the given
    parameters are satisfied.
    
    Arguments:
    game_state=None (GameState | (GameState, ...) | None)
    A game state or iterable of game states to match against.
    cell_state=None (subclass of CellContentsType | (..., ...) | None)
    A cell contents type or iterable of the same to match against. The
    decorated method must take the cell coordinate as the first argument.
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
    

class GameOptsStruct(AbstractStruct):
    """
    Structure of game options.
    """
    _elements = {
        'x_size':        8,
        'y_size':        8,
        'mines':         10,
        'first_success': True,
        'per_cell':      1,
        'lives':         1,
        'game_mode':     GameFlagMode.NORMAL,
    }


class SharedInfo:
    """
    Information to pass to front-ends.
    
    Attributes:
    cell_updates ({(int, int): CellContentsType, ...})
        Dictionary of updates to cells, mapping the coordinate to the new
        contents of the cell.
    game_state (GameState)
        The state of the game.
    mines_remaining (int)
        The number of mines remaining to be found, given by
        [total mines] - [number of flags]. Can be negative if there are too many
        flags.
    elapsed_time (float | None)
        The time elapsed if the game has ended, otherwise None.
    """
    cell_updates    = {}
    game_state      = GameState.INVALID
    mines_remaining = 0
    elapsed_time    = None



class AbstractController(ABC):
    """
    Abstract controller base class. Frontends can be registered for receiving
    updates, and the required callback functions are defined as abstract
    methods.
    """
    def __init__(self):
        # The frontends registered for updates.
        self.frontends = []

    def register_frontend(self, frontend):
        """

        """
        if not isinstance(frontend, AbstractFrontend):
            raise TypeError("Frontend must subclass AbstractFrontend")
        self.frontends.append(frontend)

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    @abstractmethod
    def new_game(self):
        """
        Create a new game, refresh the board state.
        """
        logger.info("New game requested, refreshing the board")
    @abstractmethod
    def restart_game(self):
        """
        Restart the current game, refresh the board state.
        """
        logger.info("Restart game requested, refreshing the board")
    @abstractmethod
    def select_cell(self, coord):
        """
        Select a cell for a regular click.
        """
        logger.info("Cell %s selected", coord)
    @abstractmethod
    def flag_cell(self, coord):
        """
        Select a cell for flagging.
        """
        logger.info("Cell %s selected for flagging", coord)
    @abstractmethod
    def chord_on_cell(self, coord):
        """
        Select a cell for chording.
        """
        logger.info("Cell %s selected for chording", coord)
    @abstractmethod
    def remove_cell_flags(self, coord):
        """
        Remove flags in a cell, if any.
        """
        logger.info("Flags in cell %s being removed", coord)
    @abstractmethod
    def change_settings(self, **kwargs):
        """
        Update the settings to be used for future games.
        """
        logger.info("Changing settings") #@@@

    @abstractmethod
    def resize_board(self, x_size, y_size, mines):
        """
        Resize the board and/or change the number of mines.
        """
        logger.info("Resizing the board to %sx%s with %s mines",
                    x_size, y_size, mines)



class Controller(AbstractController):
    """
    Class for processing all game logic. Implements functions defined in
    AbstractController that are called from UI.
    
    Attributes:
        opts
    """
    def __init__(self, opts):
        """
        Arguments:
        opts (GameOptsStruct)
            Object containing the required game options as attributes.
        """
        super().__init__(self)

        for kw in GameOptsStruct._elements:
            if not hasattr(opts, kw):
                raise ValueError(f"Missing option {kw}")
                
        self.opts = opts
        # Only normal game mode currently supported.
        self.opts.game_mode = GameFlagMode.NORMAL
        # Initialise game board.
        self.board = Board(opts.x_size, opts.y_size)
        # Keep track of changes made to cell states to be passed to UI.
        self._cell_updates = {}
        # Game-specific data.
        self.game_state = GameState.INVALID
        self.mines_remaining = 0
        self.lives_remaining = 0
        self.start_time = None
        self.end_time = None
        self.mf = Minefield(self.opts.x_size, self.opts.y_size, self.opts.mines,
                            self.opts.per_cell, create=False)
        self._init_game()
    
    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    @_ignore_if(game_state='READY')
    def new_game(self):
        """See AbstractController."""
        
        super().new_game()
        
        self.mf = Minefield(self.opts.x_size, self.opts.y_size, self.opts.mines,
                            self.opts.per_cell, create=False)
        self._init_game()
        for c in self.board.all_coords:
            self._set_cell(c, CellUnclicked())
            
        self._send_ui_updates()
    
    @_ignore_if(game_state=('INVALID', 'READY'))
    def restart_game(self):
        """See AbstractController."""
        
        super().restart_game()
        
        self._init_game()
        for c in self.board.all_coords:
            self._set_cell(c, CellUnclicked())
            
        self._send_ui_updates()
    
    @_ignore_if_not(game_state=('READY', 'ACTIVE'), cell_state=CellUnclicked)
    def select_cell(self, coord):
        """See AbstractController."""
        
        super().select_cell(coord)
            
        # Check if first click.
        if self.game_state == GameState.READY:
            if not self.mf.is_created:
                # Create the minefield.
                if self.opts.first_success:
                    safe_coords = self.mf.get_nbrs(coord, include_origin=True)
                    logger.debug(
                        "Trying to create minefield with the following safe "
                        "coordinates: %s", safe_coords)
                    try:
                        self.mf.create(safe_coords)
                    except ValueError:
                        logger.info(
                            "Unable to give opening on the first click, "
                            "still ensuring a safe click")
                        self.mf.create(safe_coords=[coord])
                    else:
                        logger.debug("Success")
                else:
                    self.mf.create()
                    logger.debug(
                        "Creating minefield with first success turned off")
            self.game_state = GameState.ACTIVE
            self.start_time = tm.time()
            
        self._select_cell_action(coord)
        
        if self.game_state != GameState.LOST:
            self._check_for_completion()
        
        self._send_ui_updates()

    @_ignore_if_not(game_state=('READY', 'ACTIVE'),
                    cell_state=(CellFlag, CellUnclicked))
    def flag_cell(self, coord):
        """See AbstractController."""
        
        super().flag_cell(coord)
        
        if self.opts.game_mode == GameFlagMode.NORMAL:
            if self.board[coord] == CellUnclicked():
                self._set_cell(coord, CellFlag(1))
                self.mines_remaining -= 1
            elif type(self.board[coord]) is CellFlag:
                if self.board[coord] == CellFlag(self.opts.per_cell):
                    self._set_cell(coord, CellUnclicked())
                    self.mines_remaining += self.opts.per_cell
                else:
                    self._set_cell(coord, self.board[coord] + 1)
                    self.mines_remaining -= 1
        
        elif self.opts.game_mode == GameFlagMode.SPLIT:
            if self.board[coord] == CellUnclicked():
                self._split_cell(coord)
        
        self._send_ui_updates()

    @_ignore_if_not(game_state=('READY', 'ACTIVE'), cell_state=CellNum)
    def chord_on_cell(self, coord):
        """See AbstractController."""

        super().chord_on_cell(coord)

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

    @_ignore_if_not(game_state=('READY', 'ACTIVE'), cell_state=CellFlag)
    def remove_cell_flags(self, coord):
        """See AbstractController."""
        
        super().remove_cell_flags(coord)
        
        self.mines_remaining += self.board[coord]
        self._set_cell(coord, CellUnclicked())
        
        self._send_ui_updates()

    def change_settings(self, **kwargs):
        """See AbstractController."""
        super().change_settings(**kwargs)

    def resize_board(self, x_size, y_size, mines):
        """See AbstractController."""
        if (x_size == self.opts.x_size and
            y_size == self.opts.y_size and
            mines == self.opts.mines):
            return
            
        super().resize_board(x_size, y_size, mines)
        
        logger.info("Resizing board from %sx%s with %s mines to "
                "%sx%s with %s mines",
                self.opts.x_size, self.opts.y_size, self.opts.mines,
                x_size, y_size, mines)
        self.game_state = GameState.INVALID
        self.opts.x_size, self.opts.y_size = x_size, y_size
        self.opts.mines = mines
        self.board = Board(x_size, y_size)
        
        self.new_game()
            
    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    def _init_game(self):
        """
        Initialise the game state.
        """
        self.game_state      = GameState.READY
        self.mines_remaining = self.opts.mines
        self.lives_remaining = self.opts.lives
        self.start_time      = None
        self.end_time        = None
        
    def _select_cell_action(self, coord):
        """
        Perform the action of selecting a cell.
        """
        if self.mf.cell_contains_mine(coord):
            logger.debug("Mine hit at %s", coord)
            self._set_cell(coord, CellHit(self.mf[coord]))
            self.lives_remaining -= 1
            
            if self.lives_remaining == 0:
                self.end_time = tm.time()
                logger.info("Game lost")
                self.game_state = GameState.LOST
                for c in self.mf.all_coords:
                    if (self.mf.cell_contains_mine(c) and
                        self.board[c] == CellUnclicked()):
                        self._set_cell(c, CellMine(self.mf[c]))
                    elif (type(self.board[c]) is CellFlag and
                          self.board[c] != self.mf.completed_board[c]):
                        self._set_cell(c, CellWrongFlag(self.board[c]))
                        
        elif self.mf.completed_board[coord] == CellNum(0):
            for opening in self.mf.openings:
                if coord in opening:
                    # Found the opening, quit the loop here.
                    break
            else:
                logger.error("Coordinate %s not found in openings %s",
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
                            
    def _set_cell(self, coord, state):
        """
        Set a cell to be in the given state, storing the change to be sent to
        the UI when _send_ui_updates() is called.
        """
        self.board[coord] = state
        self._cell_updates[coord] = state
                        
    def _check_for_completion(self):
        """
        Check if game is complete by comparing the board to the minefield's
        completed board.
        """
        # Assume (for contradiction) that game is complete.
        is_complete = True
        for c in self.mf.all_coords:
            exp_val = self.mf.completed_board[c]
            if type(exp_val) is CellNum and exp_val != self.board[c]:
                is_complete = False
                break
                
        if is_complete:
            self.end_time = tm.time()
            logger.info("Game won")
            self.game_state = GameState.WON
            for c in self.mf.all_coords:
                if (self.mf.cell_contains_mine(c) and
                    type(self.board[c]) is not CellHit):
                    self._set_cell(c, CellFlag(self.mf[c]))
                    
    def _split_cell(self, coord):
        """
        Split a cell.
        """
        raise NotImplementedError()
    
    def _send_ui_updates(self):
        """
        Send updates to the registered frontends and reset the cell updates.
        """
        logger.debug("Sending updates to registered front-ends")
        
        SharedInfo.cell_updates = self._cell_updates
        SharedInfo.game_state = self.game_state
        SharedInfo.mines_remaining = self.mines_remaining
        if self.game_state in ['WON', 'LOST']:
            SharedInfo.elapsed_time = self.end_time - self.start_time
        else:
            SharedInfo.elapsed_time = None
        for fe in self.frontends:
            fe.update(SharedInfo)
            
        self._cell_updates = {}



class AbstractFrontend(ABC):
    @abstractmethod
    def update(self, info):
        pass