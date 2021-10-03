__all__ = ("Coord",)

from typing import NamedTuple


class Coord(NamedTuple):
    """Regular coordinate, an (x, y) tuple."""

    x: int
    y: int
