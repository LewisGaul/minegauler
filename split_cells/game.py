__all__ = ("Game", "RegularGame", "SplitCellGame")

import abc
import functools
import logging
import sys
import time
from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)


if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from minegauler.core.game import GameNotStartedError
from minegauler.shared.types import CellContents, Difficulty, GameState

from .board import Board, RegularBoard, SplitCellBoard
from .minefield import Minefield, RegularMinefield, SplitCellMinefield
from .types import GameMode, RegularCoord


logger = logging.getLogger(__name__)


_difficulty_pairs: Mapping[
    GameMode, Iterable[Tuple[Difficulty, Tuple[int, int, int]]]
] = {
    GameMode.REGULAR: [
        (Difficulty.BEGINNER, (8, 8, 10)),
        (Difficulty.INTERMEDIATE, (16, 16, 40)),
        (Difficulty.EXPERT, (30, 16, 99)),
        (Difficulty.MASTER, (30, 30, 200)),
        (Difficulty.LUDICROUS, (50, 50, 625)),
    ],
    GameMode.SPLIT_CELL: [
        (Difficulty.BEGINNER, (4, 4, 5)),
        (Difficulty.INTERMEDIATE, (8, 8, 20)),
        (Difficulty.EXPERT, (15, 8, 49)),
        (Difficulty.MASTER, (15, 15, 100)),
        (Difficulty.LUDICROUS, (25, 25, 400)),
    ],
}


def difficulty_to_values(mode: GameMode, diff: Difficulty) -> Tuple[int, int, int]:
    try:
        mapping = dict(_difficulty_pairs[mode])
    except KeyError:
        raise ValueError(f"Unknown game mode: {mode}") from None
    try:
        return mapping[diff]
    except KeyError:
        raise ValueError(f"Unknown difficulty: {diff}") from None


def difficulty_from_values(
    mode: GameMode, x_size: int, y_size: int, mines: int
) -> Difficulty:
    try:
        mapping = dict((x[1], x[0]) for x in _difficulty_pairs[mode])
    except KeyError:
        raise ValueError(f"Unknown game mode: {mode}") from None
    try:
        return mapping[(x_size, y_size, mines)]
    except KeyError:
        return Difficulty.CUSTOM


# ------------------------------------------------------------------------------
# Game classes
# ------------------------------------------------------------------------------


def _check_coord(method: Callable) -> Callable:
    """
    Wrap a method that takes a coord to check it is inside the valid range.

    :raise ValueError:
        If the coord is not valid.
    """

    @functools.wraps(method)
    def wrapped(self: "RegularGame", coord: RegularCoord, *args, **kwargs):
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
        def wrapped(game: "RegularGame", coord: RegularCoord = None, *args, **kwargs):
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


def _check_game_started(method: Callable) -> Callable:
    """Check the game has been started, raising an error if not."""

    @functools.wraps(method)
    def wrapped(self: "Game", *args, **kwargs):
        if self.state is GameState.READY:
            raise GameNotStartedError("Minefield not yet created")
        assert self.mf is not None
        assert self.start_time is not None
        return method(self, *args, **kwargs)

    return wrapped


M = TypeVar("M", bound=GameMode)


class Game(Generic[M], metaclass=abc.ABCMeta):
    """Representation of a minesweeper game, generic on the game mode."""

    mode: M
    minefield_cls: Type[Minefield]
    board_cls: Type[Board[M]]

    mf: Minefield
    board: Board[M]
    x_size: int
    y_size: int
    mines: int
    state: GameState
    start_time: Optional[float]
    end_time: Optional[float]

    @property
    def difficulty(self) -> Difficulty:
        return difficulty_from_values(self.mode, self.x_size, self.y_size, self.mines)


class RegularGame(Game[Literal[GameMode.REGULAR]]):
    """A regular minesweeper game."""

    mode = GameMode.REGULAR
    minefield_cls = RegularMinefield
    board_cls = RegularBoard

    def __init__(
        self,
        *,
        x_size: int = None,
        y_size: int = None,
        mines: int = None,
        per_cell: int = 1,
        lives: int = 1,
        first_success: bool = False,
    ):
        """
        :param x_size:
            Number of columns in the grid. Ignored if a minefield is passed in,
            since the minefield already has a size.
        :param y_size:
            Number of rows in the grid. Ignored if a minefield is passed in, since
            the minefield already has a size.
        :param mines:
            The number of mines. Ignored if a minefield is passed in, since the
            minefield should already contain a number of mines.
        :param per_cell:
            Maximum number of mines per cell. Ignored if a minefield is passed in,
            since the minefield should already refer to a max per cell.
        :param lives:
            A number of lives available during the game.
        :param first_success:
            Whether the first cell selected should be guaranteed to be safe, and
            give an opening if possible. Ignored if a minefield is passed in, as
            the minefield is not created in response to the first select, so it
            is not possible to guarantee success on the first select.
        :raise ValueError:
            If the number of mines is too high to fit in the grid.
        """
        self.minefield_known: bool = False
        self.board: RegularBoard = self.board_cls(x_size, y_size)
        self.mf: RegularMinefield = self.minefield_cls(
            self.board.all_coords, mines=mines, per_cell=per_cell
        )
        self.lives: int = lives
        self.first_success: bool = first_success
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.state: GameState = GameState.READY
        self.mines_remaining: int = self.mines
        self.lives_remaining: int = self.lives
        self._cell_updates: Dict[RegularCoord, CellContents] = dict()
        self._num_flags: int = 0

    @classmethod
    def from_minefield(cls) -> "Game":
        raise NotImplementedError  # TODO

    @property
    def x_size(self) -> int:
        return self.mf.x_size

    @property
    def y_size(self) -> int:
        return self.mf.y_size

    @property
    def mines(self) -> int:
        return self.mf.mines

    @property
    def per_cell(self) -> int:
        return self.mf.per_cell

    def _populate_minefield(self, coord: Optional[RegularCoord] = None) -> None:
        """Create the minefield in response to a cell being selected."""
        if self.first_success:
            safe_coords = self.board.get_nbrs(coord, include_origin=True)
            logger.debug(
                "Populating minefield with the following safe coordinates: %s",
                safe_coords,
            )
            try:
                self.mf.populate(safe_coords)
            except ValueError:
                logger.warning(
                    "Unable to give opening on the first click, still ensuring a safe click"
                )
                # This should be guaranteed to succeed.
                self.mf.populate([coord])
        else:
            logger.debug("Creating minefield without guaranteed first click success")
            self.mf.populate()

    def _set_cell(self, coord: RegularCoord, state: CellContents) -> None:
        """
        Set the contents of a cell and store the update.

        :param coord:
            The coordinate of the cell to set.
        :param state:
            The state to set the cell to.
        """
        self.board[coord] = state
        self._cell_updates[coord] = state

    def _select_cell_action(self, coord: RegularCoord) -> None:
        """
        Implementation of the action of selecting/clicking a cell.
        """
        if coord in self.mf.mine_coords:
            logger.debug("Mine hit at %s", coord)
            self._set_cell(coord, CellContents.HitMine(self.mf[coord]))
            self.lives_remaining -= 1

            if self.lives_remaining == 0:
                logger.info("Game lost")
                self.end_time = time.time()
                self.state = GameState.LOST

                for c in self.mf.all_coords:
                    if (
                        c in self.mf.mine_coords
                        and self.board[c] is CellContents.Unclicked
                    ):
                        self._set_cell(c, CellContents.Mine(self.mf[c]))

                    elif (
                        type(self.board[c]) is CellContents.Flag
                        and self.board[c] != self.mf.completed_board[c]
                    ):
                        self._set_cell(c, CellContents.WrongFlag(self.board[c].num))
            else:
                self.mines_remaining -= self.mf[coord]
        elif self.mf.completed_board[coord] is CellContents.Num(0):
            for full_opening in self.mf.openings:
                if coord in full_opening:
                    # Found the opening, quit the loop here.
                    logger.debug("Opening hit: %s", full_opening)
                    break
            else:
                raise RuntimeError(f"Coordinate {coord} not found in openings")

            # Get the propagation of cells forming part of the opening.
            opening = set()  # Coords belonging to the opening
            check = {coord}  # Coords whose neighbours need checking
            while check:
                c = check.pop()
                unclicked_nbrs = {
                    z
                    for z in self.board.get_nbrs(c, include_origin=True)
                    if self.board[z] is CellContents.Unclicked
                }
                check |= {
                    z
                    for z in unclicked_nbrs - opening
                    if self.mf.completed_board[z] is CellContents.Num(0)
                }
                opening |= unclicked_nbrs

            logger.debug("Propagated opening: %s", list(opening))
            for c in opening:
                self._set_cell(c, self.mf.completed_board[c])
        else:
            logger.debug("Regular cell revealed")
            self._set_cell(coord, self.mf.completed_board[coord])

    def _check_for_completion(self) -> None:
        """
        Check if game is complete by comparing the board to the minefield's
        completed board. If it is, display flags in remaining unclicked cells.
        """
        is_complete = all(
            type(self.board[c]) is CellContents.Num or c in self.mf.mine_coords
            for c in self.board.all_coords
        )

        if is_complete:
            logger.info("Game won")

            self.end_time = time.time()
            self.state = GameState.WON
            self.mines_remaining = 0

            for c in self.board.all_coords:
                if (
                    c in self.mf.mine_coords
                    and type(self.board[c]) is not CellContents.HitMine
                ):
                    self._set_cell(c, CellContents.Flag(self.mf[c]))

    @_check_coord
    @_ignore_if_not(
        game_state=(GameState.READY, GameState.ACTIVE),
        cell_state=CellContents.Unclicked,
    )
    def select_cell(self, coord: RegularCoord) -> Mapping[RegularCoord, CellContents]:
        """
        Perform the action of selecting/clicking a cell.
        """
        just_started = False
        if self.state is GameState.READY:
            if not self.mf:
                self._populate_minefield(coord)
            self.state = GameState.ACTIVE
            self.start_time = time.time()
            just_started = True
        self._select_cell_action(coord)
        if not self.state.finished():
            self._check_for_completion()
            if self.state is GameState.WON and just_started:
                self.end_time = self.start_time
        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()

    @_check_coord
    @_ignore_if_not(
        game_state=(GameState.READY, GameState.ACTIVE),
        cell_state=(CellContents.Flag, CellContents.Unclicked),
    )
    def set_cell_flags(
        self, coord: RegularCoord, nr_flags: int
    ) -> Mapping[RegularCoord, CellContents]:
        """Set the number of flags in a cell."""
        if nr_flags < 0 or nr_flags > self.per_cell:
            raise ValueError(
                f"Invalid number of flags ({nr_flags}) - should be between 0 and "
                f"{self.per_cell}"
            )

        old_nr_flags = (
            0 if self.board[coord] is CellContents.Unclicked else self.board[coord].num
        )
        if nr_flags == 0:
            self._set_cell(coord, CellContents.Unclicked)
        else:
            self._set_cell(coord, CellContents.Flag(nr_flags))
        self.mines_remaining += old_nr_flags - nr_flags
        self._num_flags += nr_flags - old_nr_flags

        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()

    @_check_coord
    @_ignore_if_not(game_state=GameState.ACTIVE, cell_state=CellContents.Num)
    def chord_on_cell(self, coord: RegularCoord) -> Mapping[RegularCoord, CellContents]:
        """Chord on a cell that contains a revealed number."""
        nbrs = self.board.get_nbrs(coord)
        num_flagged_nbrs = sum(
            [self.board[c].num for c in nbrs if self.board[c].is_mine_type()]
        )
        logger.debug(
            "%s flagged mine(s) around clicked cell showing number %s",
            num_flagged_nbrs,
            self.board[coord],
        )

        unclicked_nbrs = [c for c in nbrs if self.board[c] is CellContents.Unclicked]
        if (
            self.board[coord] != CellContents.Num(num_flagged_nbrs)
            or not unclicked_nbrs
        ):
            return dict()

        logger.info("Successful chording, selecting cells %s", unclicked_nbrs)
        for c in unclicked_nbrs:
            self._select_cell_action(c)

        if self.state != GameState.LOST:
            self._check_for_completion()

        try:
            return self._cell_updates
        finally:
            self._cell_updates = dict()


class SplitCellGame(Game[Literal[GameMode.SPLIT_CELL]]):
    """A split-cell minesweeper game."""

    mode = GameMode.SPLIT_CELL
    minefield_cls = SplitCellMinefield
    board_cls = SplitCellBoard
