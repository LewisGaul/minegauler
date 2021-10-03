# March 2018, Lewis Gaul

"""
Minesweeper board API.

"""

__all__ = ("BoardBase",)

import abc
from typing import Iterable, List

from ..shared.types import Coord_T, GameMode


class BoardBase(metaclass=abc.ABCMeta):
    """Representation of a minesweeper board, generic over the game mode."""

    mode: GameMode

    @abc.abstractmethod
    def __eq__(self, other) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def all_coords(self) -> List:
        raise NotImplementedError

    @abc.abstractmethod
    def get_nbrs(self, coord, *, include_origin: bool = False) -> Iterable:
        raise NotImplementedError

    @abc.abstractmethod
    def get_coord_at(self, x: int, y: int) -> Coord_T:
        raise NotImplementedError
