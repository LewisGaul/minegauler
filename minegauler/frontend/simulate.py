from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QWidget

from ..core import api
from ..shared import GameOptsStruct, GUIOptsStruct
from ..shared.types import Coord_T
from .minefield import MinefieldWidget
from .state import State
from .utils import ClickEvent


class SimulationMinefieldWidget(MinefieldWidget):
    def __init__(
        self, parent: Optional[QWidget], ctrlr: api.AbstractController, state: State
    ):
        super().__init__(parent, ctrlr, state)
        self._enable_mouse_tracking = False

        self._remaining_click_events = []

    # --------------------------------------------------------------------------
    # Qt method overrides
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        self.replay_click_events(click_events)  # @@@

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double clicks."""

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def _do_click_event(self, event: ClickEvent, coord: Coord_T) -> None:
        if event is ClickEvent.LEFT_DOWN:
            self.left_button_down(coord)
        elif event is ClickEvent.LEFT_MOVE:
            self.left_button_move(coord)
        elif event is ClickEvent.LEFT_UP:
            self.left_button_release(coord)
        elif event is ClickEvent.RIGHT_DOWN:
            self.right_button_down(coord)
        elif event is ClickEvent.RIGHT_MOVE:
            self.right_button_move(coord)
        elif event is ClickEvent.BOTH_DOWN:
            self.both_buttons_down(coord)
        elif event is ClickEvent.BOTH_MOVE:
            self.both_buttons_move(coord)
        elif event is ClickEvent.FIRST_OF_BOTH_UP:
            self.first_of_both_buttons_release(coord)
        elif event is ClickEvent.DOUBLE_LEFT_DOWN:
            self.left_double_down(coord)
        elif event is ClickEvent.DOUBLE_LEFT_MOVE:
            self.left_double_move(coord)

    def _timer_cb(self):
        evt = self._remaining_click_events.pop(0)
        self._do_click_event(evt[1], evt[2])
        if self._remaining_click_events:
            QTimer.singleShot(
                1000 * (self._remaining_click_events[0][0] - evt[0]), self._timer_cb
            )

    def replay_click_events(self, click_events):
        self._remaining_click_events = click_events.copy()
        self._timer_cb()


if __name__ == "__main__":
    import logging
    from unittest import mock

    from ..core import BaseController, Minefield
    from . import init_app, run_app

    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s[%(levelname)s](%(name)s) %(message)s",
    )

    init_app()

    click_events = [
        (0, ClickEvent.LEFT_DOWN, (1, 2)),
        (0.5, ClickEvent.LEFT_UP, (1, 2)),
        (2, ClickEvent.LEFT_DOWN, (6, 2)),
        (2.5, ClickEvent.BOTH_DOWN, (6, 2)),
        (3.5, ClickEvent.FIRST_OF_BOTH_UP, (6, 2)),
        (3.5, ClickEvent.LEFT_DOWN, (6, 2)),
        (4.2, ClickEvent.LEFT_MOVE, (6, 3)),
        (4.2, ClickEvent.LEFT_MOVE, (7, 3)),
        (4.4, ClickEvent.LEFT_MOVE, (7, 4)),
        (4.6, ClickEvent.LEFT_MOVE, (7, 3)),
        (4.8, ClickEvent.LEFT_MOVE, (7, 4)),
        (5, ClickEvent.LEFT_MOVE, (7, 5)),
        (6, ClickEvent.LEFT_UP, (7, 5)),
    ]

    ctrlr = BaseController(GameOptsStruct())
    ctrlr._active_ctrlr._game.mf = Minefield.from_2d_array(
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
        ]
    )
    mf = SimulationMinefieldWidget(
        None, ctrlr, State.from_opts(GameOptsStruct(), GUIOptsStruct())
    )
    mf._remaining_click_events = click_events.copy()

    def update_cells(cell_updates):
        for c, state in cell_updates.items():
            mf._set_cell_image(c, state)

    listener = mock.Mock()
    listener.update_cells = update_cells
    ctrlr.register_listener(listener)

    run_app(mf)
