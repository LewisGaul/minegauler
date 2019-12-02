"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""

__all__ = ("Listener", "MinegaulerGUI", "create_gui", "run", "utils")

import sys

from PyQt5.QtWidgets import QApplication

from .. import core
from . import api, utils
from .api import Listener
from .main_window import MinegaulerGUI


app = None
gui = None


def create_gui(
    ctrlr: api.AbstractController,
    gui_opts: utils.GuiOptsStruct,
    game_opts: core.utils.GameOptsStruct,
):
    global app, gui
    app = QApplication(sys.argv)
    gui = MinegaulerGUI(ctrlr, gui_opts, game_opts)
    return gui


def run():
    if not app:
        raise RuntimeError("Must create the app before calling run")

    gui.show()

    return app.exec_()
