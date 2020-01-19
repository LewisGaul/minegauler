"""
minefield.py - Minefield widgets

April 2018, Lewis Gaul

Exports:
MinefieldWidget
    A minefield widget class, to be packed in a parent container. Receives
    clicks on the cells and makes calls to the backend.
"""

__all__ = ("MinefieldWidget",)

import logging
import sys
from typing import Dict, Optional, Set

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QMouseEvent, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QSizePolicy,
    QWidget,
)

from ..core import api
from ..types import (
    CellFlag,
    CellHitMine,
    CellImageType,
    CellMine,
    CellMineType,
    CellNum,
    CellUnclicked,
    CellWrongFlag,
)
from ..typing import Coord_T
from . import state
from .utils import IMG_DIR


logger = logging.getLogger(__name__)


# @@@LG :'(         ... please don't look at the contents of these two functions.
def init_or_update_cell_images(cell_images, size, styles, required=CellImageType.ALL):
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
    # @@@LG Currently only allows setting button styles.
    btn_style = styles[CellImageType.BUTTONS]
    if required & CellImageType.BUTTONS:
        cell_images["btn_up"] = make_pixmap("buttons", btn_style, "btn_up.png", size)
        cell_images["btn_down"] = make_pixmap(
            "buttons", btn_style, "btn_down.png", size
        )
        cell_images[CellUnclicked()] = cell_images["btn_up"]
        cell_images[CellNum(0)] = cell_images["btn_down"]

    if required & (CellImageType.BUTTONS | CellImageType.NUMBERS):
        for i in range(1, 19):
            cell_images[CellNum(i)] = make_pixmap(
                "numbers", btn_style, "btn_down.png", size, "num%d.png" % i, 7 / 8
            )

    if required & (CellImageType.BUTTONS | CellImageType.MARKERS):
        for i in range(1, 4):
            cell_images[CellFlag(i)] = make_pixmap(
                "markers", btn_style, "btn_up.png", size, "flag%d.png" % i, 5 / 8
            )
            cell_images[CellWrongFlag(i)] = make_pixmap(
                "markers", btn_style, "btn_up.png", size, "cross%d.png" % i, 5 / 8
            )
            cell_images[CellMine(i)] = make_pixmap(
                "markers", btn_style, "btn_down.png", size, "mine%d.png" % i, 7 / 8
            )
            cell_images[CellHitMine(i)] = make_pixmap(
                "markers", btn_style, "btn_down_hit.png", size, "mine%d.png" % i, 7 / 8
            )


def make_pixmap(img_subdir, style, bg_fname, size, fg_fname=None, propn=1):
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
        fg_size = propn * size
        fg_path = get_path(img_subdir, fg_fname, "Standard")
        overlay = QPixmap(fg_path).scaled(
            fg_size, fg_size, transformMode=Qt.SmoothTransformation
        )
        painter = QPainter(image)
        margin = size * (1 - propn) / 2
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
        self,
        parent: Optional[QWidget],
        ctrlr: api.AbstractController,
        state_: state.State,
    ):
        super().__init__(parent)
        logger.info("Initialising minefield widget")
        self._ctrlr: api.AbstractController = ctrlr
        self._state: state.State = state_
        self._cell_images: Dict = {}
        init_or_update_cell_images(self._cell_images, self.btn_size, self._state.styles)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setStyleSheet("border: 0px")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setMaximumSize(self.sizeHint())

        # Keep track of mouse button states.
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.await_release_all_buttons = False
        self.was_double_left_click = False
        self.unflag_on_right_drag = False
        # Set of coords for cells which are sunken.
        self.sunken_cells: Set = set()

        self._ignore_clicks = False
        self.reset()

    @property
    def _board(self):
        # TODO: I don't like this.
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
            self.await_release_all_buttons = False
            self.both_mouse_buttons_pressed = False
        elif self.await_release_all_buttons:
            return
        if self._ignore_clicks or self.was_double_left_click:
            return

        self.mouse_coord = coord = self._coord_from_event(event)

        ## Bothclick
        if event.buttons() & Qt.LeftButton and event.buttons() & Qt.RightButton:
            logger.debug("Both mouse buttons down on cell %s", coord)
            self.both_mouse_buttons_pressed = True
            self.both_buttons_down(coord)
        ## Leftclick
        elif event.button() == Qt.LeftButton:
            logger.debug("Left mouse button down on cell %s", coord)
            self.was_double_left_click = False
            self.left_button_down(coord)
        ## Rightclick
        elif event.button() == Qt.RightButton:
            logger.debug("Right mouse button down on cell %s", coord)
            self.right_button_down(coord)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double clicks."""

        coord = self._coord_from_event(event)

        # Redirect double right-clicks to be two normal clicks.
        if event.button() == Qt.RightButton:
            return self.mousePressEvent(event)
        elif event.button() == Qt.LeftButton and not self.both_mouse_buttons_pressed:
            self.was_double_left_click = True
            self.left_button_double_down(coord)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""

        if self._ignore_clicks:
            return

        coord = self._coord_from_event(event)

        # Return if not the left or right mouse buttons, or if the mouse wasn't
        #  moved to a different cell.
        if (
            not event.buttons() & (Qt.LeftButton | Qt.RightButton)
            or self.await_release_all_buttons
            or coord == self.mouse_coord
        ):
            return

        self.mouse_coord = coord

        ## Double leftclick
        if self.was_double_left_click:
            if event.buttons() == Qt.LeftButton:
                self.left_button_double_move(coord)
            return

        ## Bothclick
        if event.buttons() & Qt.LeftButton and event.buttons() & Qt.RightButton:
            self.both_buttons_move(coord)
        elif not self.both_mouse_buttons_pressed or self._state.drag_select:
            ## Leftclick
            if event.buttons() & Qt.LeftButton:
                self.left_button_move(coord)
            ## Rightclick
            if event.buttons() & Qt.RightButton:
                self.right_button_move(coord)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""

        if self.await_release_all_buttons and not event.buttons():
            self.await_release_all_buttons = False
            return
        # Ignore any clicks which aren't the left or right mouse buttons.
        if event.button() not in [Qt.LeftButton, Qt.RightButton] or self._ignore_clicks:
            return

        coord = self._coord_from_event(event)

        ## Bothclick (one of the buttons still down)
        if event.buttons() & (Qt.LeftButton | Qt.RightButton):
            logger.debug("Mouse button release on cell %s after both down", coord)
            self.first_of_both_buttons_release(coord)

            if self._state.drag_select and event.button() == Qt.LeftButton:
                # Only right button down - no risk.
                self.no_risk_signal.emit()

        elif not self.both_mouse_buttons_pressed:
            ## Leftclick
            if event.button() == Qt.LeftButton and not self.was_double_left_click:
                logger.debug("Left mouse button release on cell %s", coord)
                self.left_button_release(coord)

        # Reset variables if neither of the mouse buttons are down.
        if not (event.buttons() & (Qt.LeftButton | Qt.RightButton)):
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
        self._ctrlr.remove_cell_flags(coord)

    def left_button_move(self, coord: Coord_T) -> None:
        """
        Left mouse button was moved after a single click. Change display as
        appropriate.
        """
        self._raise_all_sunken_cells()
        self.no_risk_signal.emit()
        if coord is not None:
            self.left_button_down(coord)

    def left_button_double_move(self, coord: Coord_T) -> None:
        """
        Left mouse button moved after a double click.
        """
        if self._state.drag_select:
            self.left_button_double_down(coord)

    def left_button_release(self, coord: Coord_T) -> None:
        """
        Left mouse button was released. Change display and call callback
        functions as appropriate.
        """
        self._raise_all_sunken_cells()
        self.no_risk_signal.emit()
        if not self._state.drag_select and coord is not None:
            self._ctrlr.select_cell(coord)

    def right_button_down(self, coord: Coord_T) -> None:
        """
        Right mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        self._ctrlr.flag_cell(coord)
        if self._board[coord] == CellUnclicked():
            self.unflag_on_right_drag = True
        else:
            self.unflag_on_right_drag = False

    def right_button_move(self, coord: Coord_T) -> None:
        """
        Right mouse button was moved. Change display as appropriate.
        """
        if coord is not None and self._state.drag_select:
            if self.unflag_on_right_drag:
                self._ctrlr.remove_cell_flags(coord)
            else:
                self._ctrlr.flag_cell(coord, flag_only=True)

    def both_buttons_down(self, coord: Coord_T) -> None:
        """
        Both left and right mouse buttons were pressed. Change display and call
        callback functions as appropriate.
        """
        if not isinstance(self._board[coord], CellMineType):
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
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.await_release_all_buttons = False
        self.was_double_left_click = False

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
        if self._board[coord] == CellUnclicked():
            self.set_cell_image(coord, "btn_down")
            self.sunken_cells.add(coord)
        if self.sunken_cells:
            self.at_risk_signal.emit()

    def _raise_all_sunken_cells(self) -> None:
        """
        Reset all sunken cells to appear raised.
        """
        while self.sunken_cells:
            coord = self.sunken_cells.pop()
            if self._board[coord] == CellUnclicked():
                self.set_cell_image(coord, "btn_up")

    def reset(self) -> None:
        """Reset all cell images and other state for a new game."""
        logger.info("Resetting minefield widget")
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.await_release_all_buttons = True
        for c in self._board.all_coords:
            self.set_cell_image(c, CellUnclicked())

    def set_cell_image(self, coord: Coord_T, state) -> None:
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
        b = self.scene.addPixmap(self._cell_images[state])
        b.setPos(x * self.btn_size, y * self.btn_size)

    def ignore_clicks(self) -> None:
        self._ignore_clicks = True

    def accept_clicks(self) -> None:
        self._ignore_clicks = False

    def reshape(self, x_size: int, y_size: int) -> None:
        logger.info("Resizing minefield to %sx%s", x_size, y_size)
        self._update_size()
        for c in [(i, j) for i in range(self.x_size) for j in range(self.y_size)]:
            self.set_cell_image(c, CellUnclicked())

    def update_style(self, img_type: CellImageType, style: str) -> None:
        """Update the cell images."""
        logger.info("Updating %s style to '%s'", img_type.name, style)
        init_or_update_cell_images(
            self._cell_images, self.btn_size, self._state.styles, img_type
        )
        for coord in self._board.all_coords:
            self.set_cell_image(coord, self._board[coord])

    def update_btn_size(self, size: int) -> None:
        """Update the size of the cells."""
        assert size == self._state.btn_size
        init_or_update_cell_images(self._cell_images, self.btn_size, self._state.styles)
        for coord in self._board.all_coords:
            self.set_cell_image(coord, self._board[coord])
        self._update_size()

    def _update_size(self) -> None:
        self.setMaximumSize(self.sizeHint())
        self.setSceneRect(
            0, 0, self.x_size * self.btn_size, self.y_size * self.btn_size
        )
        self.size_changed.emit()


if __name__ == "__main__":
    from minegauler.core import GameController
    from minegauler.shared.utils import GameOptsStruct

    _app = QApplication(sys.argv)
    x, y = 6, 4
    ctrlr = GameController(GameOptsStruct(x_size=x, y_size=y))
    state_ = state.State()
    state_.x_size = x
    state_.y_size = y
    state_.btn_size = 100
    mf_widget = MinefieldWidget(None, ctrlr, state_=state_)
    mf_widget.show()
    sys.exit(_app.exec_())
