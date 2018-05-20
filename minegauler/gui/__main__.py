"""
__main__.py - Example of the basic GUI usage

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .main_window import MainWindow
from .panel_widget import PanelWidget
from .minefield_widget import MinefieldWidget
# from .stubs import Controller

x, y = 8, 4
app = QApplication(sys.argv)
# ctrlr = Controller(@@@)
main_window = MainWindow()
# panel_widget = PanelWidget(main_window, ctrlr)
# mf_widget = MinefieldWidget(main_window, ctrlr, btn_size=36)
# main_window.set_panel_widget(panel_widget)
# main_window.set_body_widget(mf_widget)
main_window.show()
sys.exit(app.exec_())