__all__ = ("Coord", "RegularCoord")

from typing import NewType, Tuple, TypeVar


Coord = TypeVar("Coord")

RegularCoord = NewType("RegularCoord", Tuple[int, int])
