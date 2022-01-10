# November 2018, Lewis Gaul

"""
The core game engine.

"""

__all__ = ("UberController",)

import logging
import sys
from typing import Mapping, Type


if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from ..shared.types import Coord, Difficulty, GameMode, PathLike, UIMode
from ..shared.utils import GameOptsStruct
from . import api, board, controller, game, minefield, regular, split_cell
from .board import BoardBase
from .controller import ControllerBase


logger = logging.getLogger(__name__)


class GameModeImplementation(Protocol):
    """Protocol for game mode implementations to satisfy."""

    Minefield: Type[minefield.MinefieldBase]
    Board: Type[board.BoardBase]
    Game: Type[game.GameBase]
    GameController: Type[controller.ControllerBase]
    CreateController: Type[controller.ControllerBase]
    mode: GameMode


GAME_MODE_IMPL: Mapping[GameMode, GameModeImplementation] = {
    GameMode.REGULAR: regular,
    GameMode.SPLIT_CELL: split_cell,
}


class UberController(api.AbstractController):
    """Base controller implementing all user interaction methods."""

    def __init__(self, opts: GameOptsStruct):
        super().__init__(opts)
        self._ui_mode: UIMode = UIMode.GAME
        self._opts.mode = GameMode.REGULAR
        self._active_ctrlr: ControllerBase = self._get_ctrlr_cls(
            self.mode, self._ui_mode
        )(self._opts, notif=self._notif)

    @property
    def mode(self) -> GameMode:
        return self._opts.mode

    @staticmethod
    def _get_ctrlr_cls(game_mode: GameMode, ui_mode: UIMode) -> Type[ControllerBase]:
        """Get the controller class for given modes."""
        if ui_mode is UIMode.GAME:
            return GAME_MODE_IMPL[game_mode].GameController
        elif ui_mode is UIMode.CREATE:
            return GAME_MODE_IMPL[game_mode].CreateController
        else:
            raise ValueError(f"Unsupported UI mode {ui_mode}")

    def switch_game_mode(self, mode: GameMode) -> None:
        """Switch the game mode."""
        super().switch_game_mode(mode)
        if mode is self.mode:
            logger.debug(
                "Ignore switch game mode request because mode is already %s", mode
            )
            return
        self._opts.mode = mode
        self._active_ctrlr = self._get_ctrlr_cls(mode, self._ui_mode)(
            self._opts, notif=self._notif
        )
        self._notif.reset()

    def switch_ui_mode(self, ui_mode: UIMode) -> None:
        """Switch the UI mode."""
        super().switch_ui_mode(ui_mode)
        if ui_mode is self._ui_mode:
            logger.debug(
                "Ignore switch UI mode request because mode is already %s", ui_mode
            )
            return
        self._ui_mode = ui_mode
        self._active_ctrlr = self._get_ctrlr_cls(self.mode, ui_mode)(
            self._opts, notif=self._notif
        )
        self._notif.reset()

    def reset_settings(self) -> None:
        super().reset_settings()
        self._opts = GameOptsStruct()
        self.switch_ui_mode(UIMode.GAME)
        self.resize_board(self._opts.x_size, self._opts.y_size, self._opts.mines)
        self._notif.reset()

    def load_minefield(self, file: PathLike) -> None:
        """
        Load a minefield from file.

        :param file:
            The location of the file to load from.
        """
        if self._ui_mode is UIMode.CREATE:
            self.switch_ui_mode(UIMode.GAME)
            self._notif.ui_mode_changed(UIMode.GAME)
        self._active_ctrlr.load_minefield(file)

    # ----------------------------------
    # Delegated abstractmethods
    # ----------------------------------
    @property
    def board(self) -> BoardBase:
        return self._active_ctrlr.board

    def get_game_info(self) -> api.GameInfo:
        return self._active_ctrlr.get_game_info()

    def new_game(self) -> None:
        self._active_ctrlr.new_game()

    def restart_game(self) -> None:
        self._active_ctrlr.restart_game()

    def select_cell(self, coord: Coord) -> None:
        self._active_ctrlr.select_cell(coord)

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        self._active_ctrlr.flag_cell(coord, flag_only=flag_only)

    def chord_on_cell(self, coord: Coord) -> None:
        self._active_ctrlr.chord_on_cell(coord)

    def remove_cell_flags(self, coord: Coord) -> None:
        self._active_ctrlr.remove_cell_flags(coord)

    def resize_board(self, x_size: int, y_size: int, mines: int) -> None:
        self._active_ctrlr.resize_board(x_size, y_size, mines)

    def set_difficulty(self, difficulty: Difficulty) -> None:
        self._active_ctrlr.set_difficulty(difficulty)

    def set_first_success(self, value: bool) -> None:
        self._active_ctrlr.set_first_success(value)

    def set_per_cell(self, value: int) -> None:
        self._active_ctrlr.set_per_cell(value)

    def save_current_minefield(self, file: PathLike) -> None:
        self._active_ctrlr.save_current_minefield(file)

    # TODO: Should this be deleted in favour of using flag_cell()?
    # def split_cell(self, coord: Coord) -> None:
    #     # TODO: Check the sub controller can do this...
    #     self._active_ctrlr.split_cell(coord)
