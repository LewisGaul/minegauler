import pathlib
import subprocess

import cffi


rust_project_path = pathlib.Path(__file__).resolve().parent.parent / "rust" / "solver"
header_path = rust_project_path / "include" / "solver.h"
lib_path = rust_project_path / "target" / "debug" / "libsolver.so"


def _read_header(file):
    return subprocess.run(
        ["cc", "-E", file], stdout=subprocess.PIPE, universal_newlines=True
    ).stdout


if __name__ == "__main__":
    ffi = cffi.FFI()
    ffi.cdef(_read_header(str(header_path)))
    lib = ffi.dlopen(str(lib_path))
    lib.hello()
