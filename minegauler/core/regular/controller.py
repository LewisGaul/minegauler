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

    def set_difficulty(self, difficulty: Difficulty) -> None:
        x, y, m = difficulty_to_values(difficulty)
        self.resize_board(x, y, m)


class GameController(_ControllerMixin, GameControllerBase):
    """GameController for a regular minesweeper game."""

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def select_cell(self, coord: Coord) -> None:
        """See AbstractController."""
        super().select_cell(coord)
        cells = self.game.select_cell(coord)
        self._send_updates(cells)

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        """See AbstractController."""
        super().flag_cell(coord)

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
        """See AbstractController."""
        super().remove_cell_flags(coord)
        self.game.set_cell_flags(coord, 0)
        self._send_updates({coord: self.board[coord]})

    def chord_on_cell(self, coord: Coord) -> None:
        """See AbstractController."""
        super().chord_on_cell(coord)
        cells = self.game.chord_on_cell(coord)
        self._send_updates(cells)

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
            return

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

        self.game = self.game_cls(
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._opts.mines,
            per_cell=self._opts.per_cell,
            lives=self._opts.lives,
            first_success=self._opts.first_success,
        )
        self._send_resize_update()

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
        # If the game is not started and the minefiels is not known then the
        # new per-cell value should be picked up immediately, and the board
        # cleared of any flags (e.g. 3-flag cells may no longer be allowed!).
        if not (self.game.state.started() or self.game.minefield_known):
            self.new_game()

    def load_minefield(self, file: PathLike) -> None:
        """
        Load a minefield from file.

        :param file:
            The location of the file to load from. Should have the extension
            ".mgb".
        """
        with open(file) as f:
            mf = Minefield.from_json(json.load(f))

        logger.debug(
            "Loaded minefield from file (%d x %d, %d mines)",
            mf.x_size,
            mf.y_size,
            mf.mines,
        )
        self._opts.x_size = mf.x_size
        self._opts.y_size = mf.y_size
        self._opts.mines = mf.mines
        self.game = self.game_cls.from_minefield(
            mf, x_size=mf.x_size, y_size=mf.y_size, lives=self._opts.lives
        )
        self._send_resize_update()


class CreateController(_ControllerMixin, CreateControllerBase):
    """A controller for creating boards."""

    @property
    def difficulty(self) -> Difficulty:
        return difficulty_from_values(self._opts.x_size, self._opts.y_size, self._flags)

    def _make_board(self) -> Board:
        return Board(self._opts.x_size, self._opts.y_size)

    def select_cell(self, coord: Coord) -> None:
        super().select_cell(coord)
        cell = self._board[coord]
        if cell is CellContents.Unclicked:
            self._board[coord] = CellContents.Num(0)
        elif isinstance(cell, CellContents.Num):
            self._board[coord] += 1
        else:
            return
        self._notif.update_cells({coord: self._board[coord]})

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        super().flag_cell(coord)
        cell = self._board[coord]

        if cell is CellContents.Unclicked:
            self._board[coord] = CellContents.Mine(1)
            self._flags += 1
        elif isinstance(cell, CellContents.Mine):
            if cell.num == self._opts.per_cell:
                if flag_only:
                    return
                self._board[coord] = CellContents.Unclicked
                self._flags -= self._opts.per_cell
            else:
                self._board[coord] += 1
                self._flags += 1
        elif isinstance(cell, CellContents.Num):
            self.board[coord] = CellContents.Unclicked
        else:
            return
        self._notif.update_cells({coord: self._board[coord]})
        self._notif.update_mines_remaining(self._flags)

    def chord_on_cell(self, coord: Coord) -> None:
        super().chord_on_cell(coord)

    def remove_cell_flags(self, coord: Coord) -> None:
        super().remove_cell_flags(coord)
        cell = self._board[coord]
        if not isinstance(cell, CellContents.Mine):
            return
        self._board[coord] = CellContents.Unclicked
        self._flags -= cell.num
        self._notif.update_cells({coord: self._board[coord]})
        self._notif.update_mines_remaining(self._flags)

    def resize_board(self, x_size: int, y_size: int, mines: int) -> None:
        """Resize the board. The number of mines is ignored."""
        super().resize_board(x_size=x_size, y_size=y_size, mines=mines)
        if x_size == self._opts.x_size and y_size == self._opts.y_size:
            logger.info(
                "No resize required as the parameters are unchanged, starting a new game"
            )
            self.new_game()
            return

        logger.info(
            "Resizing board from %sx%s to %sx%s",
            self._opts.x_size,
            self._opts.y_size,
            x_size,
            y_size,
        )
        self._opts.x_size = x_size
        self._opts.y_size = y_size
        self._notif.resize_minefield(x_size, y_size)
        self.new_game()

    def set_first_success(self, value: bool) -> None:
        super().set_first_success(value)
        self._opts.first_success = value

    def set_per_cell(self, value: int) -> None:
        super().set_per_cell(value)
        self._opts.per_cell = value
