"""
main_window_test.py - Test the main window of the GUI

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k main_window_test]' from
the root directory.
"""

from unittest import mock

import pytest
from pytestqt.qtbot import QtBot

from minegauler.core import api
from minegauler.frontend import main_window, minefield, panel, state
from minegauler.frontend.main_window import MinegaulerGUI

from ..utils import active_patches, make_true_mock
from . import utils


_MockPanelWidget = make_true_mock(panel.PanelWidget)
_MockMinefieldWidget = make_true_mock(minefield.MinefieldWidget)
_MockNameEntryBar = make_true_mock(main_window._NameEntryBar)


class TestMinegaulerGUI:
    """
    Tests for the main GUI window.
    """

    initial_state = state.State()

    _panel_class_mock = None
    _minefield_class_mock = None
    _name_bar_class_mock = None

    @classmethod
    def setup_class(cls):
        cls._panel_class_mock = mock.patch(
            "minegauler.frontend.panel.PanelWidget", side_effect=_MockPanelWidget
        ).start()
        cls._minefield_class_mock = mock.patch(
            "minegauler.frontend.minefield.MinefieldWidget",
            side_effect=_MockMinefieldWidget,
        ).start()
        cls._name_bar_class_mock = mock.patch(
            "minegauler.frontend.main_window._NameEntryBar",
            side_effect=_MockNameEntryBar,
        ).start()
        mock.patch("minegauler.frontend.minefield.init_or_update_cell_images").start()

    @classmethod
    def teardown_class(cls):
        mock.patch.stopall()

    @pytest.fixture
    def gui(self, qtbot: QtBot, ctrlr: api.AbstractController) -> MinegaulerGUI:
        gui = MinegaulerGUI(ctrlr, self.initial_state)
        qtbot.addWidget(gui)
        gui._panel_widget.reset_mock()
        gui._mf_widget.reset_mock()
        gui._name_entry_widget.reset_mock()
        return gui

    # --------------------------------------------------------------------------
    # Testcases
    # --------------------------------------------------------------------------
    def test_create(self, qtbot: QtBot, ctrlr: api.AbstractSwitchingController):
        """Test basic creation of the window."""
        gui = MinegaulerGUI(ctrlr, self.initial_state)
        qtbot.addWidget(gui)
        assert gui.windowTitle() == "Minegauler"
        assert not gui.windowIcon().isNull()
        # Check the menubar.
        exp_menus = ["Game", "Options", "Help"]
        assert [a.text() for a in gui.menuBar().actions()] == exp_menus
        # Check the main child widgets.
        assert type(gui._panel_widget) is _MockPanelWidget
        self._panel_class_mock.assert_called_once()
        assert type(gui._mf_widget) is _MockMinefieldWidget
        self._minefield_class_mock.assert_called_once()
        assert type(gui._name_entry_widget) is _MockNameEntryBar
        self._name_bar_class_mock.assert_called_once()
        gui.show()
        utils.maybe_stop_for_interaction(qtbot)

    def test_listener_methods(self, qtbot: QtBot, gui: MinegaulerGUI):
        """Test the AbstractListener methods."""
        # reset()
        gui.reset()
        gui._panel_widget.reset.assert_called_once()
        gui._mf_widget.reset.assert_called_once()
