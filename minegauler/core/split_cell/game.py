# October 2021, Lewis Gaul

__all__ = ("Game", "difficulty_from_values", "difficulty_to_values")

import logging
import time
from typing import Mapping, Tuple

from ...shared.types import CellContents, Difficulty, GameMode, GameState
from ..game import GameBase, _check_coord, _ignore_if_not
from .board import Board
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


_diff_pairs = [
    (Difficulty.BEGINNER, (8, 8, 5)),
    (Difficulty.INTERMEDIATE, (16, 16, 20)),
    (Difficulty.EXPERT, (30, 16, 50)),
    (Difficulty.MASTER, (30, 30, 100)),
    (Difficulty.LUDICROUS, (50, 50, 400)),
]


# TODO: Share the implementation of these functions, using the diff_pairs mapping.


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
    """A split-cells minesweeper game."""

    mode = GameMode.REGULAR
    minefield_cls = Minefield
    board_cls = Board

    mf: Minefield
    board: Board

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # ---------------------
    # Abstract methods
    # ---------------------
    @property
    def difficulty(self) -> Difficulty:
        return difficulty_from_values(self.x_size, self.y_size, self.mines)

    def _make_board(self) -> Board:
        return Board(self.x_size, self.y_size)

    def get_rem_3bv(self) -> int:
        return 0  # TODO

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
                logger.info(
                    "Unable to give opening on the first click, "
                    "still ensuring a safe click"
                )
                # This should be guaranteed to succeed.  TODO
                self.mf.populate(safe_coords=coord.split())
            else:
                logger.debug("Successfully created minefield")
        else:
            logger.debug("Creating minefield without guaranteed first click success")
            self.mf.populate()

    def _select_cell_action(self, coord: Coord) -> None:
        """Implementation of the action of selecting/clicking a cell."""
        if not coord.is_split:
            small_cells = coord.split()
            if any(c in self.mf.mine_coords for c in small_cells):
                logger.debug("Mine hit in large cell containing %s", coord)
                for c in small_cells:
                    if self.mf[c] > 0:
                        self._set_cell(c, CellContents.HitMine(self.mf[c]))
                self._finalise_lost_game()
            else:
                logger.debug("Regular cell revealed")
                cell_num = self._calc_nbr_mines(coord)
                self._set_cell(coord, CellContents.Num(cell_num))
            return

        if coord in self.mf.mine_coords:
            logger.debug("Mine hit at %s", coord)
            self._set_cell(coord, CellContents.HitMine(self.mf[coord]))
            self._finalise_lost_game()
        else:
            logger.debug("Regular cell revealed")
            self._set_cell(coord, CellContents.Num(self._calc_nbr_mines(coord)))

    # ---------------------
    # Other methods
    # ---------------------
    def _calc_nbr_mines(self, coord: Coord) -> int:
        return sum(
            self.mf[c]
            for nbr in self.board.get_nbrs(coord)
            for c in nbr.get_small_cell_coords()
        )

    def _update_board_numbers(self) -> None:
        """
        Calculate the numbers contained in the board given the split cell
        situation.
        """
        for coord in self.board.all_coords:
            if type(self.board[coord]) is not CellContents.Num:
                continue
            self._set_cell(coord, CellContents.Num(self._calc_nbr_mines(coord)))

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

    def _check_for_completion(self) -> None:
        if any(
            self.board[c] is CellContents.Unclicked and c.is_split
            for c in self.board.all_coords
        ):
            return
        super()._check_for_completion()

    @_check_coord
    @_ignore_if_not(
        game_state=GameState.ACTIVE,
        cell_state=CellContents.Unclicked,
    )
    def split_cell(self, coord: Coord) -> Mapping[Coord, CellContents]:
        small_cells = coord.split()
        if not any(c in self.mf.mine_coords for c in small_cells):
            logger.debug("Incorrect cell split %s", coord)
            self._set_cell(coord, CellContents.WrongFlag(1))
            self._finalise_lost_game()
        else:
            logger.debug("Splitting cell %s", coord)
            self.board.split_coord(coord)
            self._cell_updates.update({c: CellContents.Unclicked for c in small_cells})
            self._update_board_numbers()
        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()
