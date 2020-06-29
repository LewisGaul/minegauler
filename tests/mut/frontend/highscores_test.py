# June 2020, Lewis Gaul

"""
Tests for the frontend highscores module (model/view).

"""
import pytest

from minegauler.frontend.highscores import HighscoresModel
from minegauler.frontend.state import HighscoreWindowState


@pytest.fixture
def hs_win_state() -> HighscoreWindowState:
    return HighscoreWindowState()


class TestHighscoresModel:
    """Test the highscores model."""

    def test_basic_create(self, hs_win_state):
        """Test basic initialisation of the class."""
        model = HighscoresModel(None, hs_win_state)
