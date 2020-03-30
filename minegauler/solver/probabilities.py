"""
probabilities.py - Probability calculations

Lewis Gaul, May 2020
"""

import pathlib
import subprocess

import cffi

from ..core.board import Board
from ..shared.utils import Grid
from ..types import CellMine, CellMineType, CellNum, CellUnclicked


rust_project_path = pathlib.Path(__file__).resolve().parent.parent / "rust" / "solver"
header_path = rust_project_path / "include" / "solver.h"
lib_path = rust_project_path / "target" / "debug" / "libsolver.so"


def _read_header(file):
    # TODO: Make this a shared util.
    return subprocess.run(
        ["cc", "-E", file], stdout=subprocess.PIPE, universal_newlines=True
    ).stdout


class SolverFFI(cffi.FFI):
    def __init__(self):
        super().__init__()
        self.cdef(_read_header(str(header_path)))
        self.lib = self.dlopen(str(lib_path))

    def calc_probs(self, board: Board) -> Grid:
        x, y = board.x_size, board.y_size
        num_cells = x * y
        board_p = self.new("solver_board_t *")
        cells_p = self.new("solver_cell_contents_t[]", num_cells)
        board_p.x_size = x
        board_p.y_size = y
        board_p.cells = cells_p
        self._board_into_cells_array(board, cells_p)
        probs_p = self.new("float[]", num_cells)

        rc = self.lib.calc_probs(board_p, probs_p)
        if rc != self.lib.RC_SUCCESS:
            raise RuntimeError(f"Return code: {rc}")

        probs = [probs_p[i] for i in range(num_cells)]
        print("Probs:", probs)

    def _board_into_cells_array(self, board: Board, cells) -> None:
        number_names = {1: "one", 2: "two", 3: "three"}
        for i, coord in enumerate(board.all_coords):
            val = board[coord]
            if isinstance(val, CellNum) and 0 <= val.num <= 8:
                cells[i] = val.num
            elif isinstance(val, CellMineType) and 1 <= val.num <= 3:
                enum_name = "SOLVER_CELL_{}_MINE".format(number_names[val.num].upper())
                cells[i] = getattr(self.lib, enum_name)
            elif isinstance(val, CellUnclicked):
                cells[i] = self.lib.SOLVER_CELL_UNKNOWN
            else:
                raise ValueError(f"Unsupported board cell contents: {val}")


board = Board(5, 5)
board[(0, 0)] = CellMine(1)
board[(2, 2)] = CellNum(1)
board[(2, 3)] = CellNum(2)
SolverFFI().calc_probs(board)
