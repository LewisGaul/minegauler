"""
enums.py - Enumerations and constant variables

March 2018, Lewis Gaul
"""

from enum import Enum


class CellContents(Enum):
    """Enumeration of cell contents aside from numbers."""
    FLAG1 = 'F1'
    FLAG2 = 'F2'
    FLAG3 = 'F3'

CellContents.FLAGS = {1: CellContents.FLAG1,
                      2: CellContents.FLAG2,
                      3: CellContents.FLAG3}
