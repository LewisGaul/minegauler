# May 2020, Lewis Gaul

"""
Solver logic.

"""

import functools
import itertools
import logging
import math
import os
import time
from collections import defaultdict
from math import factorial as fac
from pprint import pprint
from typing import Collection, Iterable, List, Tuple, Union

import numpy as np
import scipy.optimize
import sympy

from ..core.board import Board
from ..shared.types import CellContents, Coord_T
from ..shared.utils import Grid
from .gen_probs import log_combs as get_log_combs
from .gen_probs import prob as get_unsafe_prob


_debug = os.environ.get("SOLVER_DEBUG")
logger = logging.getLogger(__name__)

# A configuration type, where each value in the tuple corresponds to the number
# of mines in the corresponding group.
_Config_T = Tuple[int, ...]


def _time(func):
    @functools.wraps(func)
    def timing_wrapper(*args, **kwargs):
        start = time.time()
        ret = func(*args, **kwargs)
        print(f"TIME {func.__name__:20s}: {time.time()-start:.2f}s")
        return ret

    return timing_wrapper


def _get_log_combs_approx(s: int, m: int, xmax: int) -> float:
    # If the max number of mines per cell is more than 1, the calculation is
    # slow as the size of the group gets large. In reality, with densities
    # generally lower than 50%, approximating with xmax=inf is reasonable, and
    # much quicker.
    if xmax > 1 and s > 8:
        if m / s > 0.3:
            logger.warning(
                "Approximating combs with xmax=inf for s=%d, m=%d, xmax=%d", s, m, xmax
            )
        return get_log_combs(s, m, xmax=m + 1)
    else:
        return get_log_combs(s, m, xmax)


def _get_unsafe_prob_approx(s: int, m: int, xmax: int) -> float:
    # If the max number of mines per cell is more than 1, the calculation is
    # slow as the size of the group gets large. In reality, with densities
    # generally lower than 50%, approximating with xmax=inf is reasonable, and
    # much quicker.
    if xmax > 1 and s > 8:
        if m / s > 0.3:
            logger.warning(
                "Approximating probs with xmax=inf for s=%d, m=%d, xmax=%d", s, m, xmax
            )
        return get_unsafe_prob(s, m, xmax=m + 1)
    else:
        return get_unsafe_prob(s, m, xmax)


class _MatrixAndVec:
    """Representation of simultaneous equations in matrix form."""

    def __init__(
        self, matrix: Union[np.ndarray, Iterable], vec: Union[np.ndarray, Iterable]
    ):
        self.matrix = np.array(matrix, int)
        self.vec = np.array(vec, int)

    def __str__(self):
        matrix_lines = [L[2:].rstrip("]") for L in str(self.matrix).splitlines()]
        vec_lines = [
            L[2:].rstrip("]") for L in str(np.array([self.vec]).T).splitlines()
        ]
        lines = (f"|{i} | {j} |" for i, j in zip(matrix_lines, vec_lines))
        return "\n".join(lines)

    @property
    def rows(self) -> int:
        return self.matrix.shape[0]

    @property
    def cols(self) -> int:
        return self.matrix.shape[1]

    def get_parts(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.matrix, self.vec

    def unique_cols(self) -> Tuple["_MatrixAndVec", Tuple[int, ...]]:
        """Return a copy without duplicate columns, with column order unchanged."""
        cols = []
        inverse = []
        for i, col in enumerate(self.matrix.T):
            for j, c in enumerate(cols):
                if np.all(c == col):
                    inverse.append(j)
                    break
            else:
                cols.append(col)
                inverse.append(len(cols) - 1)
        return self.__class__(np.array(cols).T, self.vec), tuple(inverse)

    @_time
    def rref(self) -> Tuple["_MatrixAndVec", Tuple[int, ...], Tuple[int, ...]]:
        """Convert to Reduced-Row-Echelon Form."""
        sp_matrix, fixed_cols = sympy.Matrix(self._join_matrix_vec()).rref()
        free_cols = tuple(i for i in range(self.matrix.shape[1]) if i not in fixed_cols)
        np_matrix = np.array(sp_matrix, int)
        np_matrix = np_matrix[(np_matrix != 0).any(axis=1)]
        return self._from_joined_matrix_vec(np_matrix), fixed_cols, free_cols

    def filter_rows(self, rows) -> "_MatrixAndVec":
        return self.__class__(self.matrix[rows, :], self.vec[rows])

    def filter_cols(self, cols) -> "_MatrixAndVec":
        return self.__class__(self.matrix[:, cols], self.vec)

    def where_rows(self, func) -> "_MatrixAndVec":
        joined = self._join_matrix_vec()
        return self._from_joined_matrix_vec(joined[func(joined), :])

    def max_from_ineq(self) -> Tuple[int, ...]:
        max_vals = []
        for i in range(self.cols):
            c = [-int(i == j) for j in range(self.cols)]
            res = scipy.optimize.linprog(
                c, A_ub=self.matrix, b_ub=self.vec, method="revised simplex"
            )
            max_vals.append(int(res.x[i]))
        return tuple(max_vals)

    def reduce_vec_with_vals(self, vals) -> np.ndarray:
        return self.vec - np.matmul(self.matrix, np.array(vals, dtype=int))

    def _join_matrix_vec(self) -> np.ndarray:
        return np.c_[self.matrix, self.vec]

    @classmethod
    def _from_joined_matrix_vec(cls, joined: np.ndarray) -> "_MatrixAndVec":
        return cls(joined[:, :-1], joined[:, -1])


class Solver:
    """Main solver class."""

    def __init__(self, board: Board, mines: int, per_cell: int = 1):
        self.board = board
        self.mines = mines
        self.per_cell = per_cell

        self._unclicked_cells = [
            c for c in board.all_coords if type(board[c]) is not CellContents.Num
        ]
        self._number_cells = [
            c for c in board.all_coords if type(board[c]) is CellContents.Num
        ]

        self._full_matrix = None
        self._groups_matrix = None
        self._groups = None
        self._configs = None

    @staticmethod
    def _iter_rectangular(max_values: _Config_T) -> Iterable[Coord_T]:
        yield from itertools.product(*[range(v + 1) for v in max_values])

    @_time
    def _find_full_matrix(self) -> _MatrixAndVec:
        """
        Convert the board into a set of simultaneous equations, represented
        in matrix form.
        """
        matrix_arr = []
        vec = []
        for num_coord in self._number_cells:
            num_nbrs = self.board.get_nbrs(num_coord)
            if any(c in self._unclicked_cells for c in num_nbrs):
                matrix_arr.append([int(c in num_nbrs) for c in self._unclicked_cells])
                vec.append(self.board[num_coord].num)
        matrix_arr.append([1] * len(self._unclicked_cells))
        vec.append(self.mines)
        return _MatrixAndVec(matrix_arr, vec)

    @_time
    def _find_groups(self, matrix_inverse) -> List[List[Coord_T]]:
        groups = defaultdict(list)
        for cell_ind, group_ind in enumerate(matrix_inverse):
            groups[group_ind].append(self._unclicked_cells[cell_ind])
        return list(groups.values())

    @_time
    def _find_configs(self) -> Collection[_Config_T]:
        rref_matrix, fixed_cols, free_cols = self._groups_matrix.rref()
        if _debug:
            print("RREF:")
            print(rref_matrix)
            print("Fixed:", fixed_cols)
            print("Free:", free_cols)
            print()

        # TODO: May be no need to bother with this?
        free_matrix = rref_matrix.filter_cols(free_cols)
        # if _debug:
        #     print("Free variables matrix:")
        #     print(free_matrix)
        #     print()

        free_vars_max = free_matrix.max_from_ineq()
        if _debug:
            print("Free variable max values:")
            print(free_vars_max)
            print()

        configs = set()
        cfg = [0 for _ in range(rref_matrix.cols)]
        for free_var_vals in self._iter_rectangular(free_vars_max):
            fixed_var_vals = free_matrix.reduce_vec_with_vals(free_var_vals)
            if not (fixed_var_vals >= 0).all():
                continue
            assert len(free_cols) == len(free_var_vals)
            assert len(fixed_cols) == len(fixed_var_vals)
            assert len(free_cols) + len(fixed_var_vals) == rref_matrix.cols
            assert not set(free_cols) & set(fixed_cols)
            for i, c in enumerate(free_cols):
                cfg[c] = free_var_vals[i]
            for i, c in enumerate(fixed_cols):
                cfg[c] = fixed_var_vals[i]
            configs.add(tuple(cfg))
        if _debug:
            print(f"Configurations ({len(configs)}):")
            print("\n".join(map(str, configs)))
            print()

        return configs

    @_time
    def _find_probs(self) -> Grid:
        # Probabilities associated with each configuration in list of configs.
        cfg_probs = []
        invalid_cfgs = []
        for cfg in self._configs:
            assert sum(cfg) == self.mines
            try:
                log_combs = 0
                # This is the product term in xi(cfg).
                for i, m_i in enumerate(cfg):
                    g_size = len(self._groups[i])
                    log_combs += get_log_combs(g_size, m_i, self.per_cell)
                    log_combs -= math.log(fac(m_i))
            except ValueError:
                # @@@ Deal with these better/earlier.
                logger.warning("Invalid configuration (1): %s", cfg)
                invalid_cfgs.append(cfg)
                continue
            cfg_probs.append(math.exp(log_combs))

        for cfg in invalid_cfgs:
            self._configs.remove(cfg)

        if sum(cfg_probs) == 0:
            raise RuntimeError("No valid configurations found")

        weight = sum(cfg_probs)
        for i, p in enumerate(cfg_probs):
            if p == 0:
                continue
            cfg_probs[i] = p / weight
        assert round(sum(cfg_probs), 5) == 1

        probs_grid = Grid(self.board.x_size, self.board.y_size)
        self._group_probs = []
        # Iterate over the groups, and then over the possible number of mines
        # in the group.
        for i, grp in enumerate(self._groups):
            probs = [0] * (len(grp) * self.per_cell + 1)
            unsafe_prob = 0
            for j, c in enumerate(self._configs):
                if c[i] >= len(probs):
                    logger.warning("Invalid configuration (2): %s", c)
                    continue
                probs[c[i]] += cfg_probs[j]
            for j, p in enumerate(probs):
                if p == 0:
                    continue
                unsafe_prob += p * get_unsafe_prob(len(grp), j, self.per_cell)
            unsafe_prob = round(unsafe_prob, 5)
            if not 0 <= unsafe_prob <= 1:
                logger.error("Invalid setup, got probability of %f", unsafe_prob)
                raise RuntimeError("Encountered an error in probability calculation")
            # Probability of the group containing 0, 1, 2,... mines, where the
            # number corresponds to the index.
            self._group_probs.append(tuple(probs))
            for coord in grp:
                # Avoid rounding errors.
                probs_grid[coord] = unsafe_prob

        return probs_grid

    @_time
    def calculate(self) -> Grid:
        """Perform the probability calculation."""
        self._full_matrix = self._find_full_matrix()
        # if _debug:
        #     print("Full matrix:")
        #     print(full_matrix)
        #     print()

        self._groups_matrix, matrix_inverse = self._full_matrix.unique_cols()
        if _debug:
            # This is how to get back to the original matrix:
            assert np.all(
                self._groups_matrix.matrix[:, matrix_inverse]
                == self._full_matrix.matrix
            )
            print("Groups matrix:")
            print(self._groups_matrix)
            print()

        self._groups = self._find_groups(matrix_inverse)
        if _debug:
            print(f"Groups ({len(self._groups)}):")
            pprint(
                [(i, g if len(g) <= 8 else "...") for i, g in enumerate(self._groups)]
            )
            print()

        self._configs = self._find_configs()

        return self._find_probs()
