"""
minefield_widget.py - Minefield widget implementation

April 2018, Lewis Gaul

Exports:
  MinefieldWidget
    A minefield widget class, to be packed in a parent container. Receives
    clicks on the cells and calls any registered functions.
    Arguments:
      parent - Parent widget
      x_size - Number of columns
      y_size - Number of rows
      btn_size (optional) - Size to display the cells, in pixels
    Methods:
      register_cb(cb_name, fn) - Register a callback function
      register_all_cbs(ctrlr) - Attempt to register for all callbacks
"""

import sys
import logging

from PyQt5.QtCore import Qt, QRectF, QRect
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QAction

from minegauler.utils import CellState
from .utils import init_or_update_cell_images


# Initialise a dictionary to contain the cell images, which can only be created
#  when a QApplication has been initialised.
cell_images = {}


class MinefieldWidget(QGraphicsView):
    """
    The minefield widget.
    """
    all_cb_names = ['leftclick_cb', 'rightclick_cb', 'bothclick_cb']
    def __init__(self, parent, ctrlr, btn_size=16):
        """
        
        """
        super().__init__(parent)
        self.setStyleSheet("border: 0px")
        # self.setViewportMargins(0, 0, 0, 0)
        # self.setContentsMargins(0, 0, 0, 0)
        self.ctrlr = ctrlr
        self.board = ctrlr.board
        self.x_size, self.y_size = ctrlr.x_size, ctrlr.y_size
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
        # Keep track of mouse button states.
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        # Set of coords for cells which are sunken.
        self.sunken_cells = set()
        # Flag indicating whether mouse clicks are received.
        self.clicks_enabled = True
        # Registered callbacks.
        self.leftclick_cb_list = [ctrlr.leftclick]
        self.rightclick_cb_list = [ctrlr.rightclick]
        self.bothclick_cb_list = [ctrlr.bothclick]
        self.at_risk_cb = lambda : None
        self.no_risk_cb = lambda : None
        
    def leftclick_cb(self, coord):
        """
        A left mouse button click was received on the cell at coordinate (x, y).
        Call all registered callback functions.
        """
        for cb in self.leftclick_cb_list:
            cb(*coord)
        
    def rightclick_cb(self, coord):
        """
        A right mouse button click was received on the cell at coordinate (x, y).
        Call all registered callback functions.
        """
        for cb in self.rightclick_cb_list:
            cb(*coord)
            
    def bothclick_cb(self, coord):
        pass
            
    def register_cb(self, cb_name, fn):
        """
        Register a callback function.
        """
        getattr(self, cb_name + '_list').append(fn)
            
    def register_all_cbs(self, ctrlr):
        """
        Register a callback for each callback specified in self.all_cb_names
        using methods of the ctrlr which match the callback names. If any
        methods are missing no callback is registered and no error is raised.
        """
        for cb_name in self.all_cb_names:
            if hasattr(ctrlr, cb_name[:-3]):
                self.register_cb(cb_name, getattr(ctrlr, cb_name[:-3]))
                
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        
        # Ignore any clicks which aren't the left or right mouse buttons.
        if (event.button() not in [Qt.LeftButton, Qt.RightButton] or
            not self.clicks_enabled):
            return
            
        coord = event.x() // self.btn_size, event.y() // self.btn_size
        # Store the mouse coordinate.
        self.mouse_coord = coord
        ## Bothclick
        if (event.buttons() & Qt.LeftButton and
            event.buttons() & Qt.RightButton):
            self.both_mouse_buttons_pressed = True
            self.both_buttons_down(coord)
        ## Leftclick
        elif event.button() == Qt.LeftButton:
            self.left_button_down(coord)
        ## Rightclick
        elif event.button() == Qt.RightButton:
            self.right_button_down(coord)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        
        # Ignore any clicks which aren't the left or right mouse buttons.
        if (event.button() not in [Qt.LeftButton, Qt.RightButton] or
            not self.clicks_enabled):
            return
        
        coord = event.x() // self.btn_size, event.y() // self.btn_size        
        # Store the mouse coordinate.
        self.mouse_coord = coord
        ## Bothclick (one of the buttons still down)
        if event.buttons() & (Qt.LeftButton | Qt.RightButton):
            self.both_buttons_release(coord)
        elif not self.both_mouse_buttons_pressed:
            ## Leftclick
            if event.button() == Qt.LeftButton:
                self.left_button_release(coord)

        # Reset variables if neither of the mouse buttons are down.
        if not (event.buttons() & (Qt.LeftButton | Qt.RightButton)):
            self.mouse_coord = None
            self.both_mouse_buttons_pressed = False
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        # print(event.x(), event.y(), event.localPos(), event.windowPos())
        # import pdb; pdb.set_trace()
    
    def left_button_down(self, coord):
        """
        Left mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        self.sink_unclicked_cell(coord)
    
    def left_button_release(self, coord):
        """
        Left mouse button was released. Change display and call callback
        functions as appropriate.
        """
        self.raise_all_sunken_cells()
        self.leftclick_cb(coord)
    
    def right_button_down(self, coord):
        """
        Right mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        self.rightclick_cb(coord)
    
    def both_buttons_down(self, coord):
        """
        Both left and right mouse buttons were pressed. Change display and call
        callback functions as appropriate.
        """
        if self.board[coord] in [CellState.UNCLICKED, *CellState.NUMS]:
            for c in self.board.get_nbrs(*coord, include_origin=True):
                self.sink_unclicked_cell(c)
    
    def both_buttons_release(self, coord):
        """
        One of the mouse buttons was released after both were pressed. Change
        display and call callback functions as appropriate.
        """
        self.raise_all_sunken_cells()
        
    def refresh(self):
        """
        Reset the cell images.
        """
        for coord in self.all_coords:
            self.set_cell_image(coord, 'btn_up')
    
    def sink_unclicked_cell(self, coord):
        """Set an unclicked cell to appear sunken."""
        if self.board[coord] == CellState.UNCLICKED:
            self.set_cell_image(coord, 'btn_down')
            self.sunken_cells.add(coord)
        if self.sunken_cells:
            self.at_risk_cb()
    
    def raise_all_sunken_cells(self):
        """Reset all sunken cells to appear raised."""
        while self.sunken_cells:
            self.set_cell_image(self.sunken_cells.pop(), 'btn_up')
        self.no_risk_cb()
                
    def set_cell_image(self, coord, state):
        """
        Set the image of a cell.
        Arguments:
          coord ((x, y) tuple in grid range)
            The coordinate of the cell.
          state
            The cell_images key for the image to be set.
        """
        x, y = coord
        b = self.scene.addPixmap(cell_images[state])
        b.setPos(x*self.btn_size, y*self.btn_size)
        
    def split_cell(self, coord):
        """
        Split a cell into 4 smaller cells.
        Arguments:
          coord ((x, y) tuple in grid range)
            The coordinate of the cell.
        """
        x, y = coord
        img = cell_images['btn_up'].scaled(self.btn_size/2, self.btn_size/2)
        for i in range(2):
            for j in range(2):
                b = self.scene.addPixmap(img)
                b.setPos((x + i/2)*self.btn_size, (y + j/2)*self.btn_size)
    
            
    
       
if __name__ == '__main__':
    # from .stubs import Processor
    
    app = QApplication(sys.argv)
    # procr = Processor(None, 7, 2)
    mf_widget = MinefieldWidget(None, 7, 2, 100)
    # refresh_action = QAction('Refresh', mf_widget)
    # refresh_action.triggered.connect(mf_widget.refresh)
    # refresh_action.setShortcut('F1')
    mf_widget.show()
    sys.exit(app.exec_())