# November 2018, Lewis Gaul

"""
The core game engine.

"""

__all__ = ("UberController",)

import logging
from typing import Any, Mapping

from ..shared.types import Coord_T, GameMode, PathLike, SplitCellCoord, UIMode
from ..shared.utils import GameOptsStruct
from . import api, regular, split_cells
from .board import BoardBase
from .controller import ControllerBase


logger = logging.getLogger(__name__)


GAME_MODE_IMPL: Mapping[GameMode, Any] = {
    GameMode.REGULAR: regular,
    GameMode.SPLIT_CELL: split_cells,
}


class UberController(api.AbstractController):
    """Base controller implementing all user interaction methods."""

    def __init__(self, opts: GameOptsStruct):
        super().__init__(opts)
        # TODO: Get mode from opts.
        self._mode = GameMode.REGULAR
        # self._mode = UIMode.SPLIT_CELL
        self._active_ctrlr: ControllerBase = GAME_MODE_IMPL[self._mode].Controller(
            self._opts, notif=self._notif
        )

    def switch_mode(self, mode: GameMode) -> None:
        """Switch the game mode."""
        super().switch_mode(mode)
        if mode is self._mode:
            logger.debug("Ignore switch mode request because mode is already %s", mode)
            return
        self._active_ctrlr = GAME_MODE_IMPL[mode].Controller(
            self._opts, notif=self._notif
        )
        self._mode = mode
        self._notif.reset()

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

    def select_cell(self, coord: Coord_T) -> None:
        self._active_ctrlr.select_cell(coord)

    def flag_cell(self, coord: Coord_T, *, flag_only: bool = False) -> None:
        self._active_ctrlr.flag_cell(coord, flag_only=flag_only)

    def chord_on_cell(self, coord: Coord_T) -> None:
        self._active_ctrlr.chord_on_cell(coord)

    def remove_cell_flags(self, coord: Coord_T) -> None:
        self._active_ctrlr.remove_cell_flags(coord)

    def resize_board(self, x_size: int, y_size: int, mines: int) -> None:
        self._active_ctrlr.resize_board(x_size, y_size, mines)

    def set_first_success(self, value: bool) -> None:
        self._active_ctrlr.set_first_success(value)

    def set_per_cell(self, value: int) -> None:
        self._active_ctrlr.set_per_cell(value)

    def save_current_minefield(self, file: PathLike) -> None:
        self._active_ctrlr.save_current_minefield(file)

    def load_minefield(self, file: PathLike) -> None:
        """
        Load a minefield from file.

        :param file:
            The location of the file to load from. Should have the extension
            ".mgb".
        """
        if self._opts.mode is UIMode.CREATE:
            self.switch_mode(UIMode.GAME)
            self._notif.ui_mode_changed(UIMode.GAME)
        self._active_ctrlr.load_minefield(file)

    def split_cell(self, coord: SplitCellCoord) -> None:
        # TODO: Check the sub controller can do this...
        self._active_ctrlr.split_cell(coord)
