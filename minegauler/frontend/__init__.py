"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""


import sys

from PyQt5.QtWidgets import QApplication

from minegauler.frontend.api import get_callback
from minegauler.frontend.main_window import MinegaulerGUI


def run(ctrlr):
    app = QApplication(sys.argv)

    gui = MinegaulerGUI(ctrlr)
    ctrlr.register_callback(get_callback(gui,
                                         gui.panel_widget,
                                         gui.body_widget))
    gui.show()

    return app.exec_()