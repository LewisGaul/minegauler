"""
create.py - Logic for creating custom boards

December 2019, Lewis Gaul
"""

__all__ = ("CreateController",)

import logging
from typing import Optional

from ..types import CellMine, CellNum, CellUnclicked
from ..typing import Coord_T
from . import api, board, utils


logger = logging.getLogger(__name__)


class CreateController(api.AbstractController):
    """A controller for creating boards."""

    def __init__(
        self, opts: utils.GameOptsStruct, *, notif: Optional[api.Caller] = None
    ):
        super().__init__(opts, notif=notif)
        self._board: board.Board
        self._flags: int = 0
        self._notif.set_mines(self._flags)
        self.new_game()

    @property
    def board(self) -> board.Board:
        return self._board

    def new_game(self) -> None:
        """See AbstractController."""
        super().new_game()
        self._board = board.Board(self.opts.x_size, self.opts.y_size)
        self._flags = 0
        self._notif.reset()

    def restart_game(self) -> None:
        super().restart_game()
        self.new_game()

    def select_cell(self, coord: Coord_T) -> None:
        super().select_cell(coord)
        cell = self._board[coord]
        if cell is CellUnclicked():
            self._board[coord] = CellNum(0)
        elif isinstance(cell, CellNum):
            self._board[coord] += 1
        else:
            return
        self._notif.update_cells({coord: self._board[coord]})

    def flag_cell(self, coord: Coord_T, *, flag_only: bool = False) -> None:
        super().flag_cell(coord)
        cell = self._board[coord]

        if cell is CellUnclicked():
            self._board[coord] = CellMine(1)
            self._flags += 1
        elif isinstance(cell, CellMine):
            if cell.num == self.opts.per_cell:
                if flag_only:
                    return
                self._board[coord] = CellUnclicked()
                self._flags -= self.opts.per_cell
            else:
                self._board[coord] += 1
                self._flags += 1
        elif isinstance(cell, CellNum):
            self.board[coord] = CellUnclicked()
        else:
            return
        self._notif.update_cells({coord: self._board[coord]})
        self._notif.update_mines_remaining(self._flags)

    def chord_on_cell(self, coord: Coord_T) -> None:
        super().chord_on_cell(coord)

    def remove_cell_flags(self, coord: Coord_T) -> None:
        super().remove_cell_flags(coord)
        cell = self._board[coord]
        if not isinstance(cell, CellMine):
            return
        self._board[coord] = CellUnclicked()
        self._flags -= cell.num
        self._notif.update_cells({coord: self._board[coord]})
        self._notif.update_mines_remaining(self._flags)

    def resize_board(self, *, x_size: int, y_size: int, mines: int) -> None:
        super().resize_board(x_size=x_size, y_size=y_size, mines=mines)
        if x_size == self.opts.x_size and y_size == self.opts.y_size:
            logger.info(
                "No resize required as the parameters are unchanged, starting a new game"
            )
            self.new_game()
            return

        logger.info(
            "Resizing board from %sx%s to %sx%s",
            self.opts.x_size,
            self.opts.y_size,
            x_size,
            y_size,
        )
        self.opts.x_size = x_size
        self.opts.y_size = y_size
        self._notif.resize(x_size, y_size)
        self.new_game()

    def set_first_success(self, value: bool) -> None:
        super().set_first_success(value)
        # Store the value so it can be retrieved from the next controller.
        self.opts.first_success = value

    def set_per_cell(self, value: int) -> None:
        super().set_per_cell(value)
        self.opts.per_cell = value
