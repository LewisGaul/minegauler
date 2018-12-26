"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""


import sys

from PyQt5.QtWidgets import QApplication

from minegauler.frontend.main_window import MinegaulerGUI


def run(ctrlr):
    app = QApplication(sys.argv)

    gui = MinegaulerGUI(ctrlr)
    gui.show()

    return app.exec_()