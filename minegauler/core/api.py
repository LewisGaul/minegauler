# September 2019, Lewis Gaul

"""
API between backend and frontends.

"""

__all__ = (
    "AbstractController",
    "AbstractListener",
    "GameInfo",
)

import abc
import logging
from typing import Callable, Dict, Iterable, List, Optional

import attr

from ..shared.types import (
    CellContents,
    Coord,
    Difficulty,
    GameMode,
    GameState,
    PathLike,
    UIMode,
)
from ..shared.utils import GameOptsStruct
from .board import BoardBase


@attr.attrs(auto_attribs=True, kw_only=True)
class GameInfo:
    """General information about a game."""

    @attr.attrs(auto_attribs=True, kw_only=True)
    class StartedInfo:
        start_time: float
        elapsed: float
        bbbv: int
        rem_bbbv: int
        bbbvps: float
        prop_complete: float
        prop_flagging: float

    game_state: GameState
    x_size: int
    y_size: int
    mines: int
    difficulty: Difficulty
    per_cell: int
    first_success: bool
    mode: GameMode

    minefield_known: bool
    started_info: Optional[StartedInfo] = None


class AbstractListener(metaclass=abc.ABCMeta):
    """
    An abstract class outlining methods that should be implemented to receive
    updates on changes to state. Instances of a concrete implementation can
    then be registered to listen for callbacks.
    """

    @abc.abstractmethod
    def reset(self) -> None:
        """
        Called to indicate the state should be reset.
        """
        return NotImplemented

    @abc.abstractmethod
    def resize_minefield(self, x_size: int, y_size: int) -> None:
        """
        Called to indicate the board is being changed.

        :param x_size:
            The number of columns.
        :param y_size:
            The number of rows.
        """
        return NotImplemented

    @abc.abstractmethod
    def set_mines(self, mines: int) -> None:
        """Called to indicate the number of base mines has changed."""
        return NotImplemented

    @abc.abstractmethod
    def set_difficulty(self, diff: Difficulty) -> None:
        """Called to indicate the difficulty has changed."""
        return NotImplemented

    @abc.abstractmethod
    def update_cells(self, cell_updates: Dict[Coord, CellContents]) -> None:
        """
        Called when one or more cells were updated.

        :param cell_updates:
            Mapping of coordinates that were changed to the new cell state.
        """
        return NotImplemented

    @abc.abstractmethod
    def update_game_state(self, game_state: GameState) -> None:
        """
        Called when the game state changes.

        :param game_state:
            The new game state.
        """
        return NotImplemented

    @abc.abstractmethod
    def update_mines_remaining(self, mines_remaining: int) -> None:
        """
        Called when the number of mines remaining changes.

        :param mines_remaining:
            The new number of mines remaining.
        """
        return NotImplemented

    @abc.abstractmethod
    def ui_mode_changed(self, mode: UIMode) -> None:
        """
        Called to indicate the UI mode has changed.

        :param mode:
            The mode to change to.
        """
        return NotImplemented

    @abc.abstractmethod
    def game_mode_about_to_change(self, mode: GameMode) -> None:
        """
        Called to indicate the game mode is about to change.

        :param mode:
            The mode to change to.
        """
        return NotImplemented

    @abc.abstractmethod
    def game_mode_changed(self, mode: GameMode) -> None:
        """
        Called to indicate the game mode has changed.

        :param mode:
            The mode to change to.
        """
        return NotImplemented

    @abc.abstractmethod
    def handle_exception(self, method: str, exc: Exception) -> None:
        """
        Called if an exception occurs when calling any of the other methods on
        the class, to allow the implementer of the class to handle (e.g. log)
        any errors.

        :param method:
            The method that the exception occurred in.
        :param exc:
            The caught exception.
        """
        return NotImplemented


class _Notifier(AbstractListener):
    """Pass on calls to registered listeners."""

    _count: int = 0

    def __init__(self, listeners: Iterable[AbstractListener] = None):
        """
        Create the implementation for all

        :param listeners:
        """
        self._listeners: List[AbstractListener] = list(listeners) if listeners else []
        self._id: int = self._count
        self._logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}[{self._id}]"
        )

        self.__class__._count += 1

        # Do the method wrapping here because we need the registered listeners.
        for method in AbstractListener.__abstractmethods__:
            setattr(self, method, self._call_registered(method))

    def register_listener(self, listener: AbstractListener) -> None:
        """
        Register a listener to receive updates from the controller.

        :param listener:
            An AbstractListener instance to register.
        """
        self._listeners.append(listener)

    def unregister_listener(self, listener: AbstractListener) -> None:
        """
        Unregister a listener to receive updates from the controller.

        Does nothing if not registered.

        :param listener:
            An AbstractListener instance to unregister.
        """
        try:
            self._listeners.remove(listener)
        except ValueError:
            self._logger.debug("Listener not registered - nothing to do")

    def _call_registered(self, func: str) -> Callable:
        """
        Decorator to call all registered listeners.

        :param func:
            The name of the method to decorate.
        :return:
            The decorated version of the method.
        """
        if not hasattr(self, func + "_orig"):
            setattr(self, func + "_orig", getattr(self, func))

        def wrapped(*args, **kwargs):
            getattr(self, func + "_orig")(*args, **kwargs)
            for listener in self._listeners:
                try:
                    getattr(listener, func)(*args, **kwargs)
                except Exception as e:
                    self._logger.warning(
                        f"Error occurred calling {func}() on {listener}"
                    )
                    listener.handle_exception(func, e)

        return wrapped

    def reset(self) -> None:
        """
        Called to indicate the state should be reset.
        """
        self._logger.debug("Calling reset()")

    def resize_minefield(self, x_size: int, y_size: int) -> None:
        """
        Called to indicate the board shape has changed.

        :param x_size:
            The number of rows.
        :param y_size:
            The number of columns.
        """
        self._logger.debug(f"Calling resize_minefield() with %s, %s", x_size, y_size)

    def set_mines(self, mines: int) -> None:
        self._logger.debug(f"Calling set_mines() with %d", mines)

    def set_difficulty(self, diff: Difficulty) -> None:
        self._logger.debug(f"Calling set_difficulty() with %s", diff)

    def update_cells(self, cell_updates: Dict[Coord, CellContents]) -> None:
        """
        Called when one or more cells were updated.

        :param cell_updates:
            Mapping of coordinates that were changed to the new cell state.
        """
        self._logger.debug(
            f"Calling update_cells() with {len(cell_updates)} updated cells"
        )

    def update_game_state(self, game_state: GameState) -> None:
        """
        Called when the game state changes.

        :param game_state:
            The new game state.
        """
        self._logger.debug(f"Calling update_game_state() with {game_state}")

    def update_mines_remaining(self, mines_remaining: int) -> None:
        """
        Called when the number of mines remaining changes.

        :param mines_remaining:
            The new number of mines remaining.
        """
        self._logger.debug(f"Calling update_mines_remaining() with {mines_remaining}")

    def ui_mode_changed(self, mode: UIMode) -> None:
        """
        Called to indicate the UI mode has changed.

        :param mode:
            The mode to change to.
        """
        self._logger.debug(f"Calling ui_mode_changed() with %r", mode.name)

    def game_mode_about_to_change(self, mode: GameMode) -> None:
        """
        Called to indicate the game mode is about to change.

        :param mode:
            The mode to change to.
        """
        self._logger.debug(f"Calling game_mode_about_to_change() with %r", mode.name)

    def game_mode_changed(self, mode: GameMode) -> None:
        """
        Called to indicate the game mode has changed.

        :param mode:
            The mode to change to.
        """
        self._logger.debug(f"Calling game_mode_changed() with %r", mode.name)

    def handle_exception(self, method: str, exc: Exception) -> None:
        """
        Not used in this class - provided only to satisfy the ABC.
        """
        return NotImplemented


class AbstractController(metaclass=abc.ABCMeta):
    """
    Abstract controller base class.

    Listeners can be registered for receiving updates.
    """

    def __init__(self, opts: GameOptsStruct):
        self._opts = GameOptsStruct.from_structs(opts)
        # The registered functions to be called with updates.
        self._notif = _Notifier()
        self._logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def register_listener(self, listener: AbstractListener) -> None:
        """
        Register a listener to receive updates from the controller.

        :param listener:
            An AbstractListener instance to register.
        """
        self._logger.info(
            "Registering listener: %s.%s",
            type(listener).__module__,
            type(listener).__name__,
        )
        self._notif.register_listener(listener)
        # TODO Implement in subclass to update with current state.

    def unregister_listener(self, listener: AbstractListener) -> None:
        """
        Unregister a listener to receive updates from the controller.

        Does nothing if not registered.

        :param listener:
            An AbstractListener instance to unregister.
        """
        self._logger.info(
            "Unregistering listener: %s.%s",
            type(listener).__module__,
            type(listener).__name__,
        )
        self._notif.unregister_listener(listener)

    # --------------------------------------------------------------------------
    # Getters
    # --------------------------------------------------------------------------
    @property
    @abc.abstractmethod
    def board(self) -> BoardBase:
        return NotImplemented

    @abc.abstractmethod
    def get_game_info(self) -> GameInfo:
        """Get information about the current game."""
        return NotImplemented

    def get_game_options(self) -> GameOptsStruct:
        return self._opts

    # --------------------------------------------------------------------------
    # Methods triggered by user interaction
    # --------------------------------------------------------------------------
    @abc.abstractmethod
    def new_game(self) -> None:
        """
        Create a new game, refresh the board state.
        """
        self._logger.info("New game requested, refreshing the board")

    @abc.abstractmethod
    def restart_game(self) -> None:
        """
        Restart the current game, refresh the board state.
        """
        self._logger.info("Restart game requested, refreshing the board")

    @abc.abstractmethod
    def select_cell(self, coord: Coord) -> None:
        """
        Select a cell for a regular click.
        """
        self._logger.debug("Cell %s selected", coord)

    @abc.abstractmethod
    def flag_cell(self, coord: Coord, *, flag_only: bool = False) -> None:
        """Select a cell for flagging."""
        self._logger.debug("Cell %s selected for flagging", coord)

    def split_cell(self, coord: Coord) -> None:
        """Split a cell - only required for split-cell mode."""
        self._logger.debug("Cell %s selected to be split", coord)

    @abc.abstractmethod
    def chord_on_cell(self, coord: Coord) -> None:
        """
        Select a cell for chording.
        """
        self._logger.debug("Cell %s selected for chording", coord)

    @abc.abstractmethod
    def remove_cell_flags(self, coord: Coord) -> None:
        """
        Remove flags in a cell, if any.
        """
        self._logger.debug("Flags in cell %s being removed", coord)

    @abc.abstractmethod
    def resize_board(self, x_size: int, y_size: int, mines: int) -> None:
        """
        Resize the board and/or change the number of mines.
        """
        self._logger.info(
            "Resizing the board to %sx%s with %s mines", x_size, y_size, mines
        )

    @abc.abstractmethod
    def set_difficulty(self, difficulty: Difficulty) -> None:
        """
        Set the size of the board and the number of mines for the given difficulty.
        """
        self._logger.info("Changing the board to difficulty %s", difficulty.name)

    @abc.abstractmethod
    def set_first_success(self, value: bool) -> None:
        """
        Set whether the first click should be a guaranteed success.
        """
        self._logger.debug("Setting first success to %s", value)

    @abc.abstractmethod
    def set_per_cell(self, value: int) -> None:
        """
        Set the maximum number of mines per cell.
        """
        self._logger.debug("Setting per cell to %s", value)

    @abc.abstractmethod
    def save_current_minefield(self, file: PathLike) -> None:
        """
        Save the current minefield to file.

        :param file:
            The location of the file to save to. Should have the extension
            ".mgb".
        """
        self._logger.debug("Saving current minefield to file: %s", file)

    @abc.abstractmethod
    def load_minefield(self, file: PathLike) -> None:
        """
        Load a minefield from file.

        :param file:
            The location of the file to load from. Should have the extension
            ".mgb".
        """
        self._logger.debug("Loading minefield from file: %s", file)

    @abc.abstractmethod
    def switch_game_mode(self, mode: GameMode) -> None:
        """
        Switch the game mode, e.g. into 'split cells' mode.
        """
        self._logger.info("Requested switch to game mode %s", mode)

    @abc.abstractmethod
    def switch_ui_mode(self, mode: UIMode) -> None:
        """
        Switch the UI mode, e.g. into 'create' mode.
        """
        self._logger.info("Requested switch to UI mode %s", mode)

    @abc.abstractmethod
    def reset_settings(self) -> None:
        """
        Reset all settings to the defaults.
        """
        self._logger.info("Requested reset of settings")
