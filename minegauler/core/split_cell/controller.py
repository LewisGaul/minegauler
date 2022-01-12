# October 2021, Lewis Gaul

__all__ = ("GameController",)

import logging

from ...shared.types import CellContents, Difficulty, GameMode, PathLike
from ..controller import GameControllerBase
from .board import Board
from .game import Game, difficulty_to_values
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


class _ControllerMixin:
    """Mixin for the controller classes."""

    mode = GameMode.REGULAR
    minefield_cls = Minefield
    board_cls = Board
    game_cls = Game

    def set_difficulty(self, difficulty: Difficulty) -> None:
        x, y, m = difficulty_to_values(difficulty)
        self.resize_board(x, y, m)


class GameController(_ControllerMixin, GameControllerBase):
    """GameController for a split-cells minesweeper game."""

    mode = GameMode.SPLIT_CELL
    minefield_cls = Minefield
    board_cls = Board
    game_cls = Game

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def select_cell(self, coord: Coord) -> None:
        super().select_cell(coord)
        cells = self.game.select_cell(coord)
        self._send_updates(cells)

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        super().flag_cell(coord, flag_only=flag_only)
        if coord.is_split:
            cell_state = self.board[coord]
            if cell_state is CellContents.Unclicked:
                self.game.set_cell_flags(coord, 1)
            elif isinstance(cell_state, CellContents.Flag):
                if cell_state.num >= self.game.per_cell:
                    if flag_only:
                        return
                    self.game.set_cell_flags(coord, 0)
                else:
                    self.game.set_cell_flags(coord, cell_state.num + 1)

            updates = {coord: self.board[coord]}
        else:
            updates = self.game.split_cell(coord)
        self._send_updates(updates)

    def remove_cell_flags(self, coord: Coord) -> None:
        if not coord.is_split:
            return
        super().remove_cell_flags(coord)

    def chord_on_cell(self, coord: Coord) -> None:
        pass

    def load_minefield(self, file: PathLike) -> None:
        pass
