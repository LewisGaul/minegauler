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
from typing import Dict, Optional

import attr

from minegauler.typing import Coord_T

from ..types import *
from . import game, utils
from .api import AbstractController


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

    cell_updates: Dict[Coord_T, CellContentsType] = attr.Factory(dict)
    game_state: GameState = GameState.READY
    mines_remaining: int = 0
    lives_remaining: int = 0
    finish_time: Optional[float] = None


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

        self.opts = utils.GameOptsStruct._from_struct(opts)
        self._game: Optional[game.Game] = None
        self._last_update: SharedInfo = SharedInfo()

        self.new_game()

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def new_game(self):
        """See AbstractController."""
        super().new_game()
        self._game = game.Game(
            x_size=self.opts.x_size,
            y_size=self.opts.y_size,
            mines=self.opts.mines,
            per_cell=self.opts.per_cell,
            lives=self.opts.lives,
            first_success=self.opts.first_success,
        )
        self._notif.reset()
        self._last_update = SharedInfo()

    def restart_game(self):
        """See AbstractController."""
        if not self._game.mf:
            return
        super().restart_game()
        self._game = game.Game(minefield=self._game.mf, lives=self.opts.lives)
        self._notif.reset()
        self._last_update = SharedInfo()

    def select_cell(self, coord):
        """See AbstractController."""
        super().select_cell(coord)
        self._game.select_cell(coord)
        self._send_updates()

    def flag_cell(self, coord, *, flag_only=False):
        """See AbstractController."""
        super().flag_cell(coord)

        cell_state = self._game.board[coord]
        if cell_state == CellUnclicked():
            self._game.set_cell_flags(coord, 1)
        elif isinstance(cell_state, CellFlag):
            if cell_state.num == self.opts.per_cell:
                if flag_only:
                    return
                self._game.set_cell_flags(coord, 0)
            else:
                self._game.set_cell_flags(coord, cell_state.num + 1)

        self._send_updates()

    def remove_cell_flags(self, coord):
        """See AbstractController."""
        super().remove_cell_flags(coord)
        self._game.set_cell_flags(coord, 0)
        self._send_updates()

    def chord_on_cell(self, coord):
        """See AbstractController."""
        super().chord_on_cell(coord)
        self._game.chord_on_cell(coord)
        self._send_updates()

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
    def _send_updates(self):
        """See AbstractController."""
        update = SharedInfo(
            cell_updates={c: self._game.board[c] for c in self._game.board.all_coords},
            mines_remaining=self._game.mines_remaining,
            lives_remaining=self._game.lives_remaining,
            game_state=self._game.state,
            finish_time=self._game.get_elapsed() if self._game.is_finished() else None,
        )

        # TODO: Only if there are some cell updates.
        self._notif.update_cells(update.cell_updates)
        if update.mines_remaining != self._last_update.mines_remaining:
            self._notif.update_mines_remaining(update.mines_remaining)
        # if update.lives_remaining != self._last_update.lives_remaining:
        #     self._notif.update_lives_remaining(update.lives_remaining)
        if update.game_state != self._last_update.game_state:
            self._notif.update_game_state(update.game_state)
        if (
            update.finish_time is not None
            and update.finish_time != self._last_update.finish_time
        ):
            self._notif.set_finish_time(update.finish_time)

        self._last_update = update
