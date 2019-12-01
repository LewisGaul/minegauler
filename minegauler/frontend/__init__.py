"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""
import sys

from PyQt5.QtWidgets import QApplication

from minegauler import core

from . import api
from .api import Listener
from .main_window import MinegaulerGUI
from .utils import GuiOptsStruct


__all__ = ("GuiOptsStruct", "Listener", "MinegaulerGUI", "create_gui", "run")


app = None
gui = None


def create_gui(
    ctrlr: api.AbstractController,
    gui_opts: GuiOptsStruct,
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
