"""
minefield_widget.py - Minefield widget implementation

April 2018, Lewis Gaul
"""

import sys
import logging

from PyQt5.QtCore import Qt, QRectF, QRect
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QAction

from .utils import init_or_update_cell_images


cell_images = {}    


class MinefieldWidget(QGraphicsView):
    """
    The minefield widget.
    """
    def __init__(self, parent, procr, btn_size=16):
        """
        
        """
        super().__init__(parent)
        self.setStyleSheet("border: 0px")
        # self.setViewportMargins(0, 0, 0, 0)
        # self.setContentsMargins(0, 0, 0, 0)
        self.procr = procr
        procr.mf_ui = self
        self.x_size, self.y_size = procr.x_size, procr.y_size
        self.all_coords = [(i, j) for i in range(self.x_size)
                                                    for j in range(self.y_size)]
        self.btn_size = btn_size
        init_or_update_cell_images(cell_images, self.btn_size)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        # self.setSceneRect(0, 0, self.x_size*self.btn_size, self.y_size*self.btn_size)
        self.refresh()
        # self.fitInView(self.scene.sceneRect())
        self.setFixedSize(self.x_size*self.btn_size, self.y_size*self.btn_size)
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.mouse_buttons_down = Qt.NoButton
        
    def refresh(self):
        """
        Reset the cell images.
        """
        for i in range(self.x_size):
            for j in range(self.y_size):
                self.set_cell_image(i, j, 'btn_up')
                
    def mousePressEvent(self, event):
        """
        
        """
        x, y = event.x() // self.btn_size, event.y() // self.btn_size
        if event.buttons() & Qt.LeftButton:
            self.procr.leftclick_received(x, y)
        if event.buttons() & Qt.RightButton:
            self.procr.rightclick_received(x, y)
                
    def set_cell_image(self, x, y, state):
        """
        Set the image of a cell.
        Arguments:
          x (int, 0 <= x < self.x_size)
            The x-coordinate of the cell.
          y (int, 0 <= y < self.y_size)
            The y-coordinate of the cell.
          state (CellState)
            The cell contents to set the image for.
        """
        b = self.scene.addPixmap(cell_images[state])
        b.setPos(x*self.btn_size, y*self.btn_size)
        
    def split_cell(self, x, y):
        img = cell_images['btn_up'].scaled(self.btn_size/2, self.btn_size/2)
        for i in range(2):
            for j in range(2):
                b = self.scene.addPixmap(img)
                b.setPos((x + i/2)*self.btn_size, (y + j/2)*self.btn_size)
            
    
       
if __name__ == '__main__':
    from .stubs import Processor
    
    app = QApplication(sys.argv)
    procr = Processor(None, 7, 2)
    mf_widget = MinefieldWidget(None, procr, 100)
    # refresh_action = QAction('Refresh', mf_widget)
    # refresh_action.triggered.connect(mf_widget.refresh)
    # refresh_action.setShortcut('F1')
    mf_widget.show()
    sys.exit(app.exec_())