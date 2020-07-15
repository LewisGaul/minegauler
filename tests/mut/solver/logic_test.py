# July 2020, Lewis Gaul

"""
MUT for the solver logic module.

"""

import logging
from collections import namedtuple
from typing import Iterable

import numpy as np
import pytest

from minegauler.core import Board
from minegauler.shared.types import CellContents
from minegauler.shared.utils import Grid
from minegauler.solver import logic
from minegauler.solver.logic import _Config_T


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------


class Case(namedtuple("_Case", "board, mines, configs, probs")):
    """Boards for testing."""

    def __new__(
        cls, board: Board, mines: int, configs: Iterable[_Config_T], probs: Grid
    ):
        return super().__new__(cls, board, mines, configs, probs)


x = CellContents.Unclicked
F = CellContents.Flag(1)
cases = [
    Case(
        board=Board.from_2d_array(
            [
                [x, 2, x, x, x],
                [x, x, x, x, x],
                [x, 3, x, x, x],
                [x, 2, x, 4, x],
                [x, x, x, x, x],
            ]
        ),
        mines=8,
        configs={
            (1, 1, 0, 0, 2, 0, 2, 2),
            (1, 1, 1, 0, 1, 0, 1, 3),
            (1, 1, 2, 0, 0, 0, 0, 4),
            (0, 2, 0, 0, 1, 1, 2, 2),
            (0, 2, 1, 0, 0, 1, 1, 3),
            (0, 2, 0, 1, 1, 0, 1, 3),
            (0, 2, 1, 1, 0, 0, 0, 4),
        },
        probs=Grid.from_2d_array([[0]]),
    )
]


# ------------------------------------------------------------------------------
# Test logic
# ------------------------------------------------------------------------------


def assert_np_rows_equal(array1: np.ndarray, array2: np.ndarray):
    """Assert two 2D numpy arrays are equal modulo row ordering."""
    assert sorted(array1.tolist()) == sorted(array2.tolist())


@pytest.mark.parametrize("case", cases)
def test_basic(case: Case):
    logger.debug("Using board with %d mines:\n%s", case.mines, case.board)

    s = logic.Solver(case.board, case.mines)
    cfgs = s._find_configs()

    assert set(cfgs) == case.configs


def test_full_flow():
    board = Board.from_2d_array(
        [
            [x, 2, x, x, x],
            [x, x, x, x, x],
            [x, 3, x, x, x],
            [x, 2, x, 4, x],
            [x, x, x, x, x],
        ]
    )
    mines = 8
    logger.debug("Using board with %d mines:\n%s", mines, board)

    s = logic.Solver(board, mines)
    full_matrix = s._find_full_matrix()
    logger.debug("Got full matrix:\n%s", full_matrix)
    exp_matrix = logic._MatrixAndVec(
        [
            [1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        [2, 3, 2, 4, 8],
    )
    assert_np_rows_equal(full_matrix._join_matrix_vec(), exp_matrix._join_matrix_vec())
