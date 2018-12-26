"""
minefield_widgets.py - Minefield widgets

April 2018, Lewis Gaul

Exports:
MinefieldWidget
    A minefield widget class, to be packed in a parent container. Receives
    clicks on the cells and makes calls to the backend.
"""

import logging
import sys
from os.path import exists, join

from PyQt5.QtCore import Qt  # QRectF, QRect
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QAction

from minegauler.frontend.utils import CellImageType, img_dir
from minegauler.shared.internal_types import (CellFlag, CellHitMine, CellMine,
    CellNum, CellUnclicked, CellWrongFlag)


logger = logging.getLogger(__name__)


#@@@LG :'(         ... please don't look at the contents of these two functions.
def init_or_update_cell_images(cell_images, size, styles,
                               required=CellImageType.ALL):
    """
    Initialise or update the pixmap images for the minefield cells.

    Arguments:
    cell_images (dict)
        The dictionary to fill with the images.
    size (int)
        The size in pixels to make the image (square).
    required (CellImageType)
        Which images types require updating.
    """
    #@@@LG Currently only allows setting button styles.
    btn_style = styles[CellImageType.BUTTONS]
    if required & CellImageType.BUTTONS:
        cell_images['btn_up'] = make_pixmap('buttons',
                                            btn_style,
                                            'btn_up.png',
                                            size)
        cell_images['btn_down'] = make_pixmap('buttons',
                                              btn_style,
                                              'btn_down.png',
                                              size)
        cell_images[CellUnclicked()] = cell_images['btn_up']
        cell_images[CellNum(0)] = cell_images['btn_down']

    if required & (CellImageType.BUTTONS | CellImageType.NUMBERS):
        for i in range(1, 19):
            cell_images[CellNum(i)] = make_pixmap('numbers',
                                                  btn_style,
                                                  'btn_down.png',
                                                  size,
                                                  'num%d.png' % i,
                                                  7/8)

    if required & (CellImageType.BUTTONS | CellImageType.MARKERS):
        for i in range(1, 4):
            cell_images[CellFlag(i)] = make_pixmap('markers',
                                                   btn_style,
                                                   'btn_up.png',
                                                   size,
                                                   'flag%d.png' % i,
                                                   5/8)
            cell_images[CellWrongFlag] = make_pixmap('markers',
                                                            btn_style,
                                                            'btn_up.png',
                                                            size,
                                                            'cross%d.png' % i,
                                                            5/8)
            cell_images[CellMine(i)] = make_pixmap('markers',
                                                   btn_style,
                                                   'btn_down.png',
                                                   size,
                                                   'mine%d.png' % i,
                                                   7/8)
            cell_images[CellHitMine(i)] = make_pixmap('markers',
                                                      btn_style,
                                                      'btn_down_hit.png',
                                                      size,
                                                      'mine%d.png' % i,
                                                      7/8)

def make_pixmap(img_subdir, style, bg_fname, size, fg_fname=None, propn=1):
    def get_path(subdir, fname, style):
        base_path = join(img_dir, subdir)
        full_path = join(base_path, style, fname)
        if not exists(full_path):
            logger.warn(
                f'Missing image file at {full_path}, using standard style')
            full_path = join(base_path, 'standard', fname)
        return full_path
    bg_path = get_path('buttons', bg_fname, style)
    if fg_fname:
        image = QImage(bg_path).scaled(size, size,
                                       transformMode=Qt.SmoothTransformation)
        fg_size = propn * size
        fg_path = get_path(img_subdir, fg_fname, 'Standard')
        overlay = QPixmap(fg_path).scaled(fg_size, fg_size,
                                          transformMode=Qt.SmoothTransformation)
        painter = QPainter(image)
        margin = size * (1 - propn) / 2
        painter.drawPixmap(margin, margin, overlay)
        painter.end()
        image = QPixmap.fromImage(image)
    else:
        image = QPixmap(bg_path).scaled(size, size,
                                        transformMode=Qt.SmoothTransformation)
    return image



class MinefieldWidget(QGraphicsView):
    """
    The minefield widget.
    """
    def __init__(self, parent, ctrlr, btn_size=16, styles=None):
        logger.info("Initialising minefield widget")
        super().__init__(parent)
        self.setStyleSheet("border: 0px")
        self.ctrlr = ctrlr
        self.x_size, self.y_size = ctrlr.opts.x_size, ctrlr.opts.y_size
        self.btn_size = btn_size
        if styles:
            # for kw in [CellImageType.BUTTONS]:
            #     assert kw in styles, "Missing image style"
            self.img_styles = styles
        else:
            self.img_styles = {CellImageType.BUTTONS: 'standard'}
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

        for c in [(i, j) for i in range(self.x_size)
                  for j in range(self.y_size)]:
            self.set_cell_image(c, CellUnclicked())

        # Register for callbacks.
        # cb_core.set_cell.connect(self.set_cell_image)
        # cb_core.new_game.connect(self.refresh)
        # cb_core.new_game.connect(lambda: setattr(self, 'clicks_enabled', True))
        # cb_core.end_game.connect(
        #     lambda _: setattr(self, 'clicks_enabled', False))
        # cb_core.resize_minefield.connect(self.resize)
        # cb_core.change_mf_style.connect(self.update_style)
        
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

    def mouseDoubleClickEvent(self, event):
        """
        Redirect double right-clicks to be treated as two single clicks.
        """
        if event.button() == Qt.RightButton:
            return self.mousePressEvent(event)

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
        # if coord is not None:
        #     cb_core.leftclick.emit(coord)
    
    def right_button_down(self, coord):
        """
        Right mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        # cb_core.rightclick.emit(coord)
        self.ctrlr.flag_cell(coord)

    def both_buttons_down(self, coord):
        """
        Both left and right mouse buttons were pressed. Change display and call
        callback functions as appropriate.
        """
        # if isinstance(self.board[coord], (CellUnclicked, CellNum)):
        #     for c in self.board.get_nbrs(*coord, include_origin=True):
        #         self.sink_unclicked_cell(c)
        pass
    
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
        # if coord is not None:
        #     cb_core.bothclick.emit(coord)
        
    def refresh(self):
        """Reset all cell images and other state for a new game."""
        logger.info("Resetting minefield widget")
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.await_release_all_buttons = True
    
    def sink_unclicked_cell(self, coord):
        """
        Set an unclicked cell to appear sunken.
        """
        # if self.board[coord] == CellUnclicked():
        #     self.set_cell_image(coord, 'btn_down')
        #     self.sunken_cells.add(coord)
        # if self.sunken_cells:
        #     cb_core.at_risk.emit()
        pass
    
    def raise_all_sunken_cells(self):
        """Reset all sunken cells to appear raised."""
        # while self.sunken_cells:
        #     self.set_cell_image(self.sunken_cells.pop(), CellUnclicked())
        # cb_core.no_risk.emit()
        pass
                
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
    
    def resize(self, board):
        logger.info("Resizing minefield from %sx%s to %sx%s",
                    self.x_size, self.y_size, board.x_size, board.y_size)
        self.board = board
        self.x_size, self.y_size = board.x_size, board.y_size
        self.setFixedSize(self.x_size*self.btn_size, self.y_size*self.btn_size)
        self.setSceneRect(0, 0,
                          self.x_size*self.btn_size,
                          self.y_size*self.btn_size)
        # cb_core.update_window_size.emit()

    def update_style(self, img_type, style):
        logger.info("Updating %s style to '%s'", img_type.name, style)
        # self.img_styles[img_type] = style
        # init_or_update_cell_images(self.cell_images, self.btn_size,
        #                            self.img_styles, img_type)
        # for coord in self.board.all_coords:
        #     self.set_cell_image(coord)

    
       
if __name__ == '__main__':
    from minegauler.backend import Controller, GameOptsStruct
    
    app = QApplication(sys.argv)
    mf_widget = MinefieldWidget(None, Controller(GameOptsStruct()), 100)
    mf_widget.show()
    sys.exit(app.exec_())   