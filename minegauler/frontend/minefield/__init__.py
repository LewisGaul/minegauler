# April 2018, Lewis Gaul

__all__ = ("MinefieldWidget",)

import functools
import logging
import time
from typing import Callable, Iterable, List, Mapping, Optional, Set, Type

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QSizePolicy,
    QWidget,
)

from ...core import BoardBase, api
from ...shared.types import CellContents, CellImageType, Coord, GameMode
from ..state import State
from ..utils import CellUpdate_T, MouseMove
from . import regular, simulate, split_cell
from ._base import RAISED_CELL, SUNKEN_CELL, FlagAction, MinefieldWidgetImplBase


logger = logging.getLogger(__name__)


_IMPLS: Mapping[GameMode, Type[MinefieldWidgetImplBase]] = {
    GameMode.REGULAR: regular.MinefieldWidgetImpl,
    GameMode.SPLIT_CELL: split_cell.MinefieldWidgetImpl,
}


def _filter_left_and_right(mouse_event_func: Callable):
    """
    Decorator for mouse event methods to filter out buttons that aren't the
    standard left or right mouse buttons.
    """

    @functools.wraps(mouse_event_func)
    def wrapper(self, event: QMouseEvent):
        if event.button() not in [Qt.LeftButton, Qt.RightButton, Qt.NoButton]:
            return
        event = QMouseEvent(
            event.type(),
            event.localPos(),
            event.windowPos(),
            event.screenPos(),
            event.button(),
            event.buttons() & (Qt.LeftButton | Qt.RightButton),
            event.modifiers(),
            event.source(),
        )
        return mouse_event_func(self, event)

    return wrapper


class MinefieldWidget(QGraphicsView):
    """
    The minefield widget.
    """

    at_risk_signal = pyqtSignal()
    no_risk_signal = pyqtSignal()
    size_changed = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget],
        ctrlr: api.AbstractController,
        state: State,
    ):
        super().__init__(parent)
        logger.info("Initialising minefield widget")
        self._ctrlr: api.AbstractController = ctrlr
        self._state: State = state

        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setStyleSheet("border: 0px")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setMaximumSize(self.sizeHint())

        self._impl: MinefieldWidgetImplBase = _IMPLS[state.game_mode](
            self._scene, ctrlr, state
        )

        # Keep track of mouse button states.
        self._mouse_coord: Optional[Coord] = None
        self._both_mouse_buttons_pressed: bool = False
        self._await_release_all_buttons: bool = False
        self._was_double_left_click: bool = False
        self._right_drag_action: FlagAction = FlagAction.FLAG

        # Set of coords for cells which are sunken.
        self._sunken_cells: Set[Coord] = set()

        # Mouse tracking info, for simulating a played game.
        self._mouse_tracking: List[MouseMove] = []
        self._mouse_events: List[CellUpdate_T] = []
        self._first_click_time: Optional[int] = None

        self.reset()

    @property
    def _board(self) -> BoardBase:
        return self._ctrlr.board

    @property
    def _elapsed(self) -> float:
        if self._first_click_time:
            return time.time() - self._first_click_time
        else:
            self._first_click_time = time.time()
            return 0

    @property
    def x_size(self) -> int:
        return self._state.x_size

    @property
    def y_size(self) -> int:
        return self._state.y_size

    @property
    def btn_size(self) -> int:
        return self._state.btn_size

    # --------------------------------------------------------------------------
    # Qt method overrides
    # --------------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        return QSize(self.x_size * self.btn_size, self.y_size * self.btn_size)

    @_filter_left_and_right
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        coord = self._coord_from_event(event)

        # If the button pressed here is the only button down, we reset the
        # tracking variables.
        # However, if the click was outside the board, we should wait for all
        # buttons to be released before acknowledging clicks.
        if event.button() == event.buttons():
            self._both_mouse_buttons_pressed = False
            self._await_release_all_buttons = False
            self._was_double_left_click = False
            if not coord:
                self._await_release_all_buttons = True

        if self._was_double_left_click:
            self._await_release_all_buttons = True
            return
        if self._await_release_all_buttons:
            return

        self._mouse_coord = coord

        ## Bothclick
        if event.buttons() == (Qt.LeftButton | Qt.RightButton):
            logger.debug("Both mouse buttons down on cell %s", coord)
            self._both_mouse_buttons_pressed = True
            if coord:
                self.both_buttons_down(coord)
        ## Leftclick
        elif event.button() == Qt.LeftButton:
            logger.debug("Left mouse button down on cell %s", coord)
            assert coord is not None
            self.left_button_down(coord)
        ## Rightclick
        elif event.button() == Qt.RightButton:
            logger.debug("Right mouse button down on cell %s", coord)
            assert coord is not None
            self.right_button_down(coord)

        # The underlying coord may have changed.
        self._mouse_coord = self._coord_from_event(event)

    @_filter_left_and_right
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double clicks."""
        self._mouse_coord = coord = self._coord_from_event(event)

        if (
            event.button() == Qt.LeftButton
            and not self._both_mouse_buttons_pressed
            and coord
        ):
            self._was_double_left_click = True
            self.left_button_double_down(coord)
        else:
            return self.mousePressEvent(event)

        # The underlying coord may have changed.
        self._mouse_coord = self._coord_from_event(event)

    @_filter_left_and_right
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""
        coord = self._coord_from_event(event)

        # Return if the mouse wasn't moved to a different cell.
        if self._await_release_all_buttons or coord == self._mouse_coord:
            return

        self._mouse_coord = coord

        ## Double leftclick
        if self._was_double_left_click:
            if event.buttons() == Qt.LeftButton:
                self.left_button_double_move(coord)
            return

        ## Bothclick
        if event.buttons() & Qt.LeftButton and event.buttons() & Qt.RightButton:
            self.both_buttons_move(coord)
        elif not self._both_mouse_buttons_pressed or self._state.drag_select:
            ## Leftclick
            if event.buttons() & Qt.LeftButton:
                self.left_button_move(coord)
            ## Rightclick
            if event.buttons() & Qt.RightButton:
                self.right_button_move(coord)

        # The underlying coord may have changed.
        self._mouse_coord = self._coord_from_event(event)

    @_filter_left_and_right
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        if self._await_release_all_buttons and not event.buttons():
            self._await_release_all_buttons = False
            return

        coord = self._coord_from_event(event)

        ## Bothclick (one of the buttons still down)
        if self._both_mouse_buttons_pressed:
            if event.buttons():
                logger.debug("Mouse button release on cell %s after both down", coord)
                self.first_of_both_buttons_release(coord)
            if not self._state.drag_select or event.buttons() == Qt.RightButton:
                # Only right button down - no risk.
                self.no_risk_signal.emit()
        ## Left release
        elif event.button() == Qt.LeftButton and not self._was_double_left_click:
            logger.debug("Left mouse button release on cell %s", coord)
            self.left_button_release(coord)

        # Reset variables if neither of the mouse buttons are down.
        if not event.buttons():
            logger.debug("No mouse buttons down, reset variables")
            self.all_buttons_release()

        # The underlying coord may have changed.
        self._mouse_coord = self._coord_from_event(event)

    # --------------------------------------------------------------------------
    # Mouse click handlers
    # --------------------------------------------------------------------------
    def left_button_down(self, coord: Coord) -> None:
        """
        Left mouse button was pressed (single click). Change display and call
        callback functions as appropriate.
        """
        if self._state.drag_select:
            self.at_risk_signal.emit()
            self._ctrlr.select_cell(coord)
        else:
            self._sink_unclicked_cells([coord])

    def left_button_double_down(self, coord: Coord) -> None:
        """
        Left button was double clicked. Call callback to remove any flags that
        were on the cell.
        """
        if self._board[coord].is_mine_type():
            self._ctrlr.remove_cell_flags(coord)
        else:
            self._was_double_left_click = False
            self.left_button_down(coord)

    def left_button_move(self, coord: Optional[Coord]) -> None:
        """
        Left mouse button was moved after a single click. Change display as
        appropriate.
        """
        self._raise_all_sunken_cells()
        self.no_risk_signal.emit()
        if coord is not None:
            self.left_button_down(coord)

    def left_button_double_move(self, coord: Optional[Coord]) -> None:
        """
        Left mouse button moved after a double click.
        """
        if self._state.drag_select and coord is not None:
            self._ctrlr.remove_cell_flags(coord)

    def left_button_release(self, coord: Coord) -> None:
        """
        Left mouse button was released. Change display and call callback
        functions as appropriate.
        """
        self._raise_all_sunken_cells()
        self.no_risk_signal.emit()
        if not self._state.drag_select and coord is not None:
            self._ctrlr.select_cell(coord)

    def right_button_down(self, coord: Coord) -> None:
        """
        Right mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        self._right_drag_action = self._impl.right_down_action(coord)

    def right_button_move(self, coord: Optional[Coord]) -> None:
        """
        Right mouse button was moved. Change display as appropriate.
        """
        if self._state.drag_select and coord is not None:
            self._impl.right_drag_action(coord, self._right_drag_action)

    def both_buttons_down(self, coord: Coord) -> None:
        """
        Both left and right mouse buttons were pressed. Change display and call
        callback functions as appropriate.
        """
        if not self._board[coord].is_mine_type():
            self._sink_unclicked_cells(self._board.get_nbrs(coord, include_origin=True))
        if self._state.drag_select:
            self.at_risk_signal.emit()
            self._ctrlr.chord_on_cell(coord)

    def both_buttons_move(self, coord: Optional[Coord]) -> None:
        """
        Both left and right mouse buttons were moved. Change display as
        appropriate.
        """
        self._raise_all_sunken_cells()
        self.no_risk_signal.emit()
        if coord is not None:
            self.both_buttons_down(coord)

    def first_of_both_buttons_release(self, coord: Coord) -> None:
        """
        One of the mouse buttons was released after both were pressed. Change
        display and call callback functions as appropriate.
        """
        self._raise_all_sunken_cells()
        if not self._state.drag_select and coord is not None:
            self._ctrlr.chord_on_cell(coord)

    def all_buttons_release(self) -> None:
        """
        The second of the mouse buttons was released after both were pressed.
        Change display and call callback functions as appropriate.
        """
        self.no_risk_signal.emit()
        self._mouse_coord = None
        self._both_mouse_buttons_pressed = False
        self._await_release_all_buttons = False
        self._was_double_left_click = False
        self._right_drag_action = FlagAction.FLAG

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def _coord_from_event(self, event: QMouseEvent) -> Optional[Coord]:
        """
        Get cell coordinate from mouse button event.

        :param event:
            The mouse event.
        :return:
            The cell coordinate, or None if outside the board.
        """
        pos = self.mapToScene(event.pos())

        try:
            return self._board.get_coord_at(
                int(pos.x()) // self.btn_size, int(pos.y()) // self.btn_size
            )
        except ValueError:
            return None

    def _sink_unclicked_cells(self, coords: Iterable[Coord]) -> None:
        """
        Set an unclicked cell to appear sunken.
        """
        if self._state.game_status.finished():
            return
        sink_cells = {c for c in coords if self._board[c] is CellContents.Unclicked}
        if sink_cells:
            self._mouse_events.append(
                (self._elapsed, {c: SUNKEN_CELL for c in sink_cells})
            )
            self.at_risk_signal.emit()
            for c in sink_cells:
                self._set_cell_image(c, SUNKEN_CELL)
                self._sunken_cells.add(c)

    def _raise_all_sunken_cells(self) -> None:
        """
        Reset all sunken cells to appear raised.
        """
        raise_cells = {
            c for c in self._sunken_cells if self._board[c] is CellContents.Unclicked
        }
        if raise_cells:
            self._mouse_events.append(
                (self._elapsed, {c: RAISED_CELL for c in raise_cells})
            )
            for c in raise_cells:
                self._set_cell_image(c, RAISED_CELL)
                # TODO: HACK - fix hit mines in small cells in drag-select mode
                #  when using chording.
                if self._state.game_mode is GameMode.SPLIT_CELL and not c.is_split:
                    for small in c.get_small_cell_coords():
                        if small in self._board:
                            self._set_cell_image(small, self._board[small])
        self._sunken_cells.clear()

    def _set_cell_image(self, coord: Coord, state: CellContents) -> None:
        """Set the image of a cell."""
        self._impl.set_cell_image(coord, state)

    def _update_cell_images(self, img_type: CellImageType = CellImageType.ALL) -> None:
        self._impl.update_cell_images(img_type)

    def _update_size(self) -> None:
        self.setMaximumSize(self.sizeHint())
        self.setSceneRect(
            0, 0, self.x_size * self.btn_size, self.y_size * self.btn_size
        )
        self.size_changed.emit()

    def _redraw_cells(self) -> None:
        self._scene.clear()
        for coord in self._board.all_coords:
            self._set_cell_image(coord, self._board[coord])

    def switch_mode(self, mode: GameMode) -> None:
        self._impl = _IMPLS[mode](self._scene, self._ctrlr, self._state)

    def reset(self) -> None:
        """Reset all cell images and other state for a new game."""
        logger.info("Resetting minefield widget")
        self._redraw_cells()
        self._mouse_coord = None
        self._both_mouse_buttons_pressed = False
        self._await_release_all_buttons = True
        self._mouse_tracking = []
        self._mouse_events = []
        self._first_click_time = None

    def update_cells(self, cell_updates: Mapping[Coord, CellContents]) -> None:
        """
        Called to indicate some cells have changed state.

        :param cell_updates:
            A mapping of cell coordinates to their new state.
        """
        self._mouse_events.append((self._elapsed, cell_updates))
        for c, state in cell_updates.items():
            self._set_cell_image(c, state)
        # Always display cell updates as soon as possible.
        QApplication.processEvents()

    def reshape(self, x_size: int, y_size: int) -> None:
        logger.info("Resizing minefield to %sx%s", x_size, y_size)
        self._update_size()
        self._redraw_cells()

    def update_style(self, img_type: CellImageType, style: str) -> None:
        """Update the cell images."""
        logger.info("Updating %s style to '%s'", img_type.name, style)
        self._update_cell_images(img_type)
        self._redraw_cells()

    def update_btn_size(self, size: int) -> None:
        """Update the size of the cells."""
        assert size == self._state.btn_size
        self._update_cell_images()
        self._redraw_cells()
        self._update_size()

    def get_mouse_events(self) -> List[CellUpdate_T]:
        return self._mouse_events
