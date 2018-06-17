"""
callback_core.py - The controller of the callbacks

May 2018, Lewis Gaul
"""

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from minegauler.utils import GameState, CellState


class CallbackCore(QObject):
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
    # Set the state of a cell (coord and state passed in).
    set_cell = pyqtSignal(tuple, CellState)
        
        
core = CallbackCore()