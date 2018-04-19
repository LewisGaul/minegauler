"""
stubs.py - Stubs for use by the GUI

April 2018, Lewis Gaul
"""

from minegauler.utils import Grid
from .utils import Board


class Processor:
    def __init__(self, ui, x_size, y_size, game_mode=None):
        self.ui = ui
        self.x_size = x_size
        self.y_size = y_size
        self.game_mode = game_mode
        self.grid = Grid(x_size, y_size)
        self.board = Board(x_size, y_size)
    
    def leftclick_received(self, x, y):
        pass
    
    def rightclick_received(self, x, y):
        pass