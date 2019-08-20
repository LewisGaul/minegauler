"""
deducer.py - The main module for deducing safety of cells on a minesweeper board

August 2019, Lewis Gaul
"""

from minegauler.backend.utils import Board
from minegauler.shared.internal_types import CellContentsType


class CellSafe(CellContentsType):
    """Indication that a cell is safe to click."""

    char = 'S'


class CellUnsafe(CellContentsType):
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
    pass

