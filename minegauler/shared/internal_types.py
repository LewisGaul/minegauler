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
from abc import ABC, abstractmethod



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
            
class CellNum(CellContentsType):
    """
    Number shown in a cell on a minesweeper board.
    """
    def __new__(cls, num):
        if num < 0:
            raise ValueError("Cell value cannot be negative")
        else:
            return super().__new__(cls, num)
        
class CellMineType(CellContentsType, ABC):
    """
    Abstract base class for the number of a mine type in a cell shown on a
    minesweeper board.
    """
    def __new__(cls, num):
        if num < 1:
            raise ValueError("Mine-like type intended for 1 or more mines")
        else:
            return super().__new__(cls, num)
    @abstractmethod
    def __repr__(self):
        pass
            
class CellMine(CellMineType):
    """
    Number of mines in a cell shown on a minesweeper board.
    """
    def __repr__(self):
        return f"M{self}"
            
class CellHit(CellMineType):
    """
    Number of hit mines in a cell shown on a minesweeper board.
    """
    def __repr__(self):
        return f"!{self}"

class CellFlag(CellMineType):
    """
    Number of flags in a cell shown on a minesweeper board.
    """
    def __repr__(self):
        return f"F{self}"
        
class CellWrongFlag(CellMineType):
    """
    Number of incorrect flags in a cell shown on a minesweeper board.
    """
    def __repr__(self):
        return f"X{self}"
    
        
    
class GameState(str, enum.Enum):
    """
    Enum representing the state of a game.
    """
    INVALID = 'INVALID'
    READY   = 'READY'
    ACTIVE  = 'ACTIVE'
    WON     = 'WON'
    LOST    = 'LOST'
    

class GameFlagMode(enum.Enum):
    """
    Game modes for different behaviour when flagging.
    """
    NORMAL = 'Original style'
    SPLIT  = 'Cells split instead of flagging'
    SPLIT1 = SPLIT
    SPLIT2 = 'Cells split twice'