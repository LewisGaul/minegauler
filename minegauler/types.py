"""
types.py - Type definitions

June 2018, Lewis Gaul
"""

import enum

from minegauler.utils import (Grid, CellState, GameCellMode, GameState,
    CellImageType, Struct)


class Board(Grid):
    """Board representation for handling displaying flags and openings."""
    def __init__(self, x_size, y_size):
        super().__init__(x_size, y_size, CellState.UNCLICKED)
        self.per_cell = 0
    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} board>"
    def __str__(self):
        def mapping(c):
            # Display openings with dashes.
            if c == 0:
                return '-'
            # Display the value from CellContents enum if it belongs to that class.
            if type(c) is CellState:
                if self.per_cell == 1:
                    return c.value[0]
                else:
                    return c.value
            return c
        return super().__str__(mapping, cell_size=2)

                
class GameOptionsStruct(Struct):
    elements = ['x_size', 'y_size', 'mines',
                'first_success', 'per_cell']
    defaults = {'x_size': 8, 'y_size': 8, 'mines': 10,
                'first_success': True, 'per_cell': 1}
                
class GUIOptionsStruct(Struct):
    elements = ['btn_size']
    defaults = {'btn_size': 32}

class PersistSettingsStruct(Struct):
    elements = GameOptionsStruct.elements + GUIOptionsStruct.elements
    defaults = {**GameOptionsStruct.defaults, **GUIOptionsStruct.defaults}


