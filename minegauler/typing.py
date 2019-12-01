"""
typing.py - Typing utilities

December 2019, Lewis Gaul
"""

__all__ = ("Coord_T", "IterableContainer")

from typing import Container, Iterable, Protocol, Tuple


Coord_T = Tuple[int, int]


class IterableContainer(Iterable, Container, Protocol):
    """An iterable that is also a container."""
