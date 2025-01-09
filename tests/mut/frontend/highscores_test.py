# June 2020, Lewis Gaul

"""
Tests for the frontend highscores module (model/view).

"""

import pytest
from PyQt6.QtCore import Qt

from minegauler.app.frontend.highscores import HighscoresModel
from minegauler.app.frontend.state import HighscoreWindowState


@pytest.fixture
def hs_win_state() -> HighscoreWindowState:
    return HighscoreWindowState()


class TestHighscoresModel:
    """Test the highscores model."""

    def test_basic_create(self, hs_win_state):
        """Test basic initialisation of the class."""
        model = HighscoresModel(None, hs_win_state)

        # Check number of rows/columns.
        assert model.columnCount() == len(model._HEADERS)
        assert model.rowCount() == 0

        # Check headers.
        headers = [
            model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole).value()
            for i in range(len(model._HEADERS))
        ]
        assert headers == [x.capitalize() for x in model._HEADERS]

        # Check row numbers.
        row_indices = [
            model.headerData(i, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole).value() for i in range(10)
        ]
        assert row_indices == [str(x + 1) for x in range(10)]
