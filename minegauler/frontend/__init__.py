# December 2018, Lewis Gaul

"""
Available imports from the package.

"""

__all__ = ("MinegaulerGUI", "init_app", "run_app", "state")

import signal
import sys

from PyQt5.QtCore import QTimer, pyqtRemoveInputHook
from PyQt5.QtWidgets import QApplication, QWidget

from . import state
from .main_window import MinegaulerGUI


_app = None
_timer = None


def init_app() -> None:
    """Initialise the GUI application. This function is idempotent."""
    global _app
    if not QApplication.instance():
        _app = QApplication(sys.argv)
    else:
        _app = QApplication.instance()
    pyqtRemoveInputHook()


def run_app(gui: QWidget) -> int:
    """
    Run the GUI application.

    :param gui:
        The main GUI widget.
    :return:
        Exit code.
    """
    global _timer

    if not _app:
        raise RuntimeError("App must be initialised before being run")

    gui.show()

    # Create a timer to run Python code periodically, so that Ctrl+C can be caught.
    signal.signal(signal.SIGINT, lambda *args: gui.close())
    _timer = QTimer()
    _timer.timeout.connect(lambda: None)
    _timer.start(100)

    return _app.exec_()
