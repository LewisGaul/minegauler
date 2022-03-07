__all__ = ("APP_DIR",)

import pathlib

import minegauler.app


# ROOT_DIR is mocked, so recalculate the package root here.
APP_DIR = pathlib.Path(minegauler.app.__file__).parent
