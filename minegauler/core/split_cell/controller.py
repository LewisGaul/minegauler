# October 2021, Lewis Gaul

__all__ = ("CreateController", "GameController")

import logging

from ...shared.types import CellContents, GameMode
from ..controller import CreateControllerBase, GameControllerBase
from .board import Board
from .game import Game
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


class _ControllerMixin:
    """Mixin for the controller classes."""

    mode = GameMode.SPLIT_CELL
    minefield_cls = Minefield
    board_cls = Board
    game_cls = Game

    @property
    def board(self) -> Board:
        return super().board


class GameController(_ControllerMixin, GameControllerBase):
    """GameController for a split-cells minesweeper game."""

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        super().flag_cell(coord, flag_only=flag_only)
        if not coord.is_split:
            return
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

    def remove_cell_flags(self, coord: Coord) -> None:
        if not coord.is_split:
            return
        super().remove_cell_flags(coord)

    def split_cell(self, coord: Coord) -> None:
        if coord.is_split:
            return
        updates = self.game.split_cell(coord)
        self._send_updates(updates)


class CreateController(_ControllerMixin, CreateControllerBase):
    """A controller for creating split-cell boards."""

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
        if isinstance(cell, CellContents.Num):
            self.board[coord] = CellContents.Unclicked
            self._notif.update_cells({coord: self.board[coord]})
        elif coord.is_split:
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
            else:
                return
            self._notif.update_cells({coord: self.board[coord]})
            self._notif.update_mines_remaining(self._flags)

    def split_cell(self, coord: Coord) -> None:
        if coord.is_split or self.board[coord] is not CellContents.Unclicked:
            return
        small_coords = coord.split()
        self.board.split_coord(coord)
        self._notif.update_cells({c: self.board[c] for c in small_coords})
