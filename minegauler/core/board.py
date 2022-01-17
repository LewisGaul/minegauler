# March 2018, Lewis Gaul

"""
Minesweeper board API.

"""

__all__ = ("BoardBase",)

import abc
from typing import Iterable, List

from ..shared.types import CellContents, Coord, GameMode


class BoardBase(metaclass=abc.ABCMeta):
    """Representation of a minesweeper board, generic over the game mode."""

    mode: GameMode

    @abc.abstractmethod
    def __eq__(self, other) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __getitem__(self, coord: Coord) -> CellContents:
        raise NotImplementedError

    @abc.abstractmethod
    def __setitem__(self, coord: Coord, contents: CellContents) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def __contains__(self, coord: Coord) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def all_coords(self) -> List[Coord]:
        """A list of all coords currently in the board."""
        raise NotImplementedError

    @property
    def all_underlying_coords(self) -> List[Coord]:
        """A list of all underlying coords that may contain a mine."""
        return self.all_coords

    @abc.abstractmethod
    def get_nbrs(
        self, coord: Coord, *, include_origin: bool = False
    ) -> Iterable[Coord]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_coord_at(self, x: int, y: int) -> Coord:
        raise NotImplementedError
