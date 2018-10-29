"""
internal_types.py - Type definitions

June 2018, Lewis Gaul

Exports:
CellContentsType (class)
    Base class for cell contents types.
CellNum, CellFlag, CellMine, CellUnclicked (class)
    CellContentsType implementations.
GameState (Enum)
    The possible states of a game.
"""

import enum



class CellContentsType(int):
    """
    Base class for types of things to go in a minesweeper board cell. Must not
    be instantiated directly - intended to be inherited from.
    """
    def __new__(cls, num):
        if cls == CellContentsType:
            raise TypeError("CellContentsType should be inherited from and not "
                            "instantiated directly")
        else:
            return super().__new__(cls, num)            
    def __eq__(self, obj):
        if not isinstance(obj, type(self)):
            return False
        else:
            return super().__eq__(obj)
    def __add__(self, obj):
        if type(obj) is not int:
            raise ValueError("Can only add integers to cell contents types")
        else:
            return self.__class__(super().__add__(obj))
    def __sub__(self, obj):
        if type(obj) is int:
            raise ValueError(
                "Can only subtract integers from cell contents types")
        else:
            return self.__class__(super().__add__(obj))
            
class CellNum(CellContentsType):
    """
    Number shown on a minesweeper board.
    """
    def __new__(cls, num):
        if num < 0:
            raise ValueError("Cell value cannot be negative")
        else:
            return super().__new__(cls, num)
        
class CellFlag(CellContentsType):
    """
    Number of flags shown on a minesweeper board.
    """
    def __new__(cls, num):
        if num < 1:
            raise ValueError("Flag type intended for 1 or more flags")
        else:
            return super().__new__(cls, num)
    def __repr__(self):
        return f"F{self}"
            
class CellMine(CellContentsType):
    """
    Number of mines shown on a minesweeper board.
    """
    def __new__(cls, num):
        if num < 1:
            raise ValueError("Mine type intended for 1 or more mines")
        else:
            return super().__new__(cls, num)
    def __repr__(self):
        return f"M{self}"
        
class CellUnclicked(CellContentsType):
    """
    Unclicked cell on a minesweeper board.
    """
    def __new__(cls):
        return super().__new__(cls, 0)
    def __repr__(self):
        return "#"
    def __add__(self, obj):
        raise TypeError("Cannot add to unclicked cell")
    def __sub__(self, obj):
        raise TypeError("Cannot subtract from unclicked cell")
    
        
    
class GameState(enum.Enum):
    """
    Enum representing the state of a game.
    """
    READY  = enum.auto()
    ACTIVE = enum.auto()
    WON    = enum.auto()
    LOST   = enum.auto()