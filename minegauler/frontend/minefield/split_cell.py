# January 2022, Lewis Gaul

__all__ = ("MinefieldWidgetImpl",)

import logging
from typing import Dict

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsScene

from ... import api
from ...core.split_cell import Coord
from ...shared.types import CellContents, CellImageType
from ..state import State
from . import _base
from ._base import FlagAction, update_cell_images


logger = logging.getLogger(__name__)


class MinefieldWidgetImpl(_base.MinefieldWidgetImplBase):
    """
    Minefield widget for regular game.
    """

    def __init__(
        self, scene: QGraphicsScene, ctrlr: api.AbstractController, state: State
    ):
        super().__init__(scene, ctrlr, state)
        self._small_cell_images: Dict[CellContents, QPixmap] = {}
        self._large_cell_images: Dict[CellContents, QPixmap] = {}
        self.update_cell_images()

    def set_cell_image(self, coord: Coord, state: CellContents) -> None:
        """Set the image of a cell on the scene."""
        try:
            if coord.is_split:
                img = self._small_cell_images[state]
            else:
                img = self._large_cell_images[state]
        except KeyError:
            logger.error("Missing cell image for state: %s", state)
            return
        b = self._scene.addPixmap(img)
        b.setPos(coord.x * self.btn_size, coord.y * self.btn_size)

    def update_cell_images(self, img_type: CellImageType = CellImageType.ALL) -> None:
        update_cell_images(
            self._small_cell_images, self.btn_size, self._state.styles, img_type
        )
        update_cell_images(
            self._large_cell_images, self.btn_size * 2, self._state.styles, img_type
        )

    def right_down_action(self, coord: Coord) -> FlagAction:
        """Perform a right click, returning the action that was taken."""
        if coord.is_split or self._ctrlr.board[coord] is not CellContents.Unclicked:
            self._ctrlr.flag_cell(coord)
            if self._ctrlr.board[coord] is CellContents.Unclicked:
                return FlagAction.UNFLAG
            else:
                return FlagAction.FLAG
        else:
            self._ctrlr.split_cell(coord)
            return FlagAction.SPLIT

    def right_drag_action(self, coord: Coord, action: FlagAction) -> None:
        """Perform a right drag click that matches the given action."""
        if action is FlagAction.FLAG:
            self._ctrlr.flag_cell(coord, flag_only=True)
        elif action is FlagAction.UNFLAG:
            self._ctrlr.remove_cell_flags(coord)
        elif action is FlagAction.SPLIT:
            self._ctrlr.split_cell(coord)
        else:
            assert False, f"Unexpected action {action!r}"
