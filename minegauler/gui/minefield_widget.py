"""
minefield_widget.py - Minefield widget implementation

April 2018, Lewis Gaul
"""

import os.path
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout

from .utils import img_dir


cell_images = {}

def init_or_update_cell_images(size, required='all'):
    for im_type in ['num', 'flag', 'cross', 'mine', 'hit', 'life']:
        cell_images.setdefault(im_type, {})
    if required in ['all', 'buttons']:
        cell_images['btn_up'] = make_pixmap('buttons', 'standard',
                                            'btn_up.png', size)
        cell_images['btn_down'] = make_pixmap('buttons', 'standard',
                                              'btn_down.png', size)
        cell_images['num'][0] = cell_images['btn_down']
    if required in ['all', 'numbers', 'buttons']:
        for i in range(1, 19):
            cell_images['num'][i] = make_pixmap('numbers',
                                                'standard',
                                                'btn_down.png',
                                                size,
                                                f'num{i}.png',
                                                7/8)
    if required in ['all', 'markers', 'buttons']:
        for i in range(1, 4):
            cell_images['flag'][i] = make_pixmap('markers',
                                                 'standard',
                                                 'btn_up.png',
                                                 size,
                                                 f'flag{i}.png',
                                                 5/8)
            cell_images['cross'][i] = make_pixmap('markers',
                                                  'standard',
                                                  'btn_up.png',
                                                  size,
                                                  f'cross{i}.png',
                                                  5/8)
            cell_images['mine'][i] = make_pixmap('markers',
                                                'standard',
                                                'btn_down.png',
                                                size,
                                                f'mine{i}.png',
                                                7/8)
            cell_images['hit'][i] = make_pixmap('markers',
                                                'standard',
                                                'btn_down_hit.png',
                                                size,
                                                f'mine{i}.png',
                                                7/8)
            cell_images['life'][i] = make_pixmap('markers',
                                                 'standard',
                                                 'btn_down_life.png',
                                                 size,
                                                 f'mine{i}.png',
                                                 7/8)
        
def make_pixmap(img_subdir, style, bg_fname, size, fg_fname=None, propn=1):
    def get_path(subdir, fname):
        base_path = os.path.join(img_dir, subdir)
        full_path = os.path.join(base_path, style, fname)
        if not os.path.exists(full_path):
            logging.warn(
                f'Missing image file at {full_path}, using standard style')
            full_path = os.path.join(base, 'standard', fname)
        return full_path
    bg_path = get_path('buttons', bg_fname)
    if fg_fname:
        image = QImage(bg_path).scaled(size, size,
                                       transformMode=Qt.SmoothTransformation)
        fg_size = propn * size
        fg_path = get_path(img_subdir, fg_fname)
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
    


class MinefieldWidget(QWidget):
    """
    
    """
    def __init__(self, parent, x_size, y_size, btn_size=16):
        """
        
        """
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