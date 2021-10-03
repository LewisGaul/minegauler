# October 2021, Lewis Gaul

__all__ = ("Controller",)

from ...shared.types import GameMode
from ..controller import ControllerBase
from .board import Board
from .game import Game
from .minefield import Minefield
from .types import Coord


class Controller(ControllerBase):
    """Controller for a split-cells minesweeper game."""

    mode = GameMode.SPLIT_CELL
    minefield_cls = Minefield
    board_cls = Board
    game_cls = Game

    def split_cell(self, coord: Coord) -> None:
        if coord.is_split:
            return
        self._send_updates(self._game.split_cell(coord))

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        if not coord.is_split:
            return
        super().flag_cell(coord, flag_only=flag_only)

    def remove_cell_flags(self, coord: Coord) -> None:
        if not coord.is_split:
            return
        super().remove_cell_flags(coord)
