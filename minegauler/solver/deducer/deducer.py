"""
deducer.py - The main module for deducing safety of cells on a minesweeper board

August 2019, Lewis Gaul
"""

from minegauler.backend.utils import Board
from minegauler.shared.internal_types import CellContentsType, CellNum, CellUnclicked, CellMineType


class CellSafe(CellUnclicked):
    """Indication that a cell is safe to click."""

    char = 'S'


class CellUnsafe(CellUnclicked):
    """Indication that a cell contains a mine."""

    char = 'U'


def deduce(board: Board) -> Board:
    """
    Take a partially solved minesweeper board, make some deductions, returning a modified version
    of the board.

    :param board:
        The minesweeper board to make deductions on.
    :return:
        The board containing deductions.
    """
    deduced_board = board.copy()
    _deduce_by_one_neighbour(deduced_board)
    return deduced_board


def _deduce_by_one_neighbour(board: Board) -> None:
    """
    Make deductions using numbers that are only adjacent to one clickable cell.

    :param board:
        The board to mutate.
    """
    for coord in board.all_coords:
        val = board[coord]
        if not isinstance(val, CellNum):
            continue
        nbrs = board.get_nbrs(coord)
        unclicked_nbrs = [
            c for c in nbrs if type(board[c], CellUnclicked)
        ]
        nbr_mines = board[coord].num - sum([board[c].num for c in nbrs if isinstance(board[c], CellMineType)])
        if len(unclicked_nbrs) == nbr_mines:
            for c in unclicked_nbrs:
                board[c] = CellUnsafe()
        elif nbr_mines == 0:
            for c in unclicked_nbrs:
                board[c] = CellSafe()
        # else:
        #     raise RuntimeError("Too many flags around cell {}".format(coord))

