# October 2021, Lewis Gaul

__all__ = ("MinefieldWidgetImpl",)

import logging
from typing import Dict

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsScene

from ... import api
from ...core.regular import Coord
from ...shared.types import CellContents, CellImageType
from ..state import State
from . import _base
from ._base import update_cell_images


logger = logging.getLogger(__name__)


class MinefieldWidgetImpl(_base.MinefieldWidgetImplBase):
    """
    Minefield widget for regular game.
    """

    def __init__(
        self, scene: QGraphicsScene, ctrlr: api.AbstractController, state: State
    ):
        super().__init__(scene, ctrlr, state)
        self._cell_images: Dict[CellContents, QPixmap] = {}
        self.update_cell_images()

    def set_cell_image(self, coord: Coord, state: CellContents) -> None:
        """Set the image of a cell on the scene."""
        try:
            img = self._cell_images[state]
        except KeyError:
            logger.error("Missing cell image for state: %s", state)
            return
        b = self._scene.addPixmap(img)
        b.setPos(coord.x * self.btn_size, coord.y * self.btn_size)

    def update_cell_images(self, img_type: CellImageType = CellImageType.ALL) -> None:
        update_cell_images(
            self._cell_images, self.btn_size, self._state.styles, img_type
        )
