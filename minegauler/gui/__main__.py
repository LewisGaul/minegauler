"""
__main__.py - Example of the basic GUI usage

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .main_window import MainWindow
from .minefield_widget import MinefieldWidget
# from .stubs import Controller

x, y = 8, 4
app = QApplication(sys.argv)
main_window = MainWindow()
# ctrlr = Controller(x, y)
mf_widget = MinefieldWidget(main_window, x, y, btn_size=36)
# mf_widget.register_all_cbs(ctrlr)
main_window.set_body_widget(mf_widget)
main_window.show()
sys.exit(app.exec_())