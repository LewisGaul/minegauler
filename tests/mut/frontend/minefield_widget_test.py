"""
minefield_widget_test.py - Test the minefield widget

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k minefield_widget_test]'
from the root directory.
"""

from minegauler.frontend.minefield_widgets import MinefieldWidget



class TestMinefieldWidget:
    def test_create(self, qtbot, ctrlr):
        widget = MinefieldWidget(None, ctrlr)
        qtbot.addWidget(widget)
        widget.show()