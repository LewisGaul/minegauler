"""
This file contains only the basic GUI layout - it needs not know anything about
any of the minesweeper game settings.
"""

import sys

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QDesktopWidget,
                             QGridLayout, QPushButton)
from PyQt5.QtCore import pyqtSlot


app = QApplication(sys.argv)

class BasicGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Test 1'
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle(self.title)
        self.mainWidget = QWidget(self)
        self.setCentralWidget(self.mainWidget)
        # self.setGeometry(500, 250, 200, 300)
        self.resize(200, 100)
        self.centre()

    def centre(self):
        qr = self.frameGeometry()
        centre = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(centre)
        self.move(qr.topLeft())


class GameGUI(BasicGUI):
    def __init__(self, processor):
        super().__init__()
        self.procr = processor
        self.make_minefield()

    def make_minefield(self):
        layout = QGridLayout(self.mainWidget)
        self.buttons = []
        for j in range(self.procr.y_size):
            row = []
            for i in range(self.procr.x_size):
                b = QPushButton('B{}{}'.format(i, j), self)
                b.clicked.connect(self.centre)
                row.append(b)
                layout.addWidget(b, j, i)
            self.buttons.append(row)

    def start(self):
        self.show()
        sys.exit(app.exec_())


@pyqtSlot()
def perform_click():
    print("Clicked")


if __name__ == '__main__':
	# app = QApplication(sys.argv)
	win = BasicGUI()
	win.show()
	sys.exit(app.exec_())
