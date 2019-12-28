"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""

__all__ = ("MinegaulerGUI", "init_app", "run_app")

import sys

from PyQt5.QtWidgets import QApplication

from .main_window import MinegaulerGUI


_app = None


def init_app() -> None:
    global _app
    _app = QApplication(sys.argv)


def run_app(gui: MinegaulerGUI) -> int:
    """
    Run the GUI application.

    :param gui:
        The main PyQt GUI object.
    :return:
        Exit code.
    """
    if not _app:
        raise RuntimeError("Must create the app before running the app")

    gui.show()

    return _app.exec_()
