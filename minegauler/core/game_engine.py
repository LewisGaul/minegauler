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
from abc import ABC, abstractmethod
from typing import Dict, Optional

import attr

from .game import Game
from .grid import CoordType
from .internal_types import *
from .utils import GameOptsStruct, get_num_pos_args_accepted


logger = logging.getLogger(__name__)


@attr.attrs(auto_attribs=True)
class SharedInfo:
    """
    Information to pass to frontends.
    
    Elements:
    cell_updates ({(int, int): CellContentsType, ...})
        Dictionary of updates to cells, mapping the coordinate to the new
        contents of the cell.
    game_state (GameState)
        The state of the game.
    mines_remaining (int)
        The number of mines remaining to be found, given by
        [total mines] - [number of flags]. Can be negative if there are too many
        flags. If the number is unchanged, None may be passed.
    lives_remaining (int)
        The number of lives remaining.
    elapsed_time (float | None)
        The time elapsed if the game has ended, otherwise None.
    """

    cell_updates: Dict[CoordType, CellContentsType] = attr.Factory(dict)
    game_state: GameState = GameState.READY
    mines_remaining: int = 0
    lives_remaining: int = 0
    elapsed_time: Optional[float] = None


class AbstractController(ABC):
    """
    Abstract controller base class. Callbacks can be registered for receiving
    updates.
    """

    def __init__(self):
        # The registered functions to be called with updates.
        self._registered_callbacks = []

    def register_callback(self, callback):
        """
        Register a callback function to receive updates from a game controller.
        If the callback is invalid it will not be registered and an error will
        be logged.
        
        Arguments:
        callback (callable, taking one argument)
            The callback function/method, to be called with the update 
            information (of type SharedInfo).
        """

        # Perform some validation on the provided callback.
        try:
            min_args, max_args = get_num_pos_args_accepted(callback)
        except ValueError as e:
            logger.warning("Unable to check callback function")
            logger.debug("%s", e)
        except TypeError:
            logger.error(
                "Invalid callback function - does not appear to be " "callable: %s",
                callback,
            )
            return
        else:
            if min_args > 1 or max_args < 1:
                logger.error(
                    "Invalid callback function - must be able to "
                    "accept one argument: %s",
                    callback,
                )
                return

        logger.info("%s: Registering callback: %s", type(self), callback)
        self._registered_callbacks.append(callback)

    @abstractmethod
    def _send_callback_updates(self):
        """
        Send updates using the registered callbacks.
        """
        logger.info("%s: Sending updates using registered callbacks", type(self))

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    @abstractmethod
    def new_game(self):
        """
        Create a new game, refresh the board state.
        """
        logger.info("%s: New game requested, refreshing the board", type(self))

    @abstractmethod
    def restart_game(self):
        """
        Restart the current game, refresh the board state.
        """
        logger.info("%s: Restart game requested, refreshing the board", type(self))

    @abstractmethod
    def select_cell(self, coord):
        """
        Select a cell for a regular click.
        """
        logger.info("%s: Cell %s selected", type(self), coord)

    @abstractmethod
    def flag_cell(self, coord):
        """
        Select a cell for flagging.
        """
        logger.info("%s: Cell %s selected for flagging", type(self), coord)

    @abstractmethod
    def chord_on_cell(self, coord):
        """
        Select a cell for chording.
        """
        logger.info("%s: Cell %s selected for chording", type(self), coord)

    @abstractmethod
    def remove_cell_flags(self, coord):
        """
        Remove flags in a cell, if any.
        """
        logger.info("%s: Flags in cell %s being removed", type(self), coord)

    @abstractmethod
    def resize_board(self, x_size, y_size, mines):
        """
        Resize the board and/or change the number of mines.
        """
        logger.info(
            "%s: Resizing the board to %sx%s with %s mines",
            type(self),
            x_size,
            y_size,
            mines,
        )


class Controller(AbstractController):
    """
    Class for processing all game logic. Implements functions defined in
    AbstractController that are called from UI.
    
    Attributes:
    opts (GameOptsStruct)
        Options for use in games.
    """

    def __init__(self, opts):
        """
        Arguments:
        opts (GameOptsStruct)
            Object containing the required game options as attributes.
        """
        super().__init__()

        self.opts = GameOptsStruct._from_struct(opts)
        self.game = None
        self.new_game()

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def new_game(self):
        """See AbstractController."""
        super().new_game()
        self.game = Game(
            x_size=self.opts.x_size,
            y_size=self.opts.y_size,
            mines=self.opts.mines,
            per_cell=self.opts.per_cell,
            lives=self.opts.lives,
            first_success=self.opts.first_success,
        )
        self._send_callback_updates()

    def restart_game(self):
        """See AbstractController."""
        if not self.game.mf:
            return
        super().restart_game()
        self.game = Game(minefield=self.game.mf, lives=self.opts.lives)
        self._send_callback_updates()

    def select_cell(self, coord):
        """See AbstractController."""
        super().select_cell(coord)
        self.game.select_cell(coord)
        self._send_callback_updates()

    def flag_cell(self, coord, *, flag_only=False):
        """See AbstractController."""
        super().flag_cell(coord)

        cell_state = self.game.board[coord]
        if cell_state == CellUnclicked():
            self.game.set_cell_flags(coord, 1)
        elif isinstance(cell_state, CellFlag):
            if cell_state.num == self.opts.per_cell:
                if flag_only:
                    return
                self.game.set_cell_flags(coord, 0)
            else:
                self.game.set_cell_flags(coord, cell_state.num + 1)

        self._send_callback_updates()

    def remove_cell_flags(self, coord):
        """See AbstractController."""
        super().remove_cell_flags(coord)
        self.game.set_cell_flags(coord, 0)
        self._send_callback_updates()

    def chord_on_cell(self, coord):
        """See AbstractController."""
        super().chord_on_cell(coord)
        self.game.chord_on_cell(coord)
        self._send_callback_updates()

    def resize_board(self, *, x_size, y_size, mines):
        """See AbstractController."""
        super().resize_board(x_size, y_size, mines)

        logger.info(
            "Resizing board from %sx%s with %s mines to %sx%s with %s mines",
            self.opts.x_size,
            self.opts.y_size,
            self.opts.mines,
            x_size,
            y_size,
            mines,
        )
        self.opts.x_size, self.opts.y_size = x_size, y_size
        self.opts.mines = mines
        self.new_game()

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    def _send_callback_updates(self):
        """See AbstractController."""

        super()._send_callback_updates()

        update = SharedInfo(
            cell_updates={c: self.game.board[c] for c in self.game.board.all_coords},
            mines_remaining=self.game.mines_remaining,
            lives_remaining=self.game.lives_remaining,
            game_state=self.game.state,
        )
        if self.game.end_time:
            update.elapsed_time = self.game.end_time - self.game.start_time

        for cb in self._registered_callbacks:
            try:
                cb(update)
            except Exception as e:
                logger.error("Encountered an error sending an update: %s", e)
