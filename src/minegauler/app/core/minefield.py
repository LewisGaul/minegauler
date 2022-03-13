# October 2021, Lewis Gaul

"""
Minesweeper minefield API.

"""

__all__ = ("MinefieldBase",)

import abc
import logging
import random
from typing import Any, Generic, Iterable, List, Mapping, Optional, Set, TypeVar

from .board import BoardBase


logger = logging.getLogger(__name__)


C = TypeVar("C")
B = TypeVar("B", bound=BoardBase)


class MinefieldBase(Generic[C, B], metaclass=abc.ABCMeta):
    """Representation of a minesweeper minefield, generic over the coord type."""

    # At the most basic level, all the minefield needs to do is choose where mines
    # are going to be in the available cells. The simplest way to implement this
    # (and therefore easiest to make generic) is to pass in a list of coordinates
    # that can contain mines, and the minefield then just places mines in those
    # coordinates.
    # The responsibility of calculating properties of the minefield (e.g. 3bv,
    # final board, ...) can go in mode-specific implementations (e.g. subclasses).

    def __init__(
        self,
        all_coords: Iterable[C],
        *,
        mines: int,
        per_cell: int = 1,
    ):
        """
        :param all_coords:
            Iterable of coords where mines may lie.
        :param mines:
            The number of mines to randomly place.
        :param per_cell:
            Maximum number of mines per cell.
        :raise ValueError:
            If the number of mines is too high.
        """
        self.all_coords: Set[C] = set(all_coords)
        self.mines: int = mines
        self.per_cell: int = per_cell
        self.mine_coords: List[C] = []
        self._bbbv: Optional[int] = None
        self._completed_board: Optional[B] = None
        self._openings: Optional[List[List[C]]] = None
        self.populated: bool = False

        # Perform some checks on the args.
        if self.per_cell < 1:
            raise ValueError(
                f"Max mines per cell must be at least 1, got {self.per_cell}"
            )
        if self.mines < 0:
            raise ValueError(f"Number of mines must be positive, got {self.mines}")
        mine_spaces = len(self.all_coords) - 1
        if self.mines > mine_spaces * self.per_cell:
            raise ValueError(
                f"Number of mines too high: {self.mines} in {mine_spaces} "
                f"spaces with max {self.per_cell} per cell"
            )

    @classmethod
    def from_coords(
        cls,
        all_coords: Iterable[C],
        *,
        mine_coords: Iterable[C],
        per_cell: int = 1,
    ) -> "MinefieldBase":
        """
        :param all_coords:
            Iterable of coords where mines may lie.
        :param mine_coords:
            Iterable of coords containing mines.
        :param per_cell:
            Maximum number of mines per cell.
        :raise ValueError:
            If the number of mines is too high.
        """
        mine_coords = list(mine_coords)
        if any(mine_coords.count(c) > per_cell for c in mine_coords):
            raise ValueError(
                f"Max number of mines per cell is {per_cell}, too many in: "
                + ", ".join(
                    str(c) for c in mine_coords if mine_coords.count(c) > per_cell
                )
            )
        self = cls(all_coords, mines=len(mine_coords), per_cell=per_cell)
        self.mine_coords = mine_coords
        self.populated = True
        return self

    def __repr__(self):
        return f"<Minefield with {len(self.all_coords)} coords, {self.mines} mines>"

    def __getitem__(self, coord: C) -> int:
        if coord not in self.all_coords:
            raise IndexError(f"Invalid coord '{coord}'")
        return self.mine_coords.count(coord)

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        fields = ("all_coords", "mines", "mine_coords", "per_cell")
        return all(getattr(self, f) == getattr(other, f) for f in fields)

    @property
    def bbbv(self) -> int:
        if not self.populated:
            raise AttributeError("Uninitialised minefield has no 3bv")
        if self._bbbv is None:
            self._bbbv = self._calc_3bv()
        return self._bbbv

    @property
    def completed_board(self) -> B:
        if not self.populated:
            raise AttributeError("Uninitialised minefield has no openings")
        if self._completed_board is None:
            self._completed_board = self._calc_completed_board()
        return self._completed_board

    @property
    def openings(self) -> List[List[C]]:
        if not self.populated:
            raise AttributeError("Uninitialised minefield has no openings")
        if self._openings is None:
            self._openings = self._find_openings()
        return self._openings

    def populate(self, safe_coords: Optional[Iterable[C]] = None) -> None:
        """
        Randomly place mines in the available coordinates.

        :param safe_coords:
            Optional iterable of coords that should not contain a mine when
            filling the minefield.
        :return:
            A list of randomly chosen mine coords.
        :raise ValueError:
            If the number of mines is too high.
        """
        safe_coords = set(safe_coords) if safe_coords else None
        mine_spaces = len(self.all_coords) - (len(safe_coords) if safe_coords else 1)

        if self.mines > mine_spaces * self.per_cell:
            raise ValueError(
                f"Number of mines too high: {self.mines} in {mine_spaces} "
                f"spaces with max {self.per_cell} per cell"
            )

        # Get a list of coordinates which can have mines placed in them.
        # Make sure there is at least one safe cell.
        avble_set = set(self.all_coords)
        if safe_coords:
            avble_set -= safe_coords
        else:
            avble_set.remove(random.choice(tuple(avble_set)))

        avble_list = list(avble_set) * self.per_cell
        random.shuffle(avble_list)
        self.mine_coords = avble_list[: self.mines]
        self.populated = True
        logger.debug("Populated minefield with %s mines", len(self.mine_coords))

    @abc.abstractmethod
    def _calc_3bv(self) -> int:
        """Calculate the 3bv of the board."""
        raise NotImplementedError

    @abc.abstractmethod
    def _calc_completed_board(self) -> B:
        """
        Create the completed board with the flags and numbers that should be
        seen upon game completion.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _find_openings(self) -> List[List[C]]:
        """Find the openings in the completed board."""
        raise NotImplementedError

    @abc.abstractmethod
    def to_json(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def from_json(cls, obj: Mapping[str, Any]) -> "MinefieldBase":
        raise NotImplementedError
