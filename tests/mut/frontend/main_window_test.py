"""
main_window_test.py - Test the main window of the GUI

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k main_window_test]' from
the root directory.
"""

from pytestqt.qtbot import QtBot

from minegauler.core import api
from minegauler.frontend import main_window, minefield, panel, state
from minegauler.frontend.main_window import MinegaulerGUI

from . import utils


class TestMinegaulerGUI:
    """Tests for the main GUI window."""

    def test_create(self, qtbot: QtBot, ctrlr: api.AbstractSwitchingController):
        """Test basic creation of the window."""
        initial_state = state.State()
        gui = MinegaulerGUI(ctrlr, initial_state)
        assert type(gui._panel_widget) == panel.PanelWidget
        assert type(gui._mf_widget) == minefield.MinefieldWidget
        assert type(gui._name_entry_widget) == main_window._NameEntryBar
        qtbot.addWidget(gui)
        gui.show()
        utils.maybe_stop_for_interaction(qtbot)
