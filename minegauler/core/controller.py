# October 2021, Lewis Gaul

__all__ = ("ControllerBase", "SharedInfo")

import abc
from typing import Dict, Optional, Type

import attr

from ..shared import GameOptsStruct
from ..shared.types import CellContents, Coord_T, GameMode, GameState
from . import api
from .board import BoardBase
from .game import GameBase
from .minefield import MinefieldBase


@attr.attrs(auto_attribs=True, kw_only=True)
class SharedInfo:
    """
    Information to pass to frontends.

    Elements:
    cell_updates
        Dictionary of updates to cells, mapping the coordinate to the new
        contents of the cell.
    game_state
        The state of the game.
    mines_remaining
        The number of mines remaining to be found, given by
        [total mines] - [number of flags].
        Can be negative if there are too many flags.
    lives_remaining
        The number of lives remaining.
    """

    cell_updates: Optional[Dict[Coord_T, CellContents]] = None
    game_state: GameState = GameState.READY
    mines_remaining: int = 0
    lives_remaining: int = 0


class ControllerBase(api.AbstractController, metaclass=abc.ABCMeta):
    """Base controller class, generic over game mode."""

    switch_mode = None  # Remove abstractmethod

    mode: GameMode
    minefield_cls: Type[MinefieldBase]
    board_cls: Type[BoardBase]
    game_cls: Type[GameBase]

    def __init__(
        self, opts: GameOptsStruct, *, notif: api.AbstractListener,
    ):
        """
        :param opts:
            Game options.
        :param notif:
            A notifier defining callbacks.
        """
        super().__init__(opts)
        # Use a reference to the given opts rather than a copy.
        self._opts = opts
        self._notif = notif
        self.game = self.game_cls(
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._opts.mines,
            per_cell=self._opts.per_cell,
            lives=self._opts.lives,
            first_success=self._opts.first_success,
        )
        self._last_update = SharedInfo()
        self._send_updates()
        self._notif.set_mines(self._opts.mines)

    def get_game_info(self) -> api.GameInfo:
        """Get info about the current game."""
        ret = api.GameInfo(
            game_state=self.game.state,
            x_size=self.game.x_size,
            y_size=self.game.y_size,
            mines=self.game.mines,
            difficulty=self.game.difficulty,
            per_cell=self.game.per_cell,
            first_success=self.game.first_success,
            minefield_known=self.game.minefield_known,
        )
        if self.game.state.started():
            ret.started_info = api.GameInfo.StartedInfo(
                start_time=self.game.start_time,
                elapsed=self.game.get_elapsed(),
                bbbv=self.game.mf.bbbv,
                rem_bbbv=self.game.get_rem_3bv(),
                bbbvps=self.game.get_3bvps(),
                prop_complete=self.game.get_prop_complete(),
                prop_flagging=self.game.get_flag_proportion(),
            )
        return ret

    @property
    def board(self) -> BoardBase:
        return self.game.board

    def _send_updates(
        self, cells_updated: Optional[Dict[Coord_T, CellContents]] = None
    ) -> None:
        """Send updates to registered listeners."""
        update = SharedInfo(
            cell_updates=cells_updated,
            mines_remaining=self.game.mines_remaining,
            lives_remaining=self.game.lives_remaining,
            game_state=self.game.state,
        )

        # Send updates to registered listeners.
        if update.cell_updates:
            self._notif.update_cells(update.cell_updates)
        if update.mines_remaining != self._last_update.mines_remaining:
            self._notif.update_mines_remaining(update.mines_remaining)
        # if update.lives_remaining != self._last_update.lives_remaining:
        #     self._notif.update_lives_remaining(update.lives_remaining)
        if update.game_state is not self._last_update.game_state:
            self._notif.update_game_state(update.game_state)

        self._last_update = update
