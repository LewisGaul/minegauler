# October 2021, Lewis Gaul

__all__ = ("Controller",)

import sys

from .types import Coord


if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from ...shared.types import GameMode
from .. import api
from ..controller import ControllerBase
from .board import Board
from .game import Game


# TODO:
#  This whole module needs effectively rewriting from scratch, hasn't worked
#  since stuff was moved around.


class Controller(ControllerBase[Literal[GameMode.SPLIT_CELL]]):
    """Controller for a split-cells minesweeper game."""

    mode = GameMode.SPLIT_CELL
    board_cls = Board
    game_cls = Game

    @property
    def board(self) -> Board:
        return self._game.board

    def get_game_info(self) -> api.GameInfo:
        ret = api.GameInfo(
            game_state=self._game.state,
            x_size=self._game.x_size,
            y_size=self._game.y_size,
            mines=self._game.mines,
            difficulty=self._game.difficulty,
            per_cell=self._game.per_cell,
            first_success=self._game.first_success,
            minefield_known=self._game.minefield_known,
        )
        if self._game.state.started():
            ret.started_info = api.GameInfo.StartedInfo(
                start_time=self._game.start_time,
                elapsed=self._game.get_elapsed(),
                bbbv=None,
                rem_bbbv=None,
                bbbvps=None,
                prop_complete=None,
                prop_flagging=None,
            )
        return ret

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
