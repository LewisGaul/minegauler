"""
main_window_test.py - Test the main window of the GUI

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k main_window_test]' from
the root directory.
"""


import pytest

from minegauler.frontend.main_window import MinegaulerGUI
from minegauler.frontend.minefield_widgets import MinefieldWidget
from minegauler.frontend.panel_widgets import PanelWidget
from minegauler.shared.utils import GameOptsStruct



class TestMinegaulerGUI:
    @pytest.mark.skip
    def test_create(self, qtbot, ctrlr):
        ctrlr.opts = GameOptsStruct()
        gui = MinegaulerGUI(ctrlr)
        assert type(gui.panel_widget) == PanelWidget
        assert type(gui.minefield_widget) == MinefieldWidget
        qtbot.addWidget(gui)
        gui.show()