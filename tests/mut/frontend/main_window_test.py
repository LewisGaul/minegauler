"""
main_window_test.py - Test the main window of the GUI

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k main_window_test]' from
the root directory.
"""

from unittest.mock import Mock

import pytest

from minegauler.frontend.main_window import MinegaulerGUI


@pytest.fixture
def ctrlr():
    return Mock()


class TestMinegaulerGUI:
    def test_create(self, ctrlr, qtbot):
        gui = MinegaulerGUI(ctrlr)
        qtbot.addWidget(gui)
        gui.show()
        qtbot.waitForWindowShown(gui)