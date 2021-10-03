# October 2021, Lewis Gaul

__all__ = ("Controller",)

import json
import logging
import os.path
import sys
from typing import Dict, Optional


if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from attr import attr

from ...shared import GameOptsStruct
from ...shared.types import CellContents, GameMode, GameState, PathLike
from .. import api
from ..controller import ControllerBase
from .board import Board
from .game import Game
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


# TODO:
#  This whole module needs effectively rewriting from scratch, hasn't worked
#  since stuff was moved around.


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


@attr.attrs(auto_attribs=True, kw_only=True)
class _SharedInfo:
    """
    Information to pass to frontends.

    Elements:
    cell_updates
        Dictionary of updates to cells, mapping the coordinate to the new
        contents of the cell.
    game_state
        The state of the game.
    mines_remaining
        The number of mines remaining to be found, given by
        [total mines] - [number of flags].
        Can be negative if there are too many flags.
    lives_remaining
        The number of lives remaining.
    """

    cell_updates: Optional[Dict[Coord, CellContents]] = None
    game_state: GameState = GameState.READY
    mines_remaining: int = 0
    lives_remaining: int = 0


class Controller(ControllerBase[Literal[GameMode.REGULAR]]):
    """Controller for a regular minesweeper game."""

    mode = GameMode.REGULAR
    board_cls = Board
    game_cls = Game

    def __init__(
        self, opts: GameOptsStruct, *, notif: api.AbstractListener,
    ):
        """
        :param opts:
            Game options.
        :param notif:
            A notifier defining callbacks.
        """
        super().__init__(opts)
        # Use a reference to the given opts rather than a copy.
        self._opts = opts
        self._notif = notif
        self._game = self.game_cls(
            x_size=self._opts.x_size,
            y_size=self._opts.y_size,
            mines=self._opts.mines,
            per_cell=self._opts.per_cell,
            lives=self._opts.lives,
            first_success=self._opts.first_success,
        )
        self._last_update = _SharedInfo()
        self._send_updates()
        self._notif.set_mines(self._opts.mines)

    @property
    def board(self) -> Board:
        return self._game.board

    def get_game_info(self) -> api.GameInfo:
        """Get info about the current game."""
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
                bbbv=self._game.mf.bbbv,
                rem_bbbv=self._game.get_rem_3bv(),
                bbbvps=self._game.get_3bvps(),
                prop_complete=self._game.get_prop_complete(),
                prop_flagging=self._game.get_flag_proportion(),
            )
        return ret

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
        self._game = self.game_cls(
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
        if not self._game.mf:
            return
        super().restart_game()
        self._game = self.game_cls(minefield=self._game.mf, lives=self._opts.lives)
        self._send_reset_update()

    def select_cell(self, coord: Coord) -> None:
        """See AbstractController."""
        super().select_cell(coord)
        cells = self._game.select_cell(coord)
        self._send_updates(cells)

    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        """See AbstractController."""
        super().flag_cell(coord)

        cell_state = self.board[coord]
        if cell_state is CellContents.Unclicked:
            self._game.set_cell_flags(coord, 1)
        elif isinstance(cell_state, CellContents.Flag):
            if cell_state.num >= self._game.per_cell:
                if flag_only:
                    return
                self._game.set_cell_flags(coord, 0)
            else:
                self._game.set_cell_flags(coord, cell_state.num + 1)

        self._send_updates({coord: self.board[coord]})

    def remove_cell_flags(self, coord: Coord) -> None:
        """See AbstractController."""
        super().remove_cell_flags(coord)
        self._game.set_cell_flags(coord, 0)
        self._send_updates({coord: self.board[coord]})

    def chord_on_cell(self, coord: Coord) -> None:
        """See AbstractController."""
        super().chord_on_cell(coord)
        cells = self._game.chord_on_cell(coord)
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

        self._game = self.game_cls(
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
        if not self._game.state.started():
            self._game.first_success = value

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
        if not (self._game.state.started() or self._game.minefield_known):
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
        if not self._game.state.finished():
            raise RuntimeError("Can only save minefields when the game is completed")
        _save_minefield(self._game.mf, file)

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
        self._game = self.game_cls(minefield=mf, lives=self._opts.lives)
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

    def _send_updates(
        self, cells_updated: Optional[Dict[Coord, CellContents]] = None
    ) -> None:
        """Send updates to registered listeners."""
        update = _SharedInfo(
            cell_updates=cells_updated,
            mines_remaining=self._game.mines_remaining,
            lives_remaining=self._game.lives_remaining,
            game_state=self._game.state,
        )

        # Send updates to registered listeners.
        if update.cell_updates:
            self._notif.update_cells(update.cell_updates)
        if update.mines_remaining != self._last_update.mines_remaining:
            self._notif.update_mines_remaining(update.mines_remaining)
        # if update.lives_remaining != self._last_update.lives_remaining:
        #     self._notif.update_lives_remaining(update.lives_remaining)
        if update.game_state is not self._last_update.game_state:
            self._notif.update_game_state(update.game_state)

        self._last_update = update
