"""
__main__.py - Example of the basic GUI usage

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .app import MainWindow
from .minefield_widget import MinefieldWidget


app = QApplication(sys.argv)
main_window = MainWindow()
mf_widget = MinefieldWidget(main_window, 8, 4, 36)
main_window.set_body_widget(mf_widget)
main_window.show()
sys.exit(app.exec_())