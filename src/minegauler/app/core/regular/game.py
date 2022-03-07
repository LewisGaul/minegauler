# October 2021, Lewis Gaul

__all__ = ("Game",)

import logging
import time

from ...shared.types import CellContents, Difficulty, GameMode, GameState
from ..game import GameBase, GameNotStartedError
from .board import Board
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


class Game(GameBase):
    """A regular minesweeper game."""

    mode = GameMode.REGULAR
    minefield_cls = Minefield
    board_cls = Board

    mf: Minefield
    board: Board

    _diff_pairs = [
        # fmt: off
        (Difficulty.BEGINNER,     ( 8,  8,  10)),
        (Difficulty.INTERMEDIATE, (16, 16,  40)),
        (Difficulty.EXPERT,       (30, 16,  99)),
        (Difficulty.MASTER,       (30, 30, 200)),
        (Difficulty.LUDICROUS,    (50, 50, 625)),
        # fmt: on
    ]

    # ---------------------
    # Abstract methods
    # ---------------------
    def _make_board(self) -> Board:
        return Board(self.x_size, self.y_size)

    def get_rem_3bv(self) -> int:
        if self.state is GameState.READY:
            try:
                return self.mf.bbbv
            except AttributeError:
                raise GameNotStartedError("Minefield not yet created") from None
        elif self.state is GameState.WON:
            return 0

        # Partially completed board - do the real work!

        partial_mf = Minefield.from_coords(
            self.mf.all_coords,
            mine_coords=self.mf.mine_coords,
            per_cell=self.per_cell,
        )
        # Replace any openings already found with normal clicks (ones).
        for c in self.board.all_coords:
            if type(self.board[c]) is CellContents.Num:
                partial_mf.completed_board[c] = CellContents.Num(1)
        # Find the openings which remain.
        rem_opening_coords = {c for opening in partial_mf.openings for c in opening}
        # Count the number of essential clicks that have already been
        # done by counting clicked cells minus the ones at the edge of
        # an undiscovered opening.
        completed_3bv = len(
            {
                c
                for c in self.board.all_coords
                if type(self.board[c]) is CellContents.Num
            }
            - rem_opening_coords
        )
        return partial_mf._calc_3bv() - completed_3bv

    def _populate_minefield(self, coord: Coord) -> None:
        """Create the minefield in response to a cell being selected."""
        if self.first_success:
            safe_coords = self.board.get_nbrs(coord, include_origin=True)
            logger.debug(
                "Trying to create minefield with the following safe coordinates: %s",
                safe_coords,
            )
            try:
                self.mf.populate(safe_coords)
            except ValueError:
                logger.info(
                    "Unable to give opening on the first click, "
                    "still ensuring a safe click"
                )
                # This should be guaranteed to succeed.
                self.mf.populate(safe_coords=[coord])
            else:
                logger.debug("Successfully created minefield")
        else:
            logger.debug("Creating minefield without guaranteed first click success")
            self.mf.populate()

    def _is_complete(self) -> bool:
        return all(
            type(self.board[c]) is CellContents.Num or c in self.mf.mine_coords
            for c in self.board.all_coords
        )

    def _select_cell_action(self, coord: Coord) -> None:
        """
        Implementation of the action of selecting/clicking a cell.
        """
        if coord in self.mf.mine_coords:
            logger.debug("Mine hit at %s", coord)
            self._set_cell(coord, CellContents.HitMine(self.mf[coord]))
            self.lives_remaining -= 1

            if self.lives_remaining == 0:
                logger.info("Game lost")
                self.end_time = time.time()
                self.state = GameState.LOST

                for c in self.mf.all_coords:
                    if (
                        c in self.mf.mine_coords
                        and self.board[c] is CellContents.Unclicked
                    ):
                        self._set_cell(c, CellContents.Mine(self.mf[c]))

                    elif (
                        type(self.board[c]) is CellContents.Flag
                        and self.board[c] != self.mf.completed_board[c]
                    ):
                        self._set_cell(c, CellContents.WrongFlag(self.board[c].num))
            else:
                self.mines_remaining -= self.mf[coord]
        elif self.mf.completed_board[coord] is CellContents.Num(0):
            for full_opening in self.mf.openings:
                if coord in full_opening:
                    # Found the opening, quit the loop here.
                    logger.debug("Opening hit: %s", full_opening)
                    break
            else:
                raise RuntimeError(f"Coordinate {coord} not found in openings")

            # Get the propagation of cells forming part of the opening.
            opening = set()  # Coords belonging to the opening
            check = {coord}  # Coords whose neighbours need checking
            while check:
                c = check.pop()
                unclicked_nbrs = {
                    z
                    for z in self.board.get_nbrs(c, include_origin=True)
                    if self.board[z] is CellContents.Unclicked
                }
                check |= {
                    z
                    for z in unclicked_nbrs - opening
                    if self.mf.completed_board[z] is CellContents.Num(0)
                }
                opening |= unclicked_nbrs

            logger.debug("Propagated opening: %s", list(opening))
            for c in opening:
                self._set_cell(c, self.mf.completed_board[c])
        else:
            logger.debug("Regular cell revealed")
            self._set_cell(coord, self.mf.completed_board[coord])
