"""
probabilities.py - Probability calculations

Lewis Gaul, May 2020
"""

import pathlib
import subprocess

import cffi


rust_project_path = pathlib.Path(__file__).resolve().parent.parent / "rust" / "solver"
header_path = rust_project_path / "include" / "solver.h"
lib_path = rust_project_path / "target" / "debug" / "libsolver.so"


def _read_header(file):
    # TODO: Make this a shared util.
    return subprocess.run(
        ["cc", "-E", file], stdout=subprocess.PIPE, universal_newlines=True
    ).stdout


if __name__ == "__main__":
    ffi = cffi.FFI()
    ffi.cdef(_read_header(str(header_path)))
    lib = ffi.dlopen(str(lib_path))
    lib.hello()

    x, y = 3, 4
    board_p = ffi.new("solver_board_t *")
    cells_p = ffi.new("solver_cell_contents_t[20]")
    board_p.x_size = x
    board_p.y_size = y
    board_p.cells = cells_p
    probs_p = ffi.new("float[20]")
    rc = lib.calc_probs(board_p, probs_p)
    print("return code:", rc)

    probs = []
    for i in range(x*y):
        probs.append(probs_p[i])
    print("Probs:", probs)
