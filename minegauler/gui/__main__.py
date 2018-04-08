"""
__main__.py - Example of the basic GUI usage

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .app import MainWindow


app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())