# December 2018, Lewis Gaul

"""
Available imports from the package.

Exports
-------
.. data:: ROOT_DIR
    The path to the root directory.

.. data:: SETTINGS_FILE
    The path to the settings file.

.. data:: IN_EXE
    Whether running from a packaged executable.

"""

__all__ = ("IN_EXE", "ROOT_DIR", "SETTINGS_FILE")

import pathlib
import sys


IN_EXE: bool = hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS")

ROOT_DIR: pathlib.Path
if IN_EXE:
    ROOT_DIR = pathlib.Path(__file__).parent.parent
else:
    ROOT_DIR = pathlib.Path(__file__).parent

SETTINGS_FILE: pathlib.Path = ROOT_DIR / "settings.cfg"
