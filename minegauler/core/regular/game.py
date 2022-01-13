# October 2021, Lewis Gaul

__all__ = ("Game", "difficulty_from_values", "difficulty_to_values")

import logging
import time
from typing import Dict, Mapping, Tuple

from ...shared.types import CellContents, Difficulty, GameMode, GameState
from ..game import GameBase, GameNotStartedError, _check_coord, _ignore_if_not
from .board import Board
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


_diff_pairs = [
    (Difficulty.BEGINNER, (8, 8, 10)),
    (Difficulty.INTERMEDIATE, (16, 16, 40)),
    (Difficulty.EXPERT, (30, 16, 99)),
    (Difficulty.MASTER, (30, 30, 200)),
    (Difficulty.LUDICROUS, (50, 50, 625)),
]


def difficulty_to_values(diff: Difficulty) -> Tuple[int, int, int]:
    try:
        return dict(_diff_pairs)[diff]
    except KeyError:
        raise ValueError(f"Unknown difficulty: {diff}") from None


def difficulty_from_values(x_size: int, y_size: int, mines: int) -> Difficulty:
    mapping = dict((x[1], x[0]) for x in _diff_pairs)
    try:
        return mapping[(x_size, y_size, mines)]
    except KeyError:
        return Difficulty.CUSTOM


class Game(GameBase):
    """A regular minesweeper game."""

    mode = GameMode.REGULAR
    minefield_cls = Minefield
    board_cls = Board

    mf: Minefield
    board: Board

    @classmethod
    def from_minefield(cls, mf: Minefield, **kwargs) -> "Game":
        self = cls(
            x_size=mf.x_size,
            y_size=mf.y_size,
            mines=mf.mines,
            per_cell=mf.per_cell,
            **kwargs,
        )
        self.mf = mf
        if mf.populated:
            self.minefield_known = True
        return self

    # ---------------------
    # Abstract methods
    # ---------------------
    @property
    def difficulty(self) -> Difficulty:
        return difficulty_from_values(self.x_size, self.y_size, self.mines)

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
        else:
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

    # ---------------------
    # Other methods
    # ---------------------
    def _set_cell(self, coord: Coord, state: CellContents) -> None:
        """
        Set the contents of a cell and store the update.

        :param coord:
            The coordinate of the cell to set.
        :param state:
            The state to set the cell to.
        """
        self.board[coord] = state
        self._cell_updates[coord] = state

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

    def _check_for_completion(self) -> None:
        """
        Check if game is complete by comparing the board to the minefield's
        completed board. If it is, display flags in remaining unclicked cells.
        """
        is_complete = all(
            type(self.board[c]) is CellContents.Num or c in self.mf.mine_coords
            for c in self.board.all_coords
        )

        if is_complete:
            logger.info("Game won")

            self.end_time = time.time()
            self.state = GameState.WON
            self.mines_remaining = 0

            for c in self.board.all_coords:
                if (
                    c in self.mf.mine_coords
                    and type(self.board[c]) is not CellContents.HitMine
                ):
                    self._set_cell(c, CellContents.Flag(self.mf[c]))

    @_check_coord
    @_ignore_if_not(
        game_state=(GameState.READY, GameState.ACTIVE),
        cell_state=CellContents.Unclicked,
    )
    def select_cell(self, coord: Coord) -> Mapping[Coord, CellContents]:
        """Perform the action of selecting/clicking a cell."""
        just_started = False
        if self.state is GameState.READY:
            if not self.mf.populated:
                self._populate_minefield(coord)
            self.state = GameState.ACTIVE
            self.start_time = time.time()
            just_started = True
        self._select_cell_action(coord)
        if not self.state.finished():
            self._check_for_completion()
            if self.state is GameState.WON and just_started:
                self.end_time = self.start_time
        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()

    @_check_coord
    @_ignore_if_not(
        game_state=(GameState.READY, GameState.ACTIVE),
        cell_state=(CellContents.Flag, CellContents.Unclicked),
    )
    def set_cell_flags(
        self, coord: Coord, nr_flags: int
    ) -> Mapping[Coord, CellContents]:
        """Set the number of flags in a cell."""
        if nr_flags < 0 or nr_flags > self.per_cell:
            raise ValueError(
                f"Invalid number of flags ({nr_flags}) - should be between 0 and "
                f"{self.per_cell}"
            )

        old_nr_flags = (
            0 if self.board[coord] is CellContents.Unclicked else self.board[coord].num
        )
        if nr_flags == 0:
            self._set_cell(coord, CellContents.Unclicked)
        else:
            self._set_cell(coord, CellContents.Flag(nr_flags))
        self.mines_remaining += old_nr_flags - nr_flags
        self._num_flags += nr_flags - old_nr_flags

        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()

    @_check_coord
    @_ignore_if_not(game_state=GameState.ACTIVE, cell_state=CellContents.Num)
    def chord_on_cell(self, coord: Coord) -> Mapping[Coord, CellContents]:
        """Chord on a cell that contains a revealed number."""
        nbrs = self.board.get_nbrs(coord)
        num_flagged_nbrs = sum(
            [self.board[c].num for c in nbrs if self.board[c].is_mine_type()]
        )
        logger.debug(
            "%s flagged mine(s) around clicked cell showing number %s",
            num_flagged_nbrs,
            self.board[coord],
        )

        unclicked_nbrs = [c for c in nbrs if self.board[c] is CellContents.Unclicked]
        if (
            self.board[coord] != CellContents.Num(num_flagged_nbrs)
            or not unclicked_nbrs
        ):
            return dict()

        logger.info("Successful chording, selecting cells %s", unclicked_nbrs)
        for c in unclicked_nbrs:
            self._select_cell_action(c)

        if self.state != GameState.LOST:
            self._check_for_completion()

        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()
