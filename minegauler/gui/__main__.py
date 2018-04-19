"""
__main__.py - Example of the basic GUI usage

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtWidgets import QApplication

from .main_window import MainWindow
from .minefield_widget import MinefieldWidget
from .stubs import Processor


app = QApplication(sys.argv)
main_window = MainWindow()
procr = Processor(8, 4)
mf_widget = MinefieldWidget(main_window, procr, btn_size=36)
main_window.set_body_widget(mf_widget)
main_window.show()
sys.exit(app.exec_())