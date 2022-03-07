__all__ = ("APP_DIR",)

import os
import pathlib
import sys


sys.path.insert(0, os.path.join(os.getcwd(), "src"))
import minegauler.app


# ROOT_DIR is mocked, so recalculate the package root here.
APP_DIR = pathlib.Path(minegauler.app.__file__).parent
