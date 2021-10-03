# October 2021, Lewis Gaul

__all__ = ("Controller",)

import json
import logging
import os.path

import minegauler.shared.utils

from ...shared import GameOptsStruct, utils
from ...shared.types import CellContents, GameMode, GameState, PathLike
from .. import api, game
from ..controller import ControllerBase
from .board import Board
from .game import Game
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


def _save_minefield(mf: Minefield, file: PathLike) -> None:
    """
    Save a minefield to file.

    :param mf:
        The minefield to save.
    :param file:
        The path of the file to save at.
    :raises OSError:
        If saving to file fails.
    """
    if os.path.isfile(file):
        logger.warning("Overwriting file at %s", file)
    with open(file, "w") as f:
        json.dump(mf.to_json(), f)


class Controller(ControllerBase):
    """Controller for a regular minesweeper game."""

    mode = GameMode.REGULAR
    minefield_cls = Minefield
    board_cls = Board
    game_cls = Game

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    def new_game(self) -> None:
        """See AbstractController."""
        super().new_game()
        if self._opts.mines > self._opts.per_cell * (
            self._opts.x_size * self._opts.y_size - 1
        ):
            # This is needed since it's possible to create a board with more
            # mines than is normally allowed.
            logger.debug(
                "Reducing number of mines from %d to %d because they don't fit",
                self._opts.mines,
                self._opts.x_size * self._opts.y_size - 1,
            )
            self._opts.mines = self._opts.x_size * self._opts.y_size - 1
            self._notif.set_mines(self._opts.mines)
        self.game = self.game_cls(
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._opts.mines,
            per_cell=self._opts.per_cell,
            lives=self._opts.lives,
            first_success=self._opts.first_success,
        )
        self._send_reset_update()

    def restart_game(self) -> None:
        """See AbstractController."""
        if not self.game.mf:
            return
        super().restart_game()
        self.game = self.game_cls(minefield=self.game.mf, lives=self._opts.lives)
        self._send_reset_update()

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

    def save_current_minefield(self, file: PathLike) -> None:
        """
        Save the current minefield to file.

        :param file:
            The location of the file to save to. Should have the extension
            ".mgb".
        :raises RuntimeError:
            If the game is not finished.
        :raises OSError:
            If saving to file fails.
        """
        super().save_current_minefield(file)
        if not self.game.state.finished():
            raise RuntimeError("Can only save minefields when the game is completed")
        _save_minefield(self.game.mf, file)

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
            mf.nr_mines,
        )
        self._opts.x_size = mf.x_size
        self._opts.y_size = mf.y_size
        self._opts.mines = mf.nr_mines
        self.game = self.game_cls(minefield=mf, lives=self._opts.lives)
        self._send_resize_update()

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    def _send_reset_update(self) -> None:
        """Send an update to reset the board."""
        self._notif.reset()
        self._send_updates()

    def _send_resize_update(self) -> None:
        """Send an update to change the dimensions and number of mines."""
        self._notif.resize_minefield(self._opts.x_size, self._opts.y_size)
        self._notif.set_mines(self._opts.mines)
        self._send_updates()


class CreateController(ControllerBase):
    """A controller for creating boards."""

    def __init__(self, opts: GameOptsStruct, *, notif: api.AbstractListener):
        super().__init__(opts)
        # Use a reference to the given opts rather than a copy.
        self._opts = opts
        self._notif = notif
        self._board = Board(self._opts.x_size, self._opts.y_size)
        self._flags: int = 0
        self._notif.set_mines(self._flags)

    @property
    def board(self) -> Board:
        return self._board

    def get_game_info(self) -> api.GameInfo:
        return api.GameInfo(
            game_state=GameState.ACTIVE,
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._flags,
            difficulty=minegauler.shared.utils.difficulty_from_values(
                GameMode.REGULAR, self._opts.x_size, self._opts.x_size, self._flags
            ),
            per_cell=self._opts.per_cell,
            first_success=self._opts.first_success,
            minefield_known=True,
        )

    def new_game(self) -> None:
        """See AbstractController."""
        super().new_game()
        self._board = self.board_cls(self._opts.x_size, self._opts.y_size)
        self._flags = 0
        self._notif.reset()

    def restart_game(self) -> None:
        super().restart_game()
        self.new_game()

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

    def save_current_minefield(self, file: PathLike) -> None:
        """
        Save the current created minefield to file.

        :param file:
            The location of the file to save to. Should have the extension
            ".mgb".
        :raises OSError:
            If saving to file fails.
        """
        super().save_current_minefield(file)
        mines_grid = utils.Grid(self._opts.x_size, self._opts.y_size)
        for c in self._board.all_coords:
            if type(self._board[c]) is CellContents.Mine:
                mines_grid[c] = self._board[c].num
        mf = Minefield.from_grid(mines_grid, per_cell=self._opts.per_cell)
        _save_minefield(mf, file)

    def load_minefield(self, file: PathLike) -> None:
        return NotImplemented
