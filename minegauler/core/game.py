"""
game.py - Game logic

March 2018, Lewis Gaul

Exports:
Game (class)
    Representation of a minesweeper game.
"""

import logging
import time as tm
from typing import Any, Iterable, Optional, Tuple, Union

from .board import Board
from .grid import CoordType
from .internal_types import *
from .minefield import Minefield


logger = logging.getLogger(__name__)


def check_coord(method):
    """
    wrap a method that takes a coord to check it is inside the valid range.

    :raise ValueError:
        If the coord is not valid.
    """

    @functools.wraps(method)
    def wrapped(self, coord: CoordType, *args, **kwargs):
        if not 0 <= coord[0] < self.x_size or not 0 <= coord[1] < self.y_size:
            raise ValueError(
                f"Coordinate is out of bounds, should be between (0,0) and "
                f"({self.x_size-1}, {self.y_size-1})"
            )
        return method(self, coord, *args, **kwargs)

    return wrapped


def ignore_if(
    *,
    game_state: Optional[
        Union[str, GameState, Iterable[str], Iterable[GameState]]
    ] = None,
    cell_state: Optional[Union[type, Tuple[type, ...]]] = None,
) -> Any:
    """
    Return a decorator which prevents a method from running if any of the given
    parameters are satisfied.

    Arguments:
    game_state=None (GameState | (GameState, ...) | None)
        A game state or iterable of game states to match against.
    cell_state=None (subclass of CellContentsType | (..., ...) | None)
        A cell contents type or iterable of the same to match against. The
        decorated method must take the cell coordinate as the first argument.
    """

    def decorator(method):
        # If the cell state is specified it is assumed the coord is passed in
        # as the first arg.
        if cell_state is None:

            @functools.wraps(method)
            def wrapped(self, *args, **kwargs):
                if game_state is not None and (
                    self.state == game_state or self.state in game_state
                ):
                    return
                return method(self, *args, **kwargs)

        else:

            @functools.wraps(method)
            def wrapped(self, coord, *args, **kwargs):
                if (
                    game_state is not None
                    and (self.state == game_state or self.state in game_state)
                ) or isinstance(self.board[coord], cell_state):
                    return
                return method(self, coord, *args, **kwargs)

        return wrapped

    return decorator


def ignore_if_not(
    *,
    game_state: Optional[
        Union[str, GameState, Iterable[str], Iterable[GameState]]
    ] = None,
    cell_state: Optional[Union[type, Tuple[type, ...]]] = None,
) -> Any:
    """
    Return a decorator which prevents a method from running if any of the given
    parameters are satisfied.

    Arguments:
    game_state=None (GameState | (GameState, ...) | None)
        A game state or iterable of game states to match against.
    cell_state=None (subclass of CellContentsType | (..., ...) | None)
        A cell contents type or iterable of the same to match against. The
        decorated method must take the cell coordinate as the first argument.
    """

    def decorator(method):
        # If the cell state is specified it is assumed the coord is passed in
        # as the first arg.
        if cell_state is None:

            @functools.wraps(method)
            def wrapped(self, *args, **kwargs):
                if (
                    game_state is not None
                    and self.state != game_state
                    and self.state not in game_state
                ):
                    return
                return method(self, *args, **kwargs)

        else:

            @functools.wraps(method)
            def wrapped(self, coord, *args, **kwargs):
                if (
                    game_state is not None
                    and self.state != game_state
                    and self.state not in game_state
                ) or not isinstance(self.board[coord], cell_state):
                    return
                return method(self, coord, *args, **kwargs)

        return wrapped

    return decorator


class Game:
    """
    A minesweeper game, storing a minefield and the state of a game, including
    the board and other game settings. Provides methods to start the game and
    standard interactions such as selecting or flagging a cell and chording.
    """

    def __init__(
        self,
        *,
        x_size: Optional[int] = None,
        y_size: Optional[int] = None,
        mines: Optional[int] = None,
        per_cell: Optional[int] = 1,
        lives: int = 1,
        first_success: bool = False,
        minefield: Optional[Minefield] = None,
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
        :param minefield:
            A minefield to use for the game. Takes precedence over various other
            arguments, see above.
        :raise ValueError:
            If the number of mines is too high to fit in the grid.
        """
        if minefield:
            x_size, y_size = minefield.x_size, minefield.y_size
            mines = minefield.nr_mines
            per_cell = minefield.per_cell
            first_success = False
            self.mf = minefield
        else:
            Minefield.check_enough_space(
                x_size=x_size, y_size=y_size, mines=mines, per_cell=per_cell
            )
            self.mf = None
        self.x_size, self.y_size = x_size, y_size
        self.mines = mines
        self.per_cell = per_cell
        self.lives = lives
        self.first_success = first_success
        self.board = Board(x_size, y_size)
        self.start_time = None
        self.end_time = None
        self.state = GameState.READY
        self.mines_remaining = self.mines
        self.lives_remaining = self.lives

    def get_rem_3bv(self) -> int:
        """
        Calculate the minimum remaining number of clicks needed to solve.
        """
        if self.state == GameState.WON:
            return 0
        elif self.state == GameState.READY:
            return self.mf.bbbv
        else:
            pass
            # TODO
            # lost_mf = Minefield(auto_create=False, **self.settings)
            # lost_mf.mine_coords = self.mf.mine_coords
            # # Replace any openings already found with normal clicks (ones).
            # lost_mf.completed_grid = np.where(self.grid<0,
            #                                   self.mf.completed_grid, 1)
            # # Find the openings which remain.
            # lost_mf.get_openings()
            # rem_opening_coords = [c for opening in lost_mf.openings
            #                       for c in opening]
            # # Count the number of essential clicks that have already been
            # # done by counting clicked cells minus the ones at the edge of
            # # an undiscovered opening.
            # completed_3bv = len({c for c in where_coords(self.grid >= 0)
            #                      if c not in rem_opening_coords})
            # return lost_mf.get_3bv() - completed_3bv

    def get_prop_complete(self) -> float:
        """
        Calculate the progress of solving the board using 3bv.
        """
        return (self.mf.bbbv - self.get_rem_3bv()) / self.mf.bbbv

    def get_3bvps(self) -> float:
        """
        Calculate the 3bv/s based on current progress.
        """
        if self.start_time:
            return (
                self.mf.bbbv * self.get_prop_complete() / (tm.time() - self.start_time)
            )

    def _create_minefield(self, coord: CoordType) -> None:
        """Create the minefield in response to a cell being selected."""
        if self.first_success:
            safe_coords = self.board.get_nbrs(coord, include_origin=True)
            logger.debug(
                "Trying to create minefield with the following safe coordinates: %s",
                safe_coords,
            )
            try:
                self.mf = Minefield(
                    self.x_size,
                    self.y_size,
                    mines=self.mines,
                    per_cell=self.per_cell,
                    safe_coords=safe_coords,
                )
            except ValueError:
                logger.info(
                    "Unable to give opening on the first click, "
                    "still ensuring a safe click"
                )
                # This should be guaranteed to succeed.
                self.mf = Minefield(
                    self.x_size,
                    self.y_size,
                    mines=self.mines,
                    per_cell=self.per_cell,
                    safe_coords=[coord],
                )
            else:
                logger.debug("Successfully created minefield")
        else:
            logger.debug("Creating minefield without guaranteed first click success")
            self.mf = Minefield(
                self.x_size, self.y_size, mines=self.mines, per_cell=self.per_cell
            )

    @check_coord
    @ignore_if_not(game_state=("READY", "ACTIVE"), cell_state=CellUnclicked)
    def select_cell(self, coord: CoordType) -> None:
        """
        Perform the action of selecting/clicking a cell. Game must be started
        before calling this method.
        """
        if self.state == GameState.READY:
            if not self.mf:
                self._create_minefield(coord)
            self.state = GameState.ACTIVE
            self.start_time = tm.time()
        self._select_cell_action(coord)
        if self.state != GameState.LOST:
            self._check_for_completion()

    def _select_cell_action(self, coord: CoordType) -> None:
        """
        Implementation of the action of selecting/clicking a cell.
        """
        if self.mf.cell_contains_mine(coord):
            logger.debug("Mine hit at %s", coord)
            self.board[coord] = CellHitMine(self.mf[coord])
            self.lives_remaining -= 1

            if self.lives_remaining == 0:
                logger.info("Game lost")
                self.end_time = tm.time()
                self.state = GameState.LOST

                for c in self.mf.all_coords:
                    if (
                        self.mf.cell_contains_mine(c)
                        and self.board[c] == CellUnclicked()
                    ):
                        self.board[c] = CellMine(self.mf[c])

                    elif (
                        type(self.board[c]) is CellFlag
                        and self.board[c] != self.mf.completed_board[c]
                    ):
                        self.board[c] = CellWrongFlag(self.board[c].num)
            else:
                self.mines_remaining -= self.mf[coord]
        elif self.mf.completed_board[coord] == CellNum(0):
            for full_opening in self.mf.openings:
                if coord in full_opening:
                    # Found the opening, quit the loop here.
                    logger.debug("Opening hit: %s", full_opening)
                    break
            else:
                logger.error(
                    "Coordinate %s not found in openings %s", coord, self.mf.openings
                )

            # Get the propagation of cells forming part of the opening.
            opening = set()  # Coords belonging to the opening
            check = {coord}  # Coords whose neighbours need checking
            while check:
                c = check.pop()
                unclicked_nbrs = {
                    z
                    for z in self.board.get_nbrs(c, include_origin=True)
                    if self.board[z] == CellUnclicked()
                }
                check |= {
                    z
                    for z in unclicked_nbrs - opening
                    if self.mf.completed_board[z] == CellNum(0)
                }
                opening |= unclicked_nbrs

            logger.debug("Propagated opening: %s", list(opening))
            bad_opening_cells = {}
            for c in opening:
                if self.board[c] == CellUnclicked():
                    self.board[c] = self.mf.completed_board[c]
                else:
                    bad_opening_cells[c] = self.board[c]
            if bad_opening_cells:
                logger.error(
                    "Should only have clicked cells in opening, found: %s",
                    bad_opening_cells,
                )
        else:
            logger.debug("Regular cell revealed")
            self.board[coord] = self.mf.completed_board[coord]

    @check_coord
    @ignore_if_not(game_state=("READY", "ACTIVE"), cell_state=(CellFlag, CellUnclicked))
    def set_cell_flags(self, coord: CoordType, nr_flags: int) -> None:
        """Set the number of flags in a cell."""
        if nr_flags < 0 or nr_flags > self.per_cell:
            raise ValueError(
                f"Invalid number of flags ({nr_flags}) - should be between 0 and "
                f"{self.per_cell}"
            )

        old_nr_flags = (
            0 if self.board[coord] == CellUnclicked() else self.board[coord].num
        )
        if nr_flags == 0:
            self.board[coord] = CellUnclicked()
        else:
            self.board[coord] = CellFlag(nr_flags)
        self.mines_remaining += old_nr_flags - nr_flags

    @check_coord
    @ignore_if_not(game_state="ACTIVE", cell_state=CellNum)
    def chord_on_cell(self, coord: CoordType):
        """Chord on a cell that contains a revealed number."""
        nbrs = self.board.get_nbrs(coord)
        num_flagged_nbrs = sum(
            [self.board[c].num for c in nbrs if isinstance(self.board[c], CellMineType)]
        )
        logger.debug(
            "%s flagged mine(s) around clicked cell showing number %s",
            num_flagged_nbrs,
            self.board[coord],
        )

        unclicked_nbrs = [c for c in nbrs if self.board[c] == CellUnclicked()]
        if self.board[coord] != CellNum(num_flagged_nbrs) or not unclicked_nbrs:
            return

        logger.info("Successful chording, selecting cells %s", unclicked_nbrs)
        for c in unclicked_nbrs:
            self._select_cell_action(c)

        if self.state != GameState.LOST:
            self._check_for_completion()

    def _check_for_completion(self):
        """
        Check if game is complete by comparing the board to the minefield's
        completed board. If it is, display flags in remaining unclicked cells.
        """
        # Assume (for contradiction) that game is complete.
        is_complete = True
        for c in self.mf.all_coords:
            exp_val = self.mf.completed_board[c]
            if type(exp_val) is CellNum and exp_val != self.board[c]:
                is_complete = False
                break

        if is_complete:
            logger.info("Game won")

            self.end_time = tm.time()
            self.state = GameState.WON
            self.mines_remaining = 0

            for c in self.mf.all_coords:
                if (
                    self.mf.cell_contains_mine(c)
                    and type(self.board[c]) is not CellHitMine
                ):
                    self.board[c] = CellFlag(self.mf[c])
