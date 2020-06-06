"""
Typing utilities.

December 2019, Lewis Gaul
"""

__all__ = ("CellContentsItem", "Coord_T")

from typing import Tuple, Type, Union


Coord_T = Tuple[int, int]

CellContentsItem = Union[Type["CellContents"], "CellContents"]
