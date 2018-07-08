"""
callbacks.py - The controller of the callbacks

May 2018, Lewis Gaul
"""

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from .types import GameState, CellState, Board, CellImageType, SimpleNamespace


class CallbackContainer(QObject):
    # A left-click was received on a cell (coord passed in).
    leftclick = pyqtSignal(tuple)
    # A right-click was received on a cell (coord passed in).
    rightclick = pyqtSignal(tuple)
    # A 'both'-click was received on a cell (coord passed in).
    bothclick = pyqtSignal(tuple)
    # The counter showing how many mines left should be set (number passed in).
    set_mines_counter = pyqtSignal(int)
    # A new game was requested.
    new_game = pyqtSignal()
    # A new game was started.
    start_game = pyqtSignal()
    # A game ended (resulting game state passed in).
    end_game = pyqtSignal(GameState)
    # There is a risk of losing based on the click that has been made.
    at_risk = pyqtSignal()
    # There is no longer a risk of losing based on the mouse state.
    no_risk = pyqtSignal()
    # Set the state of a cell (coord passed in).
    set_cell = pyqtSignal(tuple)
    # Resize the board (new dimensions and mines passed in: x, y, mines).
    resize_board = pyqtSignal(int, int, int)
    # Resize the minefield to match the resized board (new board passed in).
    resize_minefield = pyqtSignal(Board)
    # Update the size of the window after a widget changes size.
    update_window_size = pyqtSignal()
    # Change a minefield style (element to change and new style passed in).
    change_mf_style = pyqtSignal(CellImageType, str)
    # Call to save current settings to file.
    save_settings = pyqtSignal()
        
        
cb_core = CallbackContainer()