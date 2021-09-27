__all__ = ("RegularCoord",)

from typing import NamedTuple


class RegularCoord(NamedTuple):
    """Regular coord, an (x, y) tuple."""

    x: int
    y: int
