# July 2020, Lewis Gaul

"""
MUT for the solver logic module.

"""

import logging
import time
from types import SimpleNamespace
from typing import Iterable, List, Optional

import numpy as np
import pytest

from minegauler.core import Board
from minegauler.shared.types import CellContents, Coord_T
from minegauler.shared.utils import Grid
from minegauler.solver import logic
from minegauler.solver.logic import _Config_T


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------


class Case(SimpleNamespace):
    """Boards for testing."""

    board: Board
    mines: int
    per_cell: int
    full_matrix: Optional[np.ndarray]
    groups: Optional[List[Iterable[Coord_T]]]
    groups_matrix: Optional[np.ndarray]
    configs: Optional[Iterable[_Config_T]]
    probs: Grid

    def __init__(
        self,
        board: List[List],
        *,
        mines: int,
        per_cell: int = 1,
        full_matrix: Optional[List[List[int]]] = None,
        groups: Optional[List[Iterable[Coord_T]]] = None,
        groups_matrix: Optional[List[List[int]]] = None,
        configs: Optional[Iterable[_Config_T]] = None,
        probs: List[List],
    ):
        super().__init__(
            board=Board.from_2d_array(board),
            mines=mines,
            per_cell=per_cell,
            full_matrix=np.array(full_matrix) if full_matrix else None,
            groups=groups,
            groups_matrix=np.array(groups_matrix) if groups_matrix else None,
            configs=configs,
            probs=Grid.from_2d_array(probs),
        )


x = CellContents.Unclicked
F = CellContents.Flag(1)

# fmt: off
cases = [
    # Basic case with single configuration.
    Case(
        [
            [x, x, 1],
            [3, x, 2],
            [x, x, x],
        ],
        mines=3,
        full_matrix=[
            [1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1],
        ],
        groups_matrix=[
            [1, 1, 1, 0],  # [3]
            [0, 1, 0, 0],  # [1]
            [0, 1, 1, 1],  # [2]
            [1, 1, 1, 1],  # [3] (mines)
        ],
        groups=[
            {(0, 0), (0, 2)},  # 0
            {(1, 0), (1, 1)},  # 1
            {(1, 2)},          # 2
            {(2, 2)},          # 3
        ],
        configs={
            (1, 1, 1, 0),
        },
        probs=[
            [0.5, 0.5, 0],
            [0,   0.5, 0],
            [0.5, 1,   0],
        ],
    ),

    # Same as above with 4 mines instead of 3.
    Case(
        [
            [x, x, 1],
            [3, x, 2],
            [x, x, x],
        ],
        mines=4,
        groups=[
            {(0, 0), (0, 2)},  # 0
            {(1, 0), (1, 1)},  # 1
            {(1, 2)},          # 2
            {(2, 2)},          # 3
        ],
        configs={
            (2, 1, 0, 1),
        },
        probs=[
            [1, 0.5, 0],
            [0, 0.5, 0],
            [1, 0,   1],
        ],
    ),

    # Small constructed example.
    Case(
        [
            [x, 2, x, x, x],
            [x, x, x, x, x],
            [x, 3, x, x, x],
            [x, 2, x, 4, x],
            [x, x, x, x, x],
        ],
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
        probs=[
            [0.27108, 0,       0.27108, 0.31325, 0.31325],
            [0.48594, 0.48594, 0.48594, 0.31325, 0.31325],
            [0.26506, 0,       0.50602, 0.54940, 0.54940],
            [0.26506, 0,       0.50602, 0,       0.54940],
            [0.10843, 0.10843, 0.24096, 0.54940, 0.54940],
        ],
    ),

    # Partially completed expert board.
    Case(
        [
          #  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29
            [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  0
            [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  1
            [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  2
            [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  3
            [x, x, x, x, x, x, x, x, x, x, x, x, 4, 2, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  4
            [x, x, x, x, x, x, x, x, x, x, 5, x, 2, 0, 2, 3, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  5
            [x, x, x, x, x, x, x, x, x, x, x, 3, 1, 0, 1, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  6
            [x, x, x, x, x, x, x, x, x, 6, x, 2, 0, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  7
            [x, x, x, x, x, x, 2, x, x, x, 3, 1, 0, 1, x, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  8
            [x, x, x, x, 2, 1, 1, 1, 3, x, 2, 0, 0, 1, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  9
            [x, x, x, x, 2, 0, 0, 0, 1, 1, 2, 1, 1, 0, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 10
            [x, x, x, x, 2, 0, 0, 1, 1, 1, 2, x, 2, 0, 1, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 11
            [x, x, x, x, 1, 0, 0, 1, x, 2, 4, x, 3, 1, 3, 4, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 12
            [x, x, x, x, 2, 1, 1, 2, 2, 2, x, x, 2, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 13
            [x, x, x, x, x, 1, 1, x, 1, 1, 2, 2, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 14
            [x, x, x, x, 2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 15
        ],
        mines=99,
        probs=[
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 1,       0.80648, 0.19352, 0,       0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.36559, 0.36559, 1,       0,       0,       0,       1,       0.33333, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.36559, 0,       1,       0,       0,       0,       0,       0.33333, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.59676, 0.90324, 1,       0,       0,       0,       0,       1,       0.33333, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.33333, 0.33333, 0.33333, 0.59676, 0,       1,       0,       0,       0,       0,       0,       0.13778, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0,       0.09676, 0.90324, 0,       0.09676, 0.90324, 1,       0,       0,       0,       0,       1,       0,       0.28741, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0,       0,       0,       0,       0,       0,       1,       0,       0,       0,       0,       0,       0,       0.57481, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 1,       0,       0,       0,       0,       0,       0,       0,       0,       0,       0,       0,       0,       0.13778, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 1,       0,       0,       0,       0,       0,       0,       0,       1,       0,       0,       0,       1,       0.28741, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0,       0,       0,       0,       0,       1,       0,       0,       1,       0,       0,       0,       0,       0.35630, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0,       0,       0,       0,       0,       0,       0,       1,       1,       0,       0,       1,       1,       0.35630, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 1,       1,       0,       0,       1,       0,       0,       0,       0,       0,       0,       1,       0.5,     0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
            [0.19352, 0.19352, 0.19352, 0,       0,       0,       0,       0,       0,       0,       0,       0,       0,       0,       0,       0.5,     0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352, 0.19352],
        ],
    ),

    # Small constructed example, 2 mines per cell.
    Case(
        [
            [x, 2, x, x, x],
            [x, x, x, x, x],
            [x, 3, x, x, x],
            [x, 2, x, 4, x],
            [x, x, x, x, x],
        ],
        mines=8,
        per_cell=2,
        configs={
            (1, 1, 0, 0, 2, 0, 2, 2),
            (1, 1, 1, 0, 1, 0, 1, 3),
            (1, 1, 2, 0, 0, 0, 0, 4),
            (0, 2, 0, 0, 1, 1, 2, 2),
            (0, 2, 1, 0, 0, 1, 1, 3),
            (0, 2, 0, 1, 1, 0, 1, 3),
            (0, 2, 1, 1, 0, 0, 0, 4),
        },
        probs=[
            [0.26198, 0,       0.26198, 0.28362, 0.28362],
            [0.43912, 0.43912, 0.43912, 0.28362, 0.28362],
            [0.25696, 0,       0.44822, 0.46862, 0.46862],
            [0.25696, 0,       0.44822, 0,       0.46862],
            [0.12674, 0.12674, 0.22257, 0.46862, 0.46862],
        ],
    ),

    # Small constructed example, 3 mines per cell.
    Case(
        [
            [x, 2, x, x, x],
            [x, x, x, x, x],
            [x, 3, x, x, x],
            [x, 2, x, 4, x],
            [x, x, x, x, x],
        ],
        mines=8,
        per_cell=3,
        configs={
            (1, 1, 0, 0, 2, 0, 2, 2),
            (1, 1, 1, 0, 1, 0, 1, 3),
            (1, 1, 2, 0, 0, 0, 0, 4),
            (0, 2, 0, 0, 1, 1, 2, 2),
            (0, 2, 1, 0, 0, 1, 1, 3),
            (0, 2, 0, 1, 1, 0, 1, 3),
            (0, 2, 1, 1, 0, 0, 0, 4),
        },
        probs=[
            [0.26108, 0,       0.26108, 0.27890, 0.27890],
            [0.43952, 0.43952, 0.43952, 0.27890, 0.27890],
            [0.26361, 0,       0.44131, 0.46127, 0.46127],
            [0.26361, 0,       0.44131, 0,       0.46127],
            [0.12987, 0.12987, 0.21809, 0.46127, 0.46127],

        ],
    ),

    # Partially completed expert board, multiple mines per cell.
    # Case(
    #     [
    #       #  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29
    #         [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  0
    #         [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  1
    #         [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  2
    #         [x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  3
    #         [x, x, x, x, x, x, x, x, x, x, x, x, 4, 2, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  4
    #         [x, x, x, x, x, x, x, x, x, x, 5, x, 2, 0, 2, 3, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  5
    #         [x, x, x, x, x, x, x, x, x, x, x, 3, 1, 0, 1, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  6
    #         [x, x, x, x, x, x, x, x, x, 6, x, 2, 0, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  7
    #         [x, x, x, x, x, x, 2, x, x, x, 4, 1, 0, 1, x, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  8
    #         [x, x, x, x, 2, 1, 1, 1, 4, x, 3, 0, 0, 1, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  #  9
    #         [x, x, x, x, 2, 0, 0, 0, 1, 1, 2, 1, 1, 0, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 10
    #         [x, x, x, x, 2, 0, 0, 1, 1, 1, 2, x, 2, 0, 1, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 11
    #         [x, x, x, x, 1, 0, 0, 1, x, 2, 4, x, 3, 1, 3, 4, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 12
    #         [x, x, x, x, 2, 1, 1, 2, 2, 2, x, x, 2, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 13
    #         [x, x, x, x, x, 1, 1, x, 1, 1, 2, 2, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 14
    #         [x, x, x, x, 2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 2, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x],  # 15
    #     ],
    #     mines=99,
    #     per_cell=2,
    #     probs=[
    #         [0],
    #     ],
    # ),
]
# fmt: on


# ------------------------------------------------------------------------------
# Test logic
# ------------------------------------------------------------------------------


def assert_np_rows_equal(array1: np.ndarray, array2: np.ndarray):
    """Assert two 2D numpy arrays are equal modulo row ordering."""
    assert sorted(array1.tolist()) == sorted(array2.tolist())


@pytest.mark.parametrize("case", cases)
def test_full_flow(case: Case):
    logger.debug(
        "Using board with mines=%d, per_cell=%d:\n%s",
        case.mines,
        case.per_cell,
        case.board,
    )

    s = logic.Solver(case.board, case.mines, case.per_cell)

    # Full matrix
    if case.full_matrix is not None:
        s._full_matrix = s._find_full_matrix()
        logger.debug("Got full matrix:\n%s", s._full_matrix)
        assert_np_rows_equal(s._full_matrix.matrix, case.full_matrix)

    # Setup (if required)
    if any(x is not None for x in (case.groups, case.groups_matrix, case.configs)):
        if s._full_matrix is None:
            s._full_matrix = s._find_full_matrix()
        s._groups_matrix, inversion = s._full_matrix.unique_cols()
        s._groups = s._find_groups(inversion)
        assert np.all(s._groups_matrix.matrix[:, inversion] == s._full_matrix.matrix)

    # Groups
    if case.groups is not None:
        logger.debug("Got %d group(s)", len(s._groups))
        assert [set(g) for g in s._groups] == [set(g) for g in case.groups]

    # Groups matrix
    if case.groups_matrix is not None:
        logger.debug("Got groups matrix:\n%s", s._groups_matrix)
        assert_np_rows_equal(s._groups_matrix.matrix, case.groups_matrix)

    # Configs
    if case.configs is not None:
        cfgs = s._find_configs()
        logger.debug("Got %d config(s)", len(cfgs))
        assert set(cfgs) == case.configs

    # Full probability calculation
    probs = logic.Solver(case.board, case.mines, case.per_cell).calculate()
    assert probs == case.probs
