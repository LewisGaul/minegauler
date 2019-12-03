"""
main_window_test.py - Test the main window of the GUI

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k main_window_test]' from
the root directory.
"""

import pytest

from minegauler.core.utils import GameOptsStruct
from minegauler.frontend.main_window import MinegaulerGUI
from minegauler.frontend.minefield import MinefieldWidget
from minegauler.frontend.panel import PanelWidget


class TestMinegaulerGUI:
    @pytest.mark.skip
    def test_create(self, qtbot, ctrlr):
        ctrlr.opts = GameOptsStruct()
        gui = MinegaulerGUI(ctrlr)
        assert type(gui._panel_widget) == PanelWidget
        assert type(gui._minefield_widget) == MinefieldWidget
        qtbot.addWidget(gui)
        gui.show()
