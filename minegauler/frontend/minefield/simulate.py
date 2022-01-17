# June 2020, Lewis Gaul

"""
Simulate played games.
"""

__all__ = ("MinefieldWidget",)

import logging
from typing import Dict, List, Mapping, Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMouseEvent, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from minegauler.shared.types import CellContents, CellImageType, Coord

from ..utils import CellUpdate_T
from ._base import update_cell_images


logger = logging.getLogger(__name__)


# TODO: Inherit from MinefieldWidgetBase
class MinefieldWidget(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        x_size: int,
        y_size: int,
        cell_updates: List[CellUpdate_T],
    ):
        super().__init__(parent)
        self._x_size = x_size
        self._y_size = y_size
        self._remaining_cell_updates = cell_updates

        self._cell_images: Dict[CellContents, QPixmap] = {}
        update_cell_images(
            self._cell_images, self.btn_size, {CellImageType.BUTTONS: "standard"}
        )

        self._scene = QGraphicsScene()
        self.setModal(True)
        self.setWindowTitle("Highscore replay")
        self._setup_ui()

        for c in [(x, y) for x in range(self.x_size) for y in range(self.y_size)]:
            self._set_cell_image(c, CellContents.Unclicked)

        self._animation_started = False

    @property
    def x_size(self) -> int:
        return self._x_size

    @property
    def y_size(self) -> int:
        return self._y_size

    @property
    def btn_size(self) -> int:
        return 20

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        frame = QFrame(self)
        frame.setFrameShadow(QFrame.Raised)
        frame.setFrameShape(QFrame.Box)
        frame.setLineWidth(5)
        frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        base_layout.addWidget(frame)
        sub_layout = QVBoxLayout(frame)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        view = QGraphicsView(frame)
        view.setScene(self._scene)
        sub_layout.addWidget(view)

    # --------------------------------------------------------------------------
    # Qt method overrides
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if not self._animation_started:
            self._animation_started = True
            self._do_next_update()

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def _do_next_update(self):
        """Perform the next set of cell updates."""
        evt = self._remaining_cell_updates.pop(0)
        self._update_cells({tuple(c): CellContents.from_str(x) for c, x in evt[1]})
        if self._remaining_cell_updates:
            QTimer.singleShot(
                1000 * (self._remaining_cell_updates[0][0] - evt[0]),
                self._do_next_update,
            )

    def _set_cell_image(self, coord: Coord, state: CellContents) -> None:
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

    def _update_cells(self, cell_updates: Mapping[Coord, CellContents]) -> None:
        """
        Called to indicate some cells have changed state.

        :param cell_updates:
            A mapping of cell coordinates to their new state.
        """
        for c, state in cell_updates.items():
            self._set_cell_image(c, state)
