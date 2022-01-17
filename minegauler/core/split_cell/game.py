# October 2021, Lewis Gaul

__all__ = ("Game",)

import logging
import time
from typing import Iterable, Mapping

from ...shared.types import CellContents, Difficulty, GameMode, GameState
from ..game import GameBase, GameNotStartedError, _check_coord, _ignore_if_not
from .board import Board
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


class Game(GameBase):
    """A split-cells minesweeper game."""

    mode = GameMode.REGULAR
    minefield_cls = Minefield
    board_cls = Board

    mf: Minefield
    board: Board

    _diff_pairs = [
        # fmt: off
        (Difficulty.BEGINNER,     ( 8,  8,   5)),
        (Difficulty.INTERMEDIATE, (16, 16,  20)),
        (Difficulty.EXPERT,       (30, 16,  50)),
        (Difficulty.MASTER,       (30, 30, 100)),
        (Difficulty.LUDICROUS,    (50, 50, 400)),
        # fmt: on
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Used for tracking numbers that should be revealed for performance.
        self._revealed_board = Board(self.x_size, self.y_size)

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

        # TODO: This is too slow!

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
        num_coords = {
            c for c in self.board.all_coords if type(self.board[c]) is CellContents.Num
        }
        completed_3bv = len(num_coords - rem_opening_coords)
        # Add necessary splits that have already been done.
        big_cells_correctly_split = {
            c.get_big_cell_coord()
            for c in self.board.all_coords
            if c.is_split and c not in self.mf.mine_coords
        }
        completed_3bv += len(big_cells_correctly_split)
        return partial_mf._calc_3bv() - completed_3bv

    def _populate_minefield(self, coord: Coord) -> None:
        """Create the minefield in response to a cell being selected."""
        if self.first_success:
            safe_coords = [
                small
                for big in self.board.get_nbrs(coord, include_origin=True)
                for small in big.split()
            ]
            logger.debug(
                "Trying to create minefield with the following safe coordinates: %s",
                safe_coords,
            )
            try:
                self.mf.populate(safe_coords)
            except ValueError:
                try:
                    logger.info(
                        "Unable to give opening on the first click, "
                        "trying to ensure a safe click"
                    )
                    self.mf.populate(safe_coords=coord.split())
                except ValueError:
                    logger.info("Unable to give even a single safe cell")
                    self.mf.populate()
            else:
                logger.debug("Minefield populated")
        else:
            logger.debug("Creating minefield without guaranteed first click success")
            self.mf.populate()

    def _is_complete(self) -> bool:
        return all(
            type(self.board[c]) is CellContents.Num
            or all(small in self.mf.mine_coords for small in c.get_small_cell_coords())
            for c in self.board.all_coords
        )

    def _select_cell_action(self, coord: Coord) -> None:
        """Implementation of the action of selecting/clicking a cell."""
        if self._revealed_board[coord] is CellContents.Unclicked:
            # TODO: This is a bit of a hacky place to do this...
            self._revealed_board = self._calc_revealed_board()

        if coord.is_split:
            if coord in self.mf.mine_coords:
                logger.debug("Mine hit at %s", coord)
                self._set_cell(coord, CellContents.HitMine(self.mf[coord]))
                self._finalise_lost_game()
            else:
                logger.debug("Regular cell revealed")
                self._set_cell(coord, self._revealed_board[coord])
        else:
            small_cells = coord.split()
            if any(c in self.mf.mine_coords for c in small_cells):
                logger.debug("Mine hit in large cell containing %s", coord)
                for c in small_cells:
                    if self.mf[c] > 0:
                        self._set_cell(c, CellContents.HitMine(self.mf[c]))
                self._finalise_lost_game()
            else:
                assert type(self._revealed_board[coord]) is CellContents.Num
                cell_num = self._revealed_board[coord].num
                if cell_num > 0:  # regular num revealed
                    logger.debug("Regular cell revealed")
                    self._set_cell(coord, self._revealed_board[coord])
                else:  # opening hit
                    logger.debug("Opening found")
                    # Use pre-calculated 'revealed board' for performance.
                    checked = set()
                    blank_nbrs = {coord}
                    all_nbrs = {coord}
                    while blank_nbrs - checked:
                        c = (blank_nbrs - checked).pop()
                        logger.debug("Checking neighbours of %s", c)
                        cur_nbrs = set(
                            c
                            for c in self.board.get_nbrs(c)
                            if self.board[c] is CellContents.Unclicked
                        )
                        all_nbrs |= cur_nbrs
                        blank_nbrs |= {
                            c
                            for c in cur_nbrs
                            if self._revealed_board[c] == CellContents.Num(0)
                        }
                        checked.add(c)
                    logger.debug("Opening cells deduced")
                    for c in all_nbrs:
                        self._set_cell(c, self._revealed_board[c])

    # ---------------------
    # Other methods
    # ---------------------
    def _calc_revealed_board(self) -> Board:
        board = Board(self.x_size, self.y_size)
        for coord in board.all_coords:
            mines = sum(self.mf[small] for small in coord.get_small_cell_coords())
            if mines > 0:
                board[coord] = CellContents.Flag(mines)
            else:
                num = sum(
                    self.mf[small]
                    for nbr in board.get_nbrs(coord)
                    for small in nbr.get_small_cell_coords()
                )
                board[coord] = CellContents.Num(num)
        return board

    def _calc_nbr_mines(self, coord: Coord) -> int:
        return sum(
            self.mf[c]
            for nbr in self.board.get_nbrs(coord)
            for c in nbr.get_small_cell_coords()
        )

    def _update_board_numbers(self, coords: Iterable[Coord]) -> None:
        """
        Calculate the numbers contained in the board given the split cell
        situation.
        """
        for c in coords:
            num = CellContents.Num(self._calc_nbr_mines(c))
            if type(self.board[c]) is CellContents.Num:
                self._set_cell(c, num)
            self._revealed_board[c] = num

    def _finalise_lost_game(self) -> None:
        logger.info("Game lost")
        self.end_time = time.time()
        self.state = GameState.LOST
        for c in self.mf.mine_coords:
            if self.board[self.board.get_coord_at(c.x, c.y)] is CellContents.Unclicked:
                self._set_cell(c, CellContents.Mine(self.mf[c]))
        for c in self.board.all_coords:
            if (
                type(self.board[c]) is CellContents.Flag
                and self.board[c].num != self.mf[c]
            ):
                self._set_cell(c, CellContents.WrongFlag(self.board[c].num))

    @_check_coord
    @_ignore_if_not(
        game_state=[GameState.READY, GameState.ACTIVE],
        cell_state=CellContents.Unclicked,
    )
    def split_cell(self, coord: Coord) -> Mapping[Coord, CellContents]:
        small_cells = coord.split()

        just_started = False
        if self.state is GameState.READY:
            if not self.mf.populated:
                logger.debug(
                    "Creating minefield without guaranteed first click success"
                )
                self.mf.populate()
            self.state = GameState.ACTIVE
            self.start_time = time.time()
            just_started = True
            self._revealed_board = self._calc_revealed_board()

        if not any(c in self.mf.mine_coords for c in small_cells):
            logger.debug("Incorrect cell split %s", coord)
            self._set_cell(coord, CellContents.WrongFlag(1))
            self._finalise_lost_game()
            if self.state.finished() and just_started:
                self.end_time = self.start_time
        else:
            logger.debug("Splitting cell %s", coord)
            nbrs = self.board.get_nbrs(coord)
            self.board.split_coord(coord)
            self._revealed_board.split_coord(coord)
            self._cell_updates.update({c: CellContents.Unclicked for c in small_cells})
            self._update_board_numbers((*nbrs, *small_cells))
        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()
