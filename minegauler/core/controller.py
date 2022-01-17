# October 2021, Lewis Gaul

__all__ = ("ControllerBase", "GameControllerBase", "CreateControllerBase", "SharedInfo")

import abc
import json
import logging
import os.path
from os import PathLike
from typing import Dict, Optional, Type

import attr

from ..shared import GameOptsStruct
from ..shared.types import CellContents, Coord, Difficulty, GameMode, GameState
from . import api
from .board import BoardBase
from .game import GameBase
from .minefield import MinefieldBase


logger = logging.getLogger(__name__)


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

    cell_updates: Optional[Dict[Coord, CellContents]] = None
    game_state: GameState = GameState.READY
    mines_remaining: int = 0
    lives_remaining: int = 0


class ControllerBase(api.AbstractController, metaclass=abc.ABCMeta):
    """Base controller class, generic over game mode."""

    # Remove abstractmethods.
    switch_game_mode = None
    switch_ui_mode = None
    reset_settings = None

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

    def set_difficulty(self, difficulty: Difficulty) -> None:
        x, y, m = self.game_cls.difficulty_to_values(difficulty)
        self.resize_board(x, y, m)

    def resize_board(self, x_size: int, y_size: int, mines: int) -> None:
        """See AbstractController."""
        super().resize_board(x_size=x_size, y_size=y_size, mines=mines)
        if (
            x_size == self._opts.x_size
            and y_size == self._opts.y_size
            and mines == self._opts.mines
        ):
            logger.info(
                "No resize required as the parameters are unchanged, starting a new game"
            )
            self.new_game()
        else:
            logger.info(
                "Resizing board from %sx%s with %s mines to %sx%s with %s mines",
                self._opts.x_size,
                self._opts.y_size,
                self._opts.mines,
                x_size,
                y_size,
                mines,
            )
            self._opts.x_size = x_size
            self._opts.y_size = y_size
            self._opts.mines = mines
            self._notif.resize_minefield(x_size, y_size)
            self._notif.set_mines(mines)
            self.new_game()
            self._notif.set_difficulty(
                self.game_cls.difficulty_from_values(x_size, y_size, mines)
            )

    @staticmethod
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
            json.dump(mf.to_json(), f)


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
        # self._send_updates()
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
        if not self.game.mf.populated:
            return
        super().restart_game()
        self.game = self.game_cls.from_minefield(
            self.game.mf,
            lives=self._opts.lives,
        )
        self._send_reset_update()

    def select_cell(self, coord: Coord) -> None:
        """See AbstractController."""
        super().select_cell(coord)
        cells = self.game.select_cell(coord)
        self._send_updates(cells)

    def chord_on_cell(self, coord: Coord) -> None:
        """See AbstractController."""
        super().chord_on_cell(coord)
        cells = self.game.chord_on_cell(coord)
        self._send_updates(cells)

    def remove_cell_flags(self, coord: Coord) -> None:
        """See AbstractController."""
        super().remove_cell_flags(coord)
        self.game.set_cell_flags(coord, 0)
        self._send_updates({coord: self.board[coord]})

    def set_first_success(self, value: bool) -> None:
        """
        Set whether the first click should be a guaranteed success.
        """
        super().set_first_success(value)
        self._opts.first_success = value
        if not self.game.state.started():
            self.game.first_success = value

    def set_per_cell(self, value: int) -> None:
        """
        Set the maximum number of mines per cell.
        """
        super().set_per_cell(value)
        if value < 1:
            raise ValueError(
                f"Max number of mines per cell must be at least 1, got {value}"
            )
        self._opts.per_cell = value
        # If the game is not started and the minefield is not known then the
        # new per-cell value should be picked up immediately, and the board
        # cleared of any flags (e.g. 3-flag cells may no longer be allowed!).
        if not (self.game.state.started() or self.game.minefield_known):
            self.new_game()

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
        self._save_minefield(self.game.mf, file)

    def load_minefield(self, file: PathLike) -> None:
        """Load a minefield from file."""
        with open(file) as f:
            mf = self.minefield_cls.from_json(json.load(f))

        logger.debug(
            "Loaded minefield from file (%d x %d, %d mines)",
            mf.x_size,
            mf.y_size,
            mf.mines,
        )
        self.resize_board(mf.x_size, mf.y_size, mf.mines)
        self.game = self.game_cls.from_minefield(mf, lives=self._opts.lives)

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    def _send_updates(
        self, cells_updated: Optional[Dict[Coord, CellContents]] = None
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


class CreateControllerBase(ControllerBase, metaclass=abc.ABCMeta):
    """Base create controller class, generic over game mode."""

    # Remove abstractmethod - always handled by game controller.
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

    @abc.abstractmethod
    def _make_board(self) -> BoardBase:
        raise NotImplementedError

    @property
    def board(self) -> BoardBase:
        return self._board

    @property
    def difficulty(self) -> Difficulty:
        return self.game_cls.difficulty_from_values(
            self._opts.x_size, self._opts.y_size, self._flags
        )

    def get_game_info(self) -> api.GameInfo:
        return api.GameInfo(
            game_state=GameState.ACTIVE,
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._flags,
            difficulty=self.difficulty,
            per_cell=self._opts.per_cell,
            first_success=self._opts.first_success,
            mode=self.mode,
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

    def chord_on_cell(self, coord: Coord) -> None:
        super().chord_on_cell(coord)

    def remove_cell_flags(self, coord: Coord) -> None:
        super().remove_cell_flags(coord)
        cell = self.board[coord]
        if not isinstance(cell, CellContents.Mine):
            return
        self.board[coord] = CellContents.Unclicked
        self._flags -= cell.num
        self._notif.update_cells({coord: self.board[coord]})
        self._notif.update_mines_remaining(self._flags)

    def set_first_success(self, value: bool) -> None:
        super().set_first_success(value)
        self._opts.first_success = value

    def set_per_cell(self, value: int) -> None:
        super().set_per_cell(value)
        self._opts.per_cell = value

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
            self.board.all_underlying_coords,
            mine_coords=coords,
            per_cell=self._opts.per_cell,
        )
        self._save_minefield(mf, file)
