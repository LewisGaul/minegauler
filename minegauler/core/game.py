# March 2018, Lewis Gaul

__all__ = (
    "GameBase",
    "GameNotStartedError",
    "check_game_started",
)

import abc
import functools
import logging
import math
import time
from typing import Callable, Dict, Iterable, Optional, Type, Union

from ..shared.types import CellContents, Coord, GameMode, GameState
from .board import BoardBase
from .minefield import MinefieldBase


logger = logging.getLogger(__name__)


def _check_coord(method: Callable) -> Callable:
    """
    Wrap a method that takes a coord to check it is inside the valid range.

    :raise ValueError:
        If the coord is not valid.
    """

    @functools.wraps(method)
    def wrapped(self: "GameBase", coord: Coord, *args, **kwargs):
        if not 0 <= coord.x < self.x_size or not 0 <= coord.y < self.y_size:
            raise ValueError(
                f"Coordinate is out of bounds, should be between (0,0) and "
                f"({self.x_size-1}, {self.y_size-1})"
            )
        return method(self, coord, *args, **kwargs)

    return wrapped


def _ignore_decorator_helper(conditions_sense, game_state, cell_state) -> Callable:
    # If the cell state is specified it is assumed the coord is passed in
    # as the first arg.
    def decorator(method: Callable) -> Callable:
        if game_state is None:
            game_states = []
        elif type(game_state) is GameState:
            game_states = [game_state]
        else:
            game_states = game_state

        if cell_state is None:
            cell_states = []
        elif cell_state in CellContents.items:
            cell_states = [cell_state]
        else:
            cell_states = cell_state

        @functools.wraps(method)
        def wrapped(game: "GameBase", coord: Coord = None, *args, **kwargs):
            conditions = [any(game.state is s for s in game_states)]
            if cell_states:
                conditions.append(
                    any(game.board[coord].is_type(s) for s in cell_states)
                )

            # fmt: off
            if (
                any(conditions) and conditions_sense
                or not all(conditions) and not conditions_sense
            ):
                return
            # fmt: on

            return method(game, coord, *args, **kwargs)

        return wrapped

    return decorator


def _ignore_if(
    *,
    game_state: Optional[Union[GameState, Iterable[GameState]]] = None,
    cell_state: Optional[Union[CellContents, Iterable[CellContents]]] = None,
) -> Callable:
    """
    Return a decorator which prevents a method from running if any of the given
    parameters are satisfied.

    Arguments:
    game_state=None (GameState | (GameState, ...) | None)
        A game state or iterable of game states to match against.
    cell_state=None (subclass of CellContents | (..., ...) | None)
        A cell contents type or iterable of the same to match against. The
        decorated method must take the cell coordinate as the first argument.
    """
    return _ignore_decorator_helper(True, game_state, cell_state)


def _ignore_if_not(
    *,
    game_state: Optional[Union[GameState, Iterable[GameState]]] = None,
    cell_state: Optional[Union[CellContents, Iterable[CellContents]]] = None,
) -> Callable:
    """
    Return a decorator which prevents a method from running if any of the given
    parameters are not satisfied.

    Arguments:
    game_state=None (GameState | (GameState, ...) | None)
        A game state or iterable of game states to match against.
    cell_state=None (subclass of CellContents | (..., ...) | None)
        A cell contents type or iterable of the same to match against. The
        decorated method must take the cell coordinate as the first argument.
    """
    return _ignore_decorator_helper(False, game_state, cell_state)


def check_game_started(method: Callable) -> Callable:
    """Check the game has been started, raising an error if not."""

    @functools.wraps(method)
    def wrapped(self: "GameBase", *args, **kwargs):
        if self.state is GameState.READY:
            raise GameNotStartedError("Minefield may not yet be created")
        assert self.start_time is not None
        return method(self, *args, **kwargs)

    return wrapped


class GameNotStartedError(Exception):
    """Game has not been started, so no minefield has been created."""


class GameBase(metaclass=abc.ABCMeta):
    """Representation of a minesweeper game, generic on the game mode."""

    mode: GameMode
    minefield_cls: Type[MinefieldBase]
    board_cls: Type[BoardBase]

    def __init__(
        self,
        *,
        x_size: int,
        y_size: int,
        mines: int,
        per_cell: int = 1,
        lives: int = 1,
        first_success: bool = False,
    ):
        self.x_size: int = x_size
        self.y_size: int = y_size
        self.board: BoardBase = self._make_board()
        self.mf: MinefieldBase = self.minefield_cls(
            self.board.all_coords, mines=mines, per_cell=per_cell
        )
        self.minefield_known: bool = False
        self.lives: int = lives
        self.first_success: bool = first_success
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.state: GameState = GameState.READY
        self.mines_remaining: int = self.mines
        self.lives_remaining: int = self.lives
        self._num_flags: int = 0

        self._cell_updates: Dict[Coord, CellContents] = dict()

    @classmethod
    def from_minefield(cls, mf: MinefieldBase, **kwargs) -> "GameBase":
        self = cls(mines=mf.mines, per_cell=mf.per_cell, **kwargs)
        self.mf = mf
        if mf.populated:
            self.minefield_known = True
        return self

    @abc.abstractmethod
    def _make_board(self) -> BoardBase:
        raise NotImplementedError

    @abc.abstractmethod
    def get_rem_3bv(self) -> int:
        """Calculate the minimum remaining number of clicks needed to solve."""
        raise NotImplementedError

    @property
    def mines(self) -> int:
        return self.mf.mines

    @property
    def per_cell(self) -> int:
        return self.mf.per_cell

    def get_prop_complete(self) -> float:
        """Calculate the progress of solving the board using 3bv."""
        rem_3bv = self.get_rem_3bv()
        try:
            return (self.mf.bbbv - rem_3bv) / self.mf.bbbv
        except ZeroDivisionError:
            # This can only occur for created boards with no safe cells,
            # which can technically never be completed.
            return 0

    def get_3bvps(self) -> float:
        """Calculate the 3bv/s based on current progress."""
        if self.get_elapsed() == 0:
            return math.inf
        return self.mf.bbbv * self.get_prop_complete() / self.get_elapsed()

    @check_game_started
    def get_elapsed(self) -> float:
        """Get the elapsed game time."""
        if self.end_time:
            return self.end_time - self.start_time
        else:
            return time.time() - self.start_time

    def get_flag_proportion(self) -> float:
        """Get the proportion of the mines that have been flagged."""
        if self.mines == 0:
            if self._num_flags > 0:
                return math.inf
            else:
                return 0
        return self._num_flags / self.mines

    def _populate_minefield(self, coord) -> None:
        """Create the minefield in response to a cell being selected."""
        if self.first_success:
            safe_coords = self.board.get_nbrs(coord, include_origin=True)
            logger.debug(
                "Trying to create minefield with the following safe coordinates: %s",
                safe_coords,
            )
            try:
                self.mf.populate(safe_coords)
            except ValueError:
                logger.info(
                    "Unable to give opening on the first click, "
                    "still ensuring a safe click"
                )
                # This should be guaranteed to succeed.
                self.mf.populate(safe_coords=[coord])
            else:
                logger.debug("Successfully created minefield")
        else:
            logger.debug("Creating minefield without guaranteed first click success")
            self.mf.populate()
