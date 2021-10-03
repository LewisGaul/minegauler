# October 2021, Lewis Gaul

__all__ = ("MinefieldWidget",)

import enum
from typing import Any, Dict, Mapping, Optional

from PyQt5.QtGui import QPixmap

import minegauler.core.split_cell as backend
from minegauler.shared.types import CellContents, CellImageType

from .base import MinefieldWidgetBase


RightClickAction = enum.Enum("RightClickAction", ["FLAG", "UNFLAG", "SPLIT"])


class MinefieldWidget(MinefieldWidgetBase):
    def __init__(self, *args, **kwargs):
        self._large_cell_images: Dict[CellContents, QPixmap] = {}
        super().__init__(*args, **kwargs)

        self._right_click_action: Optional[RightClickAction] = None
        del self._unflag_on_right_drag

    @property
    def _board(self) -> backend.Board:
        return self._ctrlr.board

    # --------------------------------------------------------------------------
    # Mouse click handlers
    # --------------------------------------------------------------------------
    def right_button_down(self, coord: backend.Coord) -> None:
        """
        Right mouse button was pressed. Change display and call callback
        functions as appropriate.
        """
        if coord.is_split:
            self._ctrlr.flag_cell(coord)
            if self._board[coord] is CellContents.Unclicked:
                self._right_click_action = RightClickAction.UNFLAG
            else:
                self._right_click_action = RightClickAction.FLAG
        else:
            self._ctrlr.split_cell(coord)
            if self._board.get_coord_at(coord.x, coord.y).is_split:
                self._right_click_action = RightClickAction.SPLIT

    def right_button_move(self, coord: Optional[backend.Coord]) -> None:
        """
        Right mouse button was moved. Change display as appropriate.
        """
        if self._state.drag_select and coord is not None:
            if self._right_click_action is RightClickAction.SPLIT:
                self._ctrlr.split_cell(coord)
            elif self._right_click_action is RightClickAction.UNFLAG:
                self._ctrlr.remove_cell_flags(coord)
            elif self._right_click_action is RightClickAction.FLAG:
                self._ctrlr.flag_cell(coord, flag_only=True)
            else:
                # The right-button down had no effect, so treat the move like
                # a first click.
                self.right_button_down(coord)

    # --------------------------------------------------------------------------
    # Other public methods
    # --------------------------------------------------------------------------
    def reset(self) -> None:
        super().reset()
        self._right_click_action = None

    def update_cells(self, cell_updates: Mapping[backend.Coord, Any]) -> None:
        """
        Called to indicate some cells have changed state.

        :param cell_updates:
            A mapping of cell coordinates to their new state.
        """
        for c, v in cell_updates.items():
            if c.is_split:
                self._set_cell_image(c, v)
            else:
                self._set_large_cell_image(c, v)

    def all_buttons_release(self) -> None:
        super().all_buttons_release()
        self._right_click_action = None

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def _set_large_cell_image(self, coord: backend.Coord, state: CellContents) -> None:
        if state not in self._large_cell_images:
            logger.error("Missing cell image for state: %s", state)
            return
        b = self._scene.addPixmap(self._large_cell_images[state])
        b.setPos(coord.x * self.btn_size, coord.y * self.btn_size)

    def _redraw_cells(self):
        self._scene.clear()
        for coord in self._board.all_coords:
            if coord.is_split:
                self._set_cell_image(coord, self._board[coord])
            else:
                self._set_large_cell_image(coord, self._board[coord])

    def _update_cell_images(self, img_type: CellImageType = CellImageType.ALL) -> None:
        _update_cell_images(
            self._cell_images, self.btn_size, self._state.styles, img_type
        )
        _update_cell_images(
            self._large_cell_images, self.btn_size * 2, self._state.styles, img_type
        )
