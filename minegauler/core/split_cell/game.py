# October 2021, Lewis Gaul

__all__ = ("Game", "difficulty_from_values", "difficulty_to_values")

import logging
import time
from typing import Dict, Iterable, Tuple

from ...shared.types import CellContents, Difficulty, GameMode, GameState
from ..game import GameBase, _check_coord, _ignore_if_not
from .board import Board
from .minefield import Minefield
from .types import Coord


logger = logging.getLogger(__name__)


_diff_pairs = [
    (Difficulty.BEGINNER, (4, 4, 5)),
    (Difficulty.INTERMEDIATE, (8, 8, 20)),
    (Difficulty.EXPERT, (15, 8, 49)),
    (Difficulty.MASTER, (15, 15, 100)),
    (Difficulty.LUDICROUS, (25, 25, 400)),
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


# TODO:
#  This whole module needs effectively rewriting from scratch, hasn't worked
#  since stuff was moved around.


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
        return difficulty_from_values(self.mode, self.x_size, self.y_size, self.mines)

    def _make_board(self) -> Board:
        return Board(self.x_size, self.y_size)

    def get_rem_3bv(self) -> int:
        raise NotImplementedError  # TODO

    # ---------------------
    # Other methods
    # ---------------------
    def _set_cell(self, coord: Coord, state: CellContents) -> None:
        """
        Set the contents of a small cell and store the update.

        :param coord:
            The coordinate of the cell to set.
        """
        self.board[coord] = state
        self._cell_updates[coord] = state

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
        for c in self.mf.all_coords:
            small_coord = Coord(*c, True)
            board_coord = self.board.get_coord_at(*c)
            if (
                not board_coord.is_split
                and self.board[board_coord] is not CellContents.Unclicked
            ):
                continue

            if (
                small_coord not in self.board
                or self.board[small_coord] is CellContents.Unclicked
            ) and self.mf.cell_contains_mine(c):
                self._set_cell(small_coord, CellContents.Mine(self.mf[c]))
            elif (
                small_coord in self.board
                and type(self.board[small_coord]) is CellContents.Flag
                and self.board[small_coord] != self.mf.completed_board[c]
            ):
                self._set_cell(
                    small_coord, CellContents.WrongFlag(self.board[small_coord].num)
                )

    def _select_cell_action(self, coord: Coord) -> None:
        """
        Implementation of the action of selecting/clicking a cell.
        """
        if not coord.is_split:
            small_cells = coord.get_small_cell_coords()
            if any(self.mf.cell_contains_mine(c) for c in small_cells):
                logger.debug("Mine hit in large cell containing %s", coord)
                for c in small_cells:
                    if self.mf[c] > 0:
                        self._set_cell(
                            Coord(*c, True), CellContents.HitMine(self.mf[c])
                        )
                self._finalise_lost_game()
            else:
                logger.debug("Regular cell revealed")
                cell_num = self._calc_nbr_mines(coord)
                self._set_cell(coord, CellContents.Num(cell_num))
            return

        if self.mf.cell_contains_mine((coord.x, coord.y)):
            logger.debug("Mine hit at %s", coord)
            self._set_cell(coord, CellContents.HitMine(self.mf[(coord.x, coord.y)]))
            self._finalise_lost_game()
        else:
            logger.debug("Regular cell revealed")
            self._set_cell(coord, CellContents.Num(self._calc_nbr_mines(coord)))

    def _check_for_completion(self) -> None:
        if any(
            self.board[c] is CellContents.Unclicked and not c.is_split
            for c in self.board.all_coords
        ):
            return
        super()._check_for_completion()

    def select_cell(self, coord: Coord) -> Dict[Coord, CellContents]:
        if self.board[coord] is not CellContents.Unclicked:
            return {}
        return super().select_cell(coord)

    @_check_coord
    @_ignore_if_not(
        game_state=GameState.ACTIVE, cell_state=CellContents.Unclicked,
    )
    def split_cell(self, coord: Coord) -> Iterable[Coord]:
        if self.board[coord] is not CellContents.Unclicked:
            return
        small_cells = coord.get_small_cell_coords()
        if not any(self.mf.cell_contains_mine(c) for c in small_cells):
            logger.debug("Incorrect cell split %s", coord)
            self._set_cell(coord, CellContents.WrongFlag(1))
            self._finalise_lost_game()
        else:
            logger.debug("Splitting cell %s", coord)
            for c in self.board.split_cell(coord):
                self._cell_updates[c] = CellContents.Unclicked
            self._update_board_numbers()
        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()

    @_check_coord
    @_ignore_if_not(game_state=GameState.ACTIVE, cell_state=CellContents.Num)
    def chord_on_cell(self, coord: Coord) -> Dict[Coord, CellContents]:
        """Chord on a cell that contains a revealed number."""
        # TODO: Implement
