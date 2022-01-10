# October 2021, Lewis Gaul

__all__ = ("GameController",)

from ...shared.types import Difficulty, GameMode, PathLike
from ..controller import GameControllerBase
from .board import Board
from .game import Game, difficulty_to_values
from .minefield import Minefield
from .types import Coord


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

    # TODO: Remove this in favour of using 'flag_cell()'?
    def split_cell(self, coord: Coord) -> None:
        if coord.is_split:
            return
        self._send_updates(self.game.split_cell(coord))

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        if not coord.is_split:
            return
        super().flag_cell(coord, flag_only=flag_only)

    def remove_cell_flags(self, coord: Coord) -> None:
        if not coord.is_split:
            return
        super().remove_cell_flags(coord)

    def chord_on_cell(self, coord: Coord) -> None:
        pass

    def resize_board(self, x_size: int, y_size: int, mines: int) -> None:
        pass

    def set_first_success(self, value: bool) -> None:
        pass

    def set_per_cell(self, value: int) -> None:
        pass

    def load_minefield(self, file: PathLike) -> None:
        pass
