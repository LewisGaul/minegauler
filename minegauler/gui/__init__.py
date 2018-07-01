"""
__init__.py

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .utils import CellImageType
from .main_window import MinegaulerGUI


app = QApplication(sys.argv)