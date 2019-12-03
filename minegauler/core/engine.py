"""
engine.py - The core game logic

November 2018, Lewis Gaul

Exports:
Controller (class)
    Implementation of game logic and provision of functions to be called by a
    frontend implementation.
"""

__all__ = ("BaseController",)

import logging
from typing import Callable, Dict, Optional

import attr

from ..types import CellContentsType, CellFlag, CellUnclicked, GameState, UIMode
from ..typing import Coord_T
from . import api, board, create, game, utils


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


class BaseController(api.AbstractController):
    """Base controller implementing all user interaction methods."""

    def __init__(
        self, opts: utils.GameOptsStruct, *, notif: Optional[api.Caller] = None
    ):
        super().__init__(opts, notif=notif)
        self._active_ctrlr: api.AbstractController = _GameController(
            self.opts, notif=self._notif
        )

        # Do the method wrapping here because we need the registered controller.
        for method in api.AbstractController.__abstractmethods__:
            if not isinstance(getattr(type(self), method), property):
                setattr(self, method, self._call_active_ctrlr(method))

    def _call_active_ctrlr(self, func: str) -> Callable:
        """
        Decorator to call the active controller.

        :param func:
            The name of the method to decorate.
        :return:
            The decorated version of the method.
        """
        if not hasattr(self, func + "_orig"):
            setattr(self, func + "_orig", getattr(self, func))

        def wrapped(*args, **kwargs):
            getattr(self, func + "_orig")(*args, **kwargs)
            return getattr(self._active_ctrlr, func)(*args, **kwargs)

        return wrapped

    def switch_mode(self, mode: UIMode) -> None:
        """Switch the mode of the UI, e.g. into 'create' mode."""
        super().switch_mode(mode)
        if mode is UIMode.GAME:
            self._active_ctrlr = _GameController(self.opts, notif=self._notif)
        elif mode is UIMode.CREATE:
            self._active_ctrlr = create.CreateController(self.opts, notif=self._notif)
        else:
            raise ValueError(f"Unrecognised UI mode: {mode}")

    # ----------------------------------
    # Implement abstractmethods
    # ----------------------------------
    @property
    def board(self) -> board.Board:
        return self._active_ctrlr.board

    def new_game(self) -> None:
        pass

    def restart_game(self) -> None:
        pass

    def select_cell(self, coord: Coord_T) -> None:
        pass

    def flag_cell(self, coord: Coord_T, *, flag_only: bool = False) -> None:
        pass

    def chord_on_cell(self, coord: Coord_T) -> None:
        pass

    def remove_cell_flags(self, coord: Coord_T) -> None:
        pass

    def resize_board(self, *, x_size: int, y_size: int, mines: int) -> None:
        self.opts.x_size = x_size
        self.opts.y_size = y_size
        self.opts.mines = mines

    def set_first_success(self, value: bool) -> None:
        self.opts.first_success = value

    def set_per_cell(self, value: int) -> None:
        self.opts.per_cell = value


class _GameController(api.AbstractController):
    """
    Class for processing all game logic. Implements functions defined in
    AbstractController that are called from UI.
    
    Attributes:
    opts (GameOptsStruct)
        Options for use in games.
    """

    def __init__(
        self, opts: utils.GameOptsStruct, *, notif: Optional[api.Caller] = None
    ):
        """
        Arguments:
        opts (GameOptsStruct)
            Object containing the required game options as attributes.
        """
        super().__init__(opts, notif=notif)

        self._game: Optional[game.Game] = None
        self._last_update: SharedInfo

        self._notif.set_mines(self.opts.mines)
        self.new_game()

    @property
    def board(self) -> board.Board:
        return self._game.board

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def new_game(self) -> None:
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
        self._send_reset_update()

    def restart_game(self) -> None:
        """See AbstractController."""
        if not self._game.mf:
            return
        super().restart_game()
        self._game = game.Game(minefield=self._game.mf, lives=self.opts.lives)
        self._send_reset_update()

    def select_cell(self, coord: Coord_T) -> None:
        """See AbstractController."""
        super().select_cell(coord)
        cells = self._game.select_cell(coord)
        self._send_updates(cells)

    def flag_cell(self, coord: Coord_T, *, flag_only: bool = False) -> None:
        """See AbstractController."""
        super().flag_cell(coord)

        cell_state = self._game.board[coord]
        if cell_state is CellUnclicked():
            self._game.set_cell_flags(coord, 1)
        elif isinstance(cell_state, CellFlag):
            if cell_state.num == self.opts.per_cell:
                if flag_only:
                    return
                self._game.set_cell_flags(coord, 0)
            else:
                self._game.set_cell_flags(coord, cell_state.num + 1)

        self._send_updates({coord: self._game.board[coord]})

    def remove_cell_flags(self, coord: Coord_T) -> None:
        """See AbstractController."""
        super().remove_cell_flags(coord)
        self._game.set_cell_flags(coord, 0)
        self._send_updates({coord: self._game.board[coord]})

    def chord_on_cell(self, coord: Coord_T) -> None:
        """See AbstractController."""
        super().chord_on_cell(coord)
        cells = self._game.chord_on_cell(coord)
        self._send_updates(cells)

    def resize_board(self, *, x_size: int, y_size: int, mines: int) -> None:
        """See AbstractController."""
        super().resize_board(x_size=x_size, y_size=y_size, mines=mines)
        if (
            x_size == self.opts.x_size
            and y_size == self.opts.y_size
            and mines == self.opts.mines
        ):
            logger.info(
                "No resize required as the parameters are unchanged, starting a new game"
            )
            self.new_game()
            return

        logger.info(
            "Resizing board from %sx%s with %s mines to %sx%s with %s mines",
            self.opts.x_size,
            self.opts.y_size,
            self.opts.mines,
            x_size,
            y_size,
            mines,
        )
        self.opts.x_size = x_size
        self.opts.y_size = y_size
        self.opts.mines = mines
        self._send_resize_update()
        self.new_game()

    def set_first_success(self, value: bool) -> None:
        """
        Set whether the first click should be a guaranteed success.
        """
        super().set_first_success(value)
        self.opts.first_success = value

    def set_per_cell(self, value: int) -> None:
        """
        Set the maximum number of mines per cell.
        """
        super().set_per_cell(value)
        if self.opts.per_cell != value:
            self.opts.per_cell = value
            if self._game.state.unstarted():
                self.new_game()

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    def _send_reset_update(self) -> None:
        self._notif.reset()
        self._last_update = SharedInfo()
        self._cells_updated = dict()

    def _send_resize_update(self) -> None:
        self._notif.resize(self.opts.x_size, self.opts.y_size)
        self._notif.set_mines(self.opts.mines)

    def _send_updates(self, cells_updated: Dict[Coord_T, CellContentsType]) -> None:
        """Send updates to registered listeners."""
        update = SharedInfo(
            cell_updates=cells_updated,
            mines_remaining=self._game.mines_remaining,
            lives_remaining=self._game.lives_remaining,
            game_state=self._game.state,
            finish_time=self._game.get_elapsed() if self._game.is_finished() else None,
        )

        if update.cell_updates:
            self._notif.update_cells(update.cell_updates)
        if update.mines_remaining != self._last_update.mines_remaining:
            self._notif.update_mines_remaining(update.mines_remaining)
        # if update.lives_remaining != self._last_update.lives_remaining:
        #     self._notif.update_lives_remaining(update.lives_remaining)
        if update.game_state is not self._last_update.game_state:
            self._notif.update_game_state(update.game_state)
        if (
            update.finish_time is not None
            and update.finish_time != self._last_update.finish_time
        ):
            self._notif.set_finish_time(update.finish_time)

        self._last_update = update
