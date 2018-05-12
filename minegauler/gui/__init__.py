"""
__init__.py

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .main_window import MainWindow
from .minefield_widget import MinefieldWidget
from .panel_widget import PanelWidget


app = QApplication(sys.argv)

# __all__ = ['app', 'MainWindow', 'MinefieldWidget']