# October 2021, Lewis Gaul

__all__ = ("Coord",)

from typing import Tuple

from ...shared.types import Coord as CoordBase


class Coord(Tuple[int, int], CoordBase):
    def __new__(cls, x: int, y: int):
        self = super().__new__(cls, (x, y))
        self.x = x
        self.y = y
        return self
