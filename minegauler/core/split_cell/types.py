# October 2021, Lewis Gaul

__all__ = ("Coord",)

from typing import Iterable, Tuple

from ...shared.types import Coord as CoordBase


class Coord(CoordBase):
    fields = ("x", "y", "is_split")
    __slots__ = fields

    def __init__(self, x: int, y: int, is_split: bool):
        """
        :param x:
            The x coord of the underlying small cell (top-left for large cells).
        :param y:
            The y coord of the underlying small cell (top-left for large cells).
        :param is_split:
            Whether the coord corresponds to a small cell.
        """
        if not is_split and (x % 2 or y % 2):
            raise ValueError("Unsplit coords must have even values of x and y")
        self.x = x
        self.y = y
        self.is_split = is_split

    def get_small_cell_coords(self) -> Iterable["Coord"]:
        if self.is_split:
            return (self,)
        else:
            return (
                Coord(self.x, self.y, True),
                Coord(self.x + 1, self.y, True),
                Coord(self.x, self.y + 1, True),
                Coord(self.x + 1, self.y + 1, True),
            )

    def get_big_cell_coord(self) -> "Coord":
        if self.is_split:
            return Coord(self.x // 2 * 2, self.y // 2 * 2, False)
        else:
            return self

    def split(self) -> Iterable["Coord"]:
        if self.is_split:
            raise TypeError(f"Not able to split coord {(self.x, self.y)}")
        return self.get_small_cell_coords()
