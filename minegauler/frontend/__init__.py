"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .api import get_callback
from .main_window import MinegaulerGUI
from .utils import GuiOptsStruct

__all__ = (GuiOptsStruct, MinegaulerGUI, get_callback)


app = None
gui = None


def create_gui(ctrlr, opts):
    global app, gui
    app = QApplication(sys.argv)
    gui = MinegaulerGUI(ctrlr, opts)
    return gui


def run():
    if not app:
        raise RuntimeError("Must create the app before calling run")

    gui.show()

    return app.exec_()
