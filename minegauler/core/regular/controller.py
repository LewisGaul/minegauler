# October 2021, Lewis Gaul

__all__ = ("GameController", "CreateController")

import json
import logging

from ...shared.types import CellContents, Difficulty, GameMode, PathLike
from ..controller import CreateControllerBase, GameControllerBase
from .board import Board
from .game import Game, difficulty_from_values, difficulty_to_values
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


class _ControllerMixin:
    """Mixin for the controller classes."""

    mode = GameMode.REGULAR
    minefield_cls = Minefield
    board_cls = Board
    game_cls = Game

    @property
    def board(self) -> Board:
        return super().board

    def set_difficulty(self, difficulty: Difficulty) -> None:
        x, y, m = difficulty_to_values(difficulty)
        self.resize_board(x, y, m)


class GameController(_ControllerMixin, GameControllerBase):
    """GameController for a regular minesweeper game."""

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        """See AbstractController."""
        super().flag_cell(coord, flag_only=flag_only)

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

        self._send_updates({coord: self.board[coord]})


class CreateController(_ControllerMixin, CreateControllerBase):
    """A controller for creating boards."""

    @property
    def difficulty(self) -> Difficulty:
        return difficulty_from_values(self._opts.x_size, self._opts.y_size, self._flags)

    def _make_board(self) -> Board:
        return Board(self._opts.x_size, self._opts.y_size)

    def select_cell(self, coord: Coord) -> None:
        super().select_cell(coord)
        if self.board[coord] is CellContents.Unclicked:
            self.board[coord] = CellContents.Num(0)
        elif isinstance(self.board[coord], CellContents.Num):
            self.board[coord] += 1
        else:
            return
        self._notif.update_cells({coord: self.board[coord]})

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        super().flag_cell(coord)
        cell = self.board[coord]

        if cell is CellContents.Unclicked:
            self.board[coord] = CellContents.Mine(1)
            self._flags += 1
        elif isinstance(cell, CellContents.Mine):
            if cell.num == self._opts.per_cell:
                if flag_only:
                    return
                self.board[coord] = CellContents.Unclicked
                self._flags -= self._opts.per_cell
            else:
                self.board[coord] += 1
                self._flags += 1
        elif isinstance(cell, CellContents.Num):
            self.board[coord] = CellContents.Unclicked
        else:
            return
        self._notif.update_cells({coord: self.board[coord]})
        self._notif.update_mines_remaining(self._flags)
