# October 2021, Lewis Gaul

__all__ = ("ControllerBase", "GameControllerBase", "CreateControllerBase", "SharedInfo")

import abc
import json
import logging
import os.path
from os import PathLike
from typing import Dict, Optional, Type

import attr

from .. import api
from ..shared import GameOptsStruct
from ..shared.types import CellContents, Coord_T, Difficulty, GameMode, GameState
from .board import BoardBase
from .game import GameBase
from .minefield import MinefieldBase


logger = logging.getLogger(__name__)


def _save_minefield(mf: MinefieldBase, file: PathLike) -> None:
    """
    Save a minefield to file.

    :param mf:
        The minefield to save.
    :param file:
        The path of the file to save at.
    :raises OSError:
        If saving to file fails.
    """
    if os.path.isfile(file):
        logger.warning("Overwriting file at %s", file)
    with open(file, "w") as f:
        json.dump(mf.to_json(), f)  # TODO


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

    # Remove abstractmethods.
    switch_game_mode = None
    switch_ui_mode = None

    mode: GameMode
    minefield_cls: Type[MinefieldBase]
    board_cls: Type[BoardBase]
    game_cls: Type[GameBase]

    def __init__(
        self,
        opts: GameOptsStruct,
        *,
        notif: api.AbstractListener,
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

    @property
    @abc.abstractmethod
    def difficulty(self) -> Difficulty:
        raise NotImplementedError


class GameControllerBase(ControllerBase, metaclass=abc.ABCMeta):
    """Base game controller class, generic over game mode."""

    def __init__(
        self,
        opts: GameOptsStruct,
        *,
        notif: api.AbstractListener,
    ):
        """
        :param opts:
            Game options.
        :param notif:
            A notifier defining callbacks.
        """
        super().__init__(opts, notif=notif)
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

    @property
    def difficulty(self) -> Difficulty:
        return self.game.difficulty

    @property
    def board(self) -> BoardBase:
        return self.game.board

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
            mode=self.mode,
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

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def new_game(self) -> None:
        """See AbstractController."""
        super().new_game()
        if self._opts.mines > self._opts.per_cell * (
            self._opts.x_size * self._opts.y_size - 1
        ):
            # This is needed since it's possible to create a board with more
            # mines than is normally allowed.
            logger.debug(
                "Reducing number of mines from %d to %d because they don't fit",
                self._opts.mines,
                self._opts.x_size * self._opts.y_size - 1,
            )
            self._opts.mines = self._opts.x_size * self._opts.y_size - 1
            self._notif.set_mines(self._opts.mines)
        self.game = self.game_cls(
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._opts.mines,
            per_cell=self._opts.per_cell,
            lives=self._opts.lives,
            first_success=self._opts.first_success,
        )
        self._send_reset_update()

    def restart_game(self) -> None:
        """See AbstractController."""
        if not self.game.mf:
            return
        super().restart_game()
        self.game = self.game_cls.from_minefield(
            self.game.mf,
            x_size=self.game.x_size,
            y_size=self.game.y_size,
            lives=self._opts.lives,
        )
        self._send_reset_update()

    def save_current_minefield(self, file: PathLike) -> None:
        """
        Save the current minefield to file.

        :param file:
            The location of the file to save to. Should have the extension
            ".mgb".
        :raises RuntimeError:
            If the game is not finished.
        :raises OSError:
            If saving to file fails.
        """
        super().save_current_minefield(file)
        if not self.game.state.finished():
            raise RuntimeError("Can only save minefields when the game is completed")
        _save_minefield(self.game.mf, file)

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
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

    def _send_reset_update(self) -> None:
        """Send an update to reset the board."""
        self._notif.reset()
        self._send_updates()

    def _send_resize_update(self) -> None:
        """Send an update to change the dimensions and number of mines."""
        self._notif.resize_minefield(self._opts.x_size, self._opts.y_size)
        self._notif.set_mines(self._opts.mines)
        self._send_updates()


class CreateControllerBase(ControllerBase, metaclass=abc.ABCMeta):
    """Base create controller class, generic over game mode."""

    # Remove abstractmethod.
    load_minefield = None

    def __init__(
        self,
        opts: GameOptsStruct,
        *,
        notif: api.AbstractListener,
    ):
        """
        :param opts:
            Game options.
        :param notif:
            A notifier defining callbacks.
        """
        super().__init__(opts, notif=notif)
        self._board: BoardBase = self._make_board()
        self._flags: int = 0
        self._notif.set_mines(self._flags)

    @property
    def board(self) -> BoardBase:
        return self._board

    @abc.abstractmethod
    def _make_board(self) -> BoardBase:
        raise NotImplementedError

    def get_game_info(self) -> api.GameInfo:
        return api.GameInfo(
            game_state=GameState.ACTIVE,
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._flags,
            difficulty=self.difficulty,
            per_cell=self._opts.per_cell,
            first_success=self._opts.first_success,
            minefield_known=True,
        )

    def new_game(self) -> None:
        """See AbstractController."""
        super().new_game()
        self._board = self._make_board()
        self._flags = 0
        self._notif.reset()

    def restart_game(self) -> None:
        """See AbstractController."""
        super().restart_game()
        self.new_game()

    def save_current_minefield(self, file: PathLike) -> None:
        """
        Save the current created minefield to file.

        :param file:
            The location of the file to save to. Should have the extension
            ".mgb".
        :raises OSError:
            If saving to file fails.
        """
        super().save_current_minefield(file)
        coords = []
        for c in self.board.all_coords:
            if type(self.board[c]) is CellContents.Mine:
                coords.extend([c] * self.board[c].num)
        mf = self.minefield_cls.from_coords(
            self.board.all_coords, mine_coords=coords, per_cell=self._opts.per_cell
        )
        _save_minefield(mf, file)
