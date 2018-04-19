"""
minefield.py - Test timings for minefield widget

April 2018, Lewis Gaul
"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QApplication

from minegauler.gui.minefield_widget import (init_or_update_cell_images,
    cell_images)


class MinefieldWidget(QWidget):
    def __init__(self, parent, x_size, y_size, btn_size=16):
        super().__init__(parent)
        self.x_size, self.y_size = x_size, y_size
        self.all_coords = [(i, j) for i in range(self.x_size)
                                                    for j in range(self.y_size)]
        self.btn_size = btn_size
        init_or_update_cell_images(self.btn_size)        
        self.init_widget()
        self.setFixedSize(self.x_size*self.btn_size, self.y_size*self.btn_size)
        #self.get_pixmaps()
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.mouse_buttons_down = Qt.NoButton
        
    def init_widget(self):
        """
        Create the cell widgets and pack them into a grid layout.
        """
        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.buttons = []
        for j in range(self.y_size):
            row = []
            for i in range(self.x_size):
                cell = CellButton(self, i, j, self.btn_size)
                cell.setPixmap(cell_images['btn_up'])
                self.layout.addWidget(cell, j, i)
                row.append(cell)
            self.buttons.append(row)

    def set_cell_image(self, x, y, image):
        """
        Set the image of a cell.
        Arguments:
          x (int, 0 <= x < self.x_size)
            The x-coordinate of the cell.
          y (int, 0 <= y < self.y_size)
            The y-coordinate of the cell.
          image (QPixmap)
            The image to set.
        """
        self.buttons[y][x].setPixmap(image)
        
        
class CellButton(QLabel):
    def __init__(self, parent, x, y, size):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.x, self.y = x, y
    
    def mousePressEvent(self, event):
        self.setPixmap(cell_images['num'][10])
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Crashes with 200 x 100 grid.
    mf_widget = MinefieldWidget(None, 100, 100, 12)
    mf_widget.show()
    sys.exit(app.exec_())
