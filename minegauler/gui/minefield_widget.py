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

from PyQt5.QtCore import Qt, QRectF, QRect, pyqtSlot
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QAction

from minegauler.core import cb_core
from minegauler.types import Board
from minegauler.utils import CellState
from .utils import init_or_update_cell_images, CellImageType


logger = logging.getLogger(__name__)


class MinefieldWidget(QGraphicsView):
    """
    The minefield widget.
    """
    def __init__(self, parent, board, btn_size=16, styles=None):
        logger.info("Initialising minefield widget")
        super().__init__(parent)
        self.setStyleSheet("border: 0px")
        self.board = board
        self.x_size, self.y_size = board.x_size, board.y_size
        self.btn_size = btn_size
        if styles:
            for kw in [CellImageType.BUTTON]:
                ASSERT(kw in styles, "Missing image style")
        else:
            self.img_styles = {CellImageType.BUTTON: 'standard'}
        self.cell_images = {}
        init_or_update_cell_images(self.cell_images, btn_size, self.img_styles)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setFixedSize(self.x_size*self.btn_size, self.y_size*self.btn_size)
        # Keep track of mouse button states.
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.await_release_all_buttons = False
        # Set of coords for cells which are sunken.
        self.sunken_cells = set()
        # Flag indicating whether mouse clicks are received.
        self.clicks_enabled = True
        # Register for callbacks.
        cb_core.set_cell.connect(self.set_cell_image)
        cb_core.new_game.connect(self.refresh)
        cb_core.new_game.connect(lambda: setattr(self, 'clicks_enabled', True))
        cb_core.end_game.connect(
            lambda _: setattr(self, 'clicks_enabled', False))
        cb_core.resize_minefield.connect(self.resize)
        cb_core.change_mf_style.connect(self.update_style)
        
    def is_coord_in_grid(self, coord):
        x, y = coord
        return (0 <= x < self.x_size and 0 <= y < self.y_size)
                
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        
        # Ignore any clicks which aren't the left or right mouse buttons.
        if (event.button() not in [Qt.LeftButton, Qt.RightButton] or
            not self.clicks_enabled):
            return
        if event.button() == event.buttons():
            self.await_release_all_buttons = False
        elif self.await_release_all_buttons:
            return
            
        coord = event.x() // self.btn_size, event.y() // self.btn_size
        self.mouse_coord = coord
        ## Bothclick
        if (event.buttons() & Qt.LeftButton and
            event.buttons() & Qt.RightButton):
            logger.info("Both mouse buttons down on cell %s", coord)
            self.both_mouse_buttons_pressed = True
            self.both_buttons_down(coord)
        ## Leftclick
        elif event.button() == Qt.LeftButton:
            logger.info("Left mouse button down on cell %s", coord)
            self.left_button_down(coord)
        ## Rightclick
        elif event.button() == Qt.RightButton:
            logger.info("Right mouse button down on cell %s", coord)
            self.right_button_down(coord)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        
        coord = event.x() // self.btn_size, event.y() // self.btn_size
        if not self.is_coord_in_grid(coord):
            coord = None
            
        # Return if not the left or right mouse buttons, or if the mouse wasn't
        #  moved to a different cell.
        if (not event.buttons() & (Qt.LeftButton | Qt.RightButton) or
            not self.clicks_enabled or
            self.await_release_all_buttons or
            coord == self.mouse_coord):
            return
            
        ## Bothclick
        if (event.buttons() & Qt.LeftButton and
            event.buttons() & Qt.RightButton):
            self.both_buttons_move(coord)
        ## Leftclick
        elif not self.both_mouse_buttons_pressed:
            if event.buttons() & Qt.LeftButton:
                self.left_button_move(coord)
        
        self.mouse_coord = coord
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        
        if self.await_release_all_buttons and not event.buttons():
            self.await_release_all_buttons = False
            return
        # Ignore any clicks which aren't the left or right mouse buttons.
        if (event.button() not in [Qt.LeftButton, Qt.RightButton] or
            not self.clicks_enabled):
            return
        
        coord = event.x() // self.btn_size, event.y() // self.btn_size
        if not self.is_coord_in_grid(coord):
            coord = None
        
        ## Bothclick (one of the buttons still down)
        if event.buttons() & (Qt.LeftButton | Qt.RightButton):
            logger.info("Mouse button release on cell %s after both down",
                        coord)
            self.both_buttons_release(coord)
        elif not self.both_mouse_buttons_pressed:
            ## Leftclick
            if event.button() == Qt.LeftButton:
                logger.info("Left mouse button release on cell %s", coord)
                self.left_button_release(coord)

        # Reset variables if neither of the mouse buttons are down.
        if not (event.buttons() & (Qt.LeftButton | Qt.RightButton)):
            logger.debug("No mouse buttons down, reset variables")
            self.mouse_coord = None
            self.both_mouse_buttons_pressed = False
        
    def left_button_down(self, coord):
        """
        Left mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        self.sink_unclicked_cell(coord)

    def left_button_move(self, coord):
        """Left mouse button was moved. Change display as appropriate."""
        self.raise_all_sunken_cells()
        if coord is not None:
            self.left_button_down(coord)
    
    def left_button_release(self, coord):
        """
        Left mouse button was released. Change display and call callback
        functions as appropriate.
        """
        self.raise_all_sunken_cells()
        if coord is not None:
            cb_core.leftclick.emit(coord)
    
    def right_button_down(self, coord):
        """
        Right mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        cb_core.rightclick.emit(coord)
    
    def both_buttons_down(self, coord):
        """
        Both left and right mouse buttons were pressed. Change display and call
        callback functions as appropriate.
        """
        if self.board[coord] in [CellState.UNCLICKED, *CellState.NUMS]:
            for c in self.board.get_nbrs(*coord, include_origin=True):
                self.sink_unclicked_cell(c)
    
    def both_buttons_move(self, coord):
        """
        Both left and right mouse buttons were moved. Change display as
        appropriate.
        """
        self.raise_all_sunken_cells()
        if coord is not None:
            self.both_buttons_down(coord)
    
    def both_buttons_release(self, coord):
        """
        One of the mouse buttons was released after both were pressed. Change
        display and call callback functions as appropriate.
        """
        self.raise_all_sunken_cells()
        if coord is not None:
            cb_core.bothclick.emit(coord)
        
    @pyqtSlot()
    def refresh(self):
        """Reset all cell images and other state for a new game."""
        logger.info("Resetting minefield widget")
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.await_release_all_buttons = True
    
    def sink_unclicked_cell(self, coord):
        """Set an unclicked cell to appear sunken."""
        if self.board[coord] == CellState.UNCLICKED:
            self.set_cell_image(coord, 'btn_down')
            self.sunken_cells.add(coord)
        if self.sunken_cells:
            cb_core.at_risk.emit()
    
    def raise_all_sunken_cells(self):
        """Reset all sunken cells to appear raised."""
        while self.sunken_cells:
            self.set_cell_image(self.sunken_cells.pop(), CellState.UNCLICKED)
        cb_core.no_risk.emit()
                
    @pyqtSlot(tuple)
    def set_cell_image(self, coord, state=None):
        """
        Set the image of a cell.
        Arguments:
          coord ((x, y) tuple in grid range)
            The coordinate of the cell.
          state
            The cell_images key for the image to be set, or None to get the
            state from the board.
        """
        x, y = coord
        if not state:
            state = self.board[coord]
        b = self.scene.addPixmap(self.cell_images[state])
        b.setPos(x*self.btn_size, y*self.btn_size)
        
    def split_cell(self, coord):
        """
        Split a cell into 4 smaller cells.
        Arguments:
          coord ((x, y) tuple in grid range)
            The coordinate of the cell.
        """
        x, y = coord
        img = self.cell_images['btn_up'].scaled(self.btn_size/2,
                                                self.btn_size/2)
        for i in range(2):
            for j in range(2):
                b = self.scene.addPixmap(img)
                b.setPos((x + i/2)*self.btn_size, (y + j/2)*self.btn_size)
    
    @pyqtSlot(Board)
    def resize(self, board):
        logger.info("Resizing minefield from %sx%s to %sx%s",
                    self.x_size, self.y_size, board.x_size, board.y_size)
        self.board = board
        self.x_size, self.y_size = board.x_size, board.y_size
        self.setFixedSize(self.x_size*self.btn_size, self.y_size*self.btn_size)
        self.setSceneRect(0, 0,
                          self.x_size*self.btn_size,
                          self.y_size*self.btn_size)
        cb_core.update_window_size.emit()
    
    @pyqtSlot(CellImageType, str)
    def update_style(self, img_type, style):
        logger.info("Updating %s style to '%s'", img_type.name, style)
        self.img_styles[img_type] = style
        init_or_update_cell_images(self.cell_images, self.btn_size,
                                   self.img_styles, img_type)
        for coord in self.board.all_coords:
            self.set_cell_image(coord)

    
       
if __name__ == '__main__':
    from minegauler.core import Board
    
    app = QApplication(sys.argv)
    mf_widget = MinefieldWidget(None, Board(2, 7), 100)
    mf_widget.show()
    sys.exit(app.exec_())   