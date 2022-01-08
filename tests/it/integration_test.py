# January 2022, Lewis Gaul (typed by Jess Toudic)

"""
Integration tests. Simulates interactions by calling frontend APIs only.

"""

import contextlib
import functools
import json
import logging
import os
import time
import types
from importlib.util import find_spec
from typing import Optional
from unittest import mock

import pytest
from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

import minegauler
from minegauler import frontend
from minegauler.frontend import QApplication
from minegauler.shared.utils import AllOptsStruct


logger = logging.getLogger(__name__)


def _run_minegauler__main__() -> types.ModuleType:
    """
    Run minegauler via the __main__ module.

    :return:
        The __main__ module namespace.
    """
    module = types.ModuleType("minegauler.__main__")
    spec = find_spec("minegauler.__main__")
    spec.loader.exec_module(module)
    return module


def create_gui(settings: Optional[AllOptsStruct] = None) -> frontend.MinegaulerGUI:
    """@@@ TODO"""
    if settings is None:
        settings = AllOptsStruct()

    def run_app(gui: frontend.MinegaulerGUI) -> int:
        logger.info("In run_app()")
        gui.show()
        return 0

    logger.info("Executing __main__ without starting app event loop")
    with contextlib.ExitStack() as ctxs:
        ctxs.enter_context(mock.patch("minegauler.frontend.run_app", run_app))
        ctxs.enter_context(mock.patch("sys.exit"))
        # TODO Should only mock reading from the settings file.
        ctxs.enter_context(
            mock.patch(
                "builtins.open",
                mock.mock_open(read_data=json.dumps(settings.encode_to_json())),
            )
        )
        main_module = _run_minegauler__main__()

    return main_module.gui


class Test:
    """
    @@@ TODO
    """

    # --------------------------------------------------------------------------
    # Testcases
    # --------------------------------------------------------------------------
    def test_create(self):
        gui = create_gui()
        self._process_events()

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
            btn_size = self.btn_size
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

    def assert_cell_sank(self, coord):
        self._mf_widget._set_cell_image.assert_any_call(coord, _SUNKEN_CELL)

    def assert_cell_rose(self, coord):
        self._mf_widget._set_cell_image.assert_any_call(coord, _RAISED_CELL)

    def assert_num_cells_changed(self, num):
        """
        Assert on the number of cells that had their image changed.
        """
        assert self._mf_widget._set_cell_image.call_count == num

    def assert_cells_unchanged(self):
        self._mf_widget._set_cell_image.assert_not_called()

    def reset_mocks(self):
        self._mf_widget._set_cell_image.reset_mock()
        self._mf_widget._ctrlr.reset_mock()
        self.at_risk_signal_cb.reset_mock()
        self.no_risk_signal_cb.reset_mock()

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

    @staticmethod
    def _process_events() -> None:
        """
        Manually process Qt events (normally taken care of by the event loop).

        The environment variable TEST_IT_EVENT_WAIT can be used to set the
        amount of time to spend processing events (in seconds).
        """
        start_time = time.time()
        if os.environ.get("TEST_IT_EVENT_WAIT"):
            wait = float(os.environ["TEST_IT_EVENT_WAIT"])
        else:
            wait = 0
        QApplication.processEvents()
        while time.time() < start_time + wait:
            QApplication.processEvents()
