# January 2022, Lewis Gaul (typed by Jess Toudic)

"""
Integration tests. Simulates interactions by calling frontend APIs only.

"""

import contextlib
import logging
from typing import Optional
from unittest import mock

import pytest
from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtGui import QMouseEvent

import minegauler.paths
from minegauler import core, frontend  # TODO: Fix circular dependency
from minegauler.shared.types import CellImageType
from minegauler.shared.utils import AllOptsStruct, write_settings_to_file

from . import process_events, run_main_entrypoint


logger = logging.getLogger(__name__)


def create_gui(settings: Optional[AllOptsStruct] = None) -> frontend.MinegaulerGUI:
    """Create a minegauler GUI instance via the main entrypoint."""
    if settings is not None:
        write_settings_to_file(settings, minegauler.paths.SETTINGS_FILE)

    def run_app(gui: frontend.MinegaulerGUI) -> int:
        logger.info("In run_app()")
        gui.show()
        return 0

    logger.info("Executing __main__ without starting app event loop")
    with contextlib.ExitStack() as ctxs:
        ctxs.enter_context(mock.patch("minegauler.frontend.run_app", run_app))
        ctxs.enter_context(mock.patch("sys.exit"))
        main_module = run_main_entrypoint()

    return main_module.gui


class Test:
    """
    Main class of integration tests.

    Uses a shared GUI which is factory reset after each testcase.
    """

    gui: frontend.MinegaulerGUI

    # Stored for convenience in helper functions.
    _qtbot = None
    _mf_widget = None
    _mouse_buttons_down = Qt.NoButton
    _mouse_down_pos = None

    @pytest.fixture(scope="class", autouse=True)
    def class_setup(self):
        cls = type(self)
        cls.gui = create_gui()
        cls._mf_widget = cls.gui._mf_widget

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, qtbot):
        self._qtbot = qtbot
        self._mouse_buttons_down = Qt.NoButton
        self._mouse_down_pos = None

        yield

        self._mouse_down_pos = None
        self._mouse_buttons_down = Qt.NoButton
        self._qtbot = None
        self.gui.factory_reset()

    # --------------------------------------------------------------------------
    # Testcases
    # --------------------------------------------------------------------------
    def test_create(self):
        process_events()

    def test_change_theme(self):
        process_events()
        self.right_press((0, 0))
        self.right_release()
        self.left_press((2, 2))
        self.left_release()
        process_events()
        self.gui._change_styles(
            {
                CellImageType.BUTTONS: "Dark",
                CellImageType.MARKERS: "Halloween",
                CellImageType.NUMBERS: "Dark",
            },
        )
        process_events()

    # --------------------------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------------------------
    def point_from_coord(self, coord, *, pos=None, btn_size=None) -> QPoint:
        """
        Arguments:
        coord ((int, int))
            The coordinate to get the point for.
        pos=None ((int, int) | None)
            The position on the cell, defaults to the centre.
        btn_size=None (int | None)
            The button size in use. Defaults to the value stored on the class.

        Return: (QPoint)
            The QPoint corresponding to the passed-in coordinate.
        """
        if not btn_size:
            btn_size = self._mf_widget.btn_size
        if not pos:
            pos = (btn_size // 2, btn_size // 2)

        return QPoint(coord[0] * btn_size + pos[0], coord[1] * btn_size + pos[1])

    def left_press(self, coord=None, **kwargs):
        """
        Simulate a left mouse button press.

        Arguments:
        coord=None ((int, int) | None)
            The coordinate to click on, if the mouse is not already down.
        **kwargs
            Passed on to self._mouse_press().
        """
        self._mouse_press(Qt.LeftButton, coord, **kwargs)

    def left_release(self):
        """
        Simulate a left mouse button release.
        """
        self._mouse_release(Qt.LeftButton)

    def right_press(self, coord=None, **kwargs):
        """
        Simulate a right mouse button press.

        Arguments:
        coord=None ((int, int) | None)
            The coordinate to click on, if the mouse is not already down.
        **kwargs
            Passed on to self._mouse_press().
        """
        self._mouse_press(Qt.RightButton, coord, **kwargs)

    def right_release(self):
        """
        Simulate a right mouse button release.
        """
        self._mouse_release(Qt.RightButton)

    def mouse_move(self, coord, **kwargs):
        """
        Arguments:
        coord ((int, int))
            The coordinate to press down on.
        **kwargs
            Passed on to self.point_from_coord().
        """

        # The following line doesn't work, see QTBUG-5232.
        # self._qtbot.mouseMove(self._mf_widget.viewport(),
        #                       pos=self.point_from_coord(coord))

        pos = self.point_from_coord(coord, **kwargs)
        event = QMouseEvent(
            QEvent.MouseMove, pos, Qt.NoButton, self._mouse_buttons_down, Qt.NoModifier
        )
        self._mf_widget.mouseMoveEvent(event)
        self._mouse_down_pos = pos

    def _mouse_press(self, button, coord=None, **kwargs):
        """
        Arguments:
        button (Qt.*Button)
            The mouse button to simulate a press for.
        coord=None ((int, int) | None)
            The coordinate to press down on, if the mouse is not already down.
        **kwargs
            Passed on to self.point_from_coord() if coord is given.
        """
        if self._mouse_buttons_down & button:
            raise RuntimeError("Mouse button already down, can't press again")
        if self._mouse_down_pos:
            if coord is not None:
                raise ValueError("Coord should not be given, mouse already down")
            pos = self._mouse_down_pos
        else:
            if coord is None:
                raise ValueError("Coord required, mouse is not down")
            pos = self.point_from_coord(coord, **kwargs)
        self._qtbot.mousePress(self._mf_widget.viewport(), button, pos=pos)
        self._mouse_buttons_down |= button
        self._mouse_down_pos = pos

    def _mouse_release(self, button):
        """
        Arguments:
        button (Qt.*Button)
            The mouse button to simulate a press for.
        """
        if not (self._mouse_buttons_down & button):
            raise RuntimeError("Mouse button isn't down, can't release")
        self._qtbot.mouseRelease(
            self._mf_widget.viewport(), button, pos=self._mouse_down_pos
        )
        self._mouse_buttons_down &= ~button
        if self._mouse_buttons_down == Qt.NoButton:
            self._mouse_down_pos = None
