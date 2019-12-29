"""
main_window_test.py - Test the main window of the GUI

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k main_window_test]' from
the root directory.
"""

from unittest import mock

from pytestqt.qtbot import QtBot

from minegauler.core import api
from minegauler.frontend import main_window, minefield, panel, state
from minegauler.frontend.main_window import MinegaulerGUI

from . import utils


class TestMinegaulerGUI:
    """
    Tests for the main GUI window.

    These tests treat the panel widget, minefield widget and name entry bar
    widget as trusted because there doesn't seem to be an easy way to mock out
    PyQt widgets with unittest.mock (?).
    """

    initial_state = state.State()

    def test_create(self, qtbot: QtBot, ctrlr: api.AbstractSwitchingController):
        """Test basic creation of the window."""
        gui = MinegaulerGUI(ctrlr, self.initial_state)
        assert gui.windowTitle() == "Minegauler"
        assert not gui.windowIcon().isNull()
        exp_menus = ["Game", "Options", "Help"]
        assert [a.text() for a in gui.menuBar().actions()] == exp_menus
        assert type(gui._panel_widget) == panel.PanelWidget
        assert type(gui._mf_widget) == minefield.MinefieldWidget
        assert type(gui._name_entry_widget) == main_window._NameEntryBar
        qtbot.addWidget(gui)
        gui.show()
        utils.maybe_stop_for_interaction(qtbot)
