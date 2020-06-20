# April 2018, Lewis Gaul

"""
Minefield widgets.

Exports
-------
.. class:: MinefieldWidget
    The minefield widget class.

"""

__all__ = ("MinefieldWidget",)

import logging
import time
from typing import Dict, List, Mapping, Optional, Set

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QMouseEvent, QPainter, QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QSizePolicy, QWidget

from ..core import Board, api
from ..shared.types import CellContents, CellImageType, Coord_T
from .state import State
from .utils import IMG_DIR, ClickEvent, MouseEvent, MouseMove


logger = logging.getLogger(__name__)

_SUNKEN_CELL = CellContents.Num(0)
_RAISED_CELL = CellContents.Unclicked


def _update_cell_images(
    cell_images: Dict[CellContents, QPixmap],
    size: int,
    styles: Dict[CellImageType, str],
    required: CellImageType = CellImageType.ALL,
) -> None:
    """
    Initialise or update the pixmap images for the minefield cells.

    Arguments:
    cell_images (dict)
        The dictionary to fill with the images.
    size (int)
        The size in pixels to make the image (square).
    required (CellImageType)
        Which images types require updating.
    """
    # Currently only allows setting button styles.
    btn_style = styles[CellImageType.BUTTONS]
    if required & CellImageType.BUTTONS:
        cell_images[_RAISED_CELL] = _make_pixmap(
            "buttons", btn_style, "btn_up.png", size
        )
        cell_images[_SUNKEN_CELL] = _make_pixmap(
            "buttons", btn_style, "btn_down.png", size
        )
    if required & (CellImageType.BUTTONS | CellImageType.NUMBERS):
        for i in range(1, 19):
            cell_images[CellContents.Num(i)] = _make_pixmap(
                "numbers", btn_style, "btn_down.png", size, "num%d.png" % i, 7 / 8
            )
    if required & (CellImageType.BUTTONS | CellImageType.MARKERS):
        for i in range(1, 4):
            cell_images[CellContents.Flag(i)] = _make_pixmap(
                "markers", btn_style, "btn_up.png", size, "flag%d.png" % i, 5 / 8
            )
            cell_images[CellContents.WrongFlag(i)] = _make_pixmap(
                "markers", btn_style, "btn_up.png", size, "cross%d.png" % i, 5 / 8
            )
            cell_images[CellContents.Mine(i)] = _make_pixmap(
                "markers", btn_style, "btn_down.png", size, "mine%d.png" % i, 7 / 8
            )
            cell_images[CellContents.HitMine(i)] = _make_pixmap(
                "markers", btn_style, "btn_down_hit.png", size, "mine%d.png" % i, 7 / 8
            )


def _make_pixmap(
    img_subdir: str,
    style: str,
    bg_fname: str,
    size: int,
    fg_fname: Optional[str] = None,
    propn: float = 1.0,
) -> QPixmap:
    def get_path(subdir, fname, style) -> str:
        base_path = IMG_DIR / subdir
        full_path = base_path / style / fname
        if not full_path.exists():
            logger.warning(f"Missing image file at {full_path}, using standard style")
            full_path = base_path / "standard" / fname
        return str(full_path)

    bg_path = get_path("buttons", bg_fname, style)
    if fg_fname:
        image = QImage(bg_path).scaled(
            size, size, transformMode=Qt.SmoothTransformation
        )
        fg_size = int(propn * size)
        fg_path = get_path(img_subdir, fg_fname, "Standard")
        overlay = QPixmap(fg_path).scaled(
            fg_size, fg_size, transformMode=Qt.SmoothTransformation
        )
        painter = QPainter(image)
        margin = int(size * (1 - propn) / 2)
        painter.drawPixmap(margin, margin, overlay)
        painter.end()
        image = QPixmap.fromImage(image)
    else:
        image = QPixmap(bg_path).scaled(
            size, size, transformMode=Qt.SmoothTransformation
        )
    return image


class MinefieldWidget(QGraphicsView):
    """
    The minefield widget.
    """

    at_risk_signal = pyqtSignal()
    no_risk_signal = pyqtSignal()
    size_changed = pyqtSignal()

    def __init__(
        self, parent: Optional[QWidget], ctrlr: api.AbstractController, state: State,
    ):
        super().__init__(parent)
        logger.info("Initialising minefield widget")
        self._ctrlr: api.AbstractController = ctrlr
        self._state: State = state
        self._cell_images: Dict[CellContents, QPixmap] = {}
        _update_cell_images(self._cell_images, self.btn_size, self._state.styles)

        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setStyleSheet("border: 0px")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setMaximumSize(self.sizeHint())

        # Keep track of mouse button states.
        self._mouse_coord = None
        self._both_mouse_buttons_pressed = False
        self._await_release_all_buttons = False
        self._was_double_left_click = False
        self._unflag_on_right_drag = False

        # Set of coords for cells which are sunken.
        self._sunken_cells: Set = set()

        # Mouse tracking info, for simulating a played game.
        self._enable_mouse_tracking: bool = True
        self._mouse_tracking: List[MouseMove] = []
        self._mouse_events: List[MouseEvent] = []
        self._first_click_time: Optional[int] = None

        self.reset()

    @property
    def _board(self) -> Board:
        return self._ctrlr.board

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

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        # Ignore any clicks which aren't the left or right mouse buttons.
        if event.button() not in [Qt.LeftButton, Qt.RightButton]:
            return
        if event.button() == event.buttons():
            self._await_release_all_buttons = False
            self._both_mouse_buttons_pressed = False
        elif self._await_release_all_buttons:
            return
        if self._was_double_left_click:
            return

        self._mouse_coord = coord = self._coord_from_event(event)
        if not self._first_click_time:
            self._first_click_time = time.time()
            assert len(self._mouse_tracking) == 0
            assert len(self._mouse_events) == 0
            self._mouse_tracking.append(MouseMove(0, (event.x(), event.y())))

        ## Bothclick
        if event.buttons() & Qt.LeftButton and event.buttons() & Qt.RightButton:
            logger.debug("Both mouse buttons down on cell %s", coord)
            self._both_mouse_buttons_pressed = True
            self.both_buttons_down(coord)
        ## Leftclick
        elif event.button() == Qt.LeftButton:
            logger.debug("Left mouse button down on cell %s", coord)
            self._was_double_left_click = False
            self.left_button_down(coord)
        ## Rightclick
        elif event.button() == Qt.RightButton:
            logger.debug("Right mouse button down on cell %s", coord)
            self.right_button_down(coord)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double clicks."""
        self._mouse_coord = coord = self._coord_from_event(event)

        if event.button() == Qt.LeftButton and not self._both_mouse_buttons_pressed:
            self._was_double_left_click = True
            self.left_button_double_down(coord)
        else:
            return self.mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""
        coord = self._coord_from_event(event)

        # Return if not the left or right mouse buttons, or if the mouse wasn't
        #  moved to a different cell.
        if (
            not event.buttons() & int(Qt.LeftButton | Qt.RightButton)
            or self._await_release_all_buttons
            or coord == self._mouse_coord
        ):
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

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        if self._await_release_all_buttons and not event.buttons():
            self._await_release_all_buttons = False
            return
        # Ignore any clicks which aren't the left or right mouse buttons.
        if event.button() not in [Qt.LeftButton, Qt.RightButton]:
            return

        coord = self._coord_from_event(event)

        ## Bothclick (one of the buttons still down)
        if event.buttons() & int(Qt.LeftButton | Qt.RightButton):
            logger.debug("Mouse button release on cell %s after both down", coord)
            self.first_of_both_buttons_release(coord)

            if self._state.drag_select and event.button() == Qt.LeftButton:
                # Only right button down - no risk.
                self.no_risk_signal.emit()

        elif not self._both_mouse_buttons_pressed:
            ## Leftclick
            if event.button() == Qt.LeftButton and not self._was_double_left_click:
                logger.debug("Left mouse button release on cell %s", coord)
                self.left_button_release(coord)

        # Reset variables if neither of the mouse buttons are down.
        if not (event.buttons() & int(Qt.LeftButton | Qt.RightButton)):
            logger.debug("No mouse buttons down, reset variables")
            self.all_buttons_release()

    # --------------------------------------------------------------------------
    # Mouse click handlers
    # --------------------------------------------------------------------------
    def left_button_down(self, coord: Coord_T) -> None:
        """
        Left mouse button was pressed (single click). Change display and call
        callback functions as appropriate.
        """
        self._track_mouse_event(ClickEvent.LEFT_DOWN, coord)
        if self._state.drag_select:
            self.at_risk_signal.emit()
            self._ctrlr.select_cell(coord)
        else:
            self._sink_unclicked_cell(coord)

    def left_button_double_down(self, coord: Coord_T) -> None:
        """
        Left button was double clicked. Call callback to remove any flags that
        were on the cell.
        """
        self._track_mouse_event(ClickEvent.DOUBLE_LEFT_DOWN, coord)
        if type(self._board[coord]) is CellContents.Flag:
            self._ctrlr.remove_cell_flags(coord)
        else:
            self._was_double_left_click = False
            self.left_button_down(coord)

    def left_button_move(self, coord: Coord_T) -> None:
        """
        Left mouse button was moved after a single click. Change display as
        appropriate.
        """
        self._track_mouse_event(ClickEvent.LEFT_MOVE, coord)
        self._raise_all_sunken_cells()
        self.no_risk_signal.emit()
        if coord is not None:
            self.left_button_down(coord)

    def left_button_double_move(self, coord: Coord_T) -> None:
        """
        Left mouse button moved after a double click.
        """
        self._track_mouse_event(ClickEvent.DOUBLE_LEFT_MOVE, coord)
        if self._state.drag_select:
            self._ctrlr.remove_cell_flags(coord)

    def left_button_release(self, coord: Coord_T) -> None:
        """
        Left mouse button was released. Change display and call callback
        functions as appropriate.
        """
        self._track_mouse_event(ClickEvent.LEFT_UP, coord)
        self._raise_all_sunken_cells()
        self.no_risk_signal.emit()
        if not self._state.drag_select and coord is not None:
            self._ctrlr.select_cell(coord)

    def right_button_down(self, coord: Coord_T) -> None:
        """
        Right mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        self._track_mouse_event(ClickEvent.RIGHT_DOWN, coord)
        self._ctrlr.flag_cell(coord)
        if self._board[coord] is CellContents.Unclicked:
            self._unflag_on_right_drag = True
        else:
            self._unflag_on_right_drag = False

    def right_button_move(self, coord: Coord_T) -> None:
        """
        Right mouse button was moved. Change display as appropriate.
        """
        self._track_mouse_event(ClickEvent.RIGHT_MOVE, coord)
        if self._state.drag_select and coord is not None:
            if self._unflag_on_right_drag:
                self._ctrlr.remove_cell_flags(coord)
            else:
                self._ctrlr.flag_cell(coord, flag_only=True)

    def both_buttons_down(self, coord: Coord_T) -> None:
        """
        Both left and right mouse buttons were pressed. Change display and call
        callback functions as appropriate.
        """
        self._track_mouse_event(ClickEvent.BOTH_DOWN, coord)
        if not self._board[coord].is_mine_type():
            for c in self._board.get_nbrs(coord, include_origin=True):
                self._sink_unclicked_cell(c)
        if self._state.drag_select:
            self.at_risk_signal.emit()
            self._ctrlr.chord_on_cell(coord)

    def both_buttons_move(self, coord: Coord_T) -> None:
        """
        Both left and right mouse buttons were moved. Change display as
        appropriate.
        """
        self._track_mouse_event(ClickEvent.BOTH_MOVE, coord)
        self._raise_all_sunken_cells()
        if not self._state.drag_select:
            self.no_risk_signal.emit()
        if coord is not None:
            self.both_buttons_down(coord)

    def first_of_both_buttons_release(self, coord: Coord_T) -> None:
        """
        One of the mouse buttons was released after both were pressed. Change
        display and call callback functions as appropriate.
        """
        self._track_mouse_event(ClickEvent.FIRST_OF_BOTH_UP, coord)
        self._raise_all_sunken_cells()
        if not self._state.drag_select:
            self.no_risk_signal.emit()
            if coord is not None:
                self._ctrlr.chord_on_cell(coord)

    def all_buttons_release(self) -> None:
        """
        The second of the mouse buttons was released after both were pressed.
        Change display and call callback functions as appropriate.
        """
        if self._state.drag_select:
            self.no_risk_signal.emit()
        self._mouse_coord = None
        self._both_mouse_buttons_pressed = False
        self._await_release_all_buttons = False
        self._was_double_left_click = False

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def _is_coord_in_grid(self, coord: Coord_T) -> bool:
        return self._board.is_coord_in_grid(coord)

    def _coord_from_event(self, event: QMouseEvent) -> Optional[Coord_T]:
        pos = self.mapToScene(event.pos())

        coord = int(pos.x()) // self.btn_size, int(pos.y()) // self.btn_size
        if not self._is_coord_in_grid(coord):
            return None
        return coord

    def _sink_unclicked_cell(self, coord: Coord_T) -> None:
        """
        Set an unclicked cell to appear sunken.
        """
        if self._state.game_status.finished():
            return
        if self._board[coord] is CellContents.Unclicked:
            self._set_cell_image(coord, _SUNKEN_CELL)
            self._sunken_cells.add(coord)
        if self._sunken_cells:
            self.at_risk_signal.emit()

    def _raise_all_sunken_cells(self) -> None:
        """
        Reset all sunken cells to appear raised.
        """
        while self._sunken_cells:
            coord = self._sunken_cells.pop()
            if self._board[coord] is CellContents.Unclicked:
                self._set_cell_image(coord, _RAISED_CELL)

    def _set_cell_image(self, coord: Coord_T, state: CellContents) -> None:
        """
        Set the image of a cell.

        Arguments:
        coord ((x, y) tuple in grid range)
            The coordinate of the cell.
        state
            The cell_images key for the image to be set.
        """
        if state not in self._cell_images:
            logger.error("Missing cell image for state: %s", state)
            return
        x, y = coord
        b = self._scene.addPixmap(self._cell_images[state])
        b.setPos(x * self.btn_size, y * self.btn_size)

    def _track_mouse_event(self, event: ClickEvent, coord: Coord_T):
        if self._enable_mouse_tracking:
            self._mouse_events.append(
                MouseEvent(time.time() - self._first_click_time, event, coord)
            )

    def _update_size(self) -> None:
        self.setMaximumSize(self.sizeHint())
        self.setSceneRect(
            0, 0, self.x_size * self.btn_size, self.y_size * self.btn_size
        )
        self.size_changed.emit()

    def reset(self) -> None:
        """Reset all cell images and other state for a new game."""
        logger.info("Resetting minefield widget")
        self._mouse_coord = None
        self._both_mouse_buttons_pressed = False
        self._await_release_all_buttons = True
        self._mouse_tracking = []
        self._mouse_events = []
        self._first_click_time = None
        for c in self._board.all_coords:
            self._set_cell_image(c, CellContents.Unclicked)

    def update_cells(self, cell_updates: Mapping[Coord_T, CellContents]) -> None:
        """
        Called to indicate some cells have changed state.

        :param cell_updates:
            A mapping of cell coordinates to their new state.
        """
        for c, state in cell_updates.items():
            self._set_cell_image(c, state)

    def reshape(self, x_size: int, y_size: int) -> None:
        logger.info("Resizing minefield to %sx%s", x_size, y_size)
        self._update_size()
        for c in [(i, j) for i in range(self.x_size) for j in range(self.y_size)]:
            self._set_cell_image(c, CellContents.Unclicked)

    def update_style(self, img_type: CellImageType, style: str) -> None:
        """Update the cell images."""
        logger.info("Updating %s style to '%s'", img_type.name, style)
        _update_cell_images(
            self._cell_images, self.btn_size, self._state.styles, img_type
        )
        for coord in self._board.all_coords:
            self._set_cell_image(coord, self._board[coord])

    def update_btn_size(self, size: int) -> None:
        """Update the size of the cells."""
        assert size == self._state.btn_size
        _update_cell_images(self._cell_images, self.btn_size, self._state.styles)
        for coord in self._board.all_coords:
            self._set_cell_image(coord, self._board[coord])
        self._update_size()

    def get_mouse_events(self) -> List[MouseEvent]:
        return self._mouse_events
