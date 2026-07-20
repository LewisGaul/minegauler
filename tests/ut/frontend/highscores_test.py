# June 2020, Lewis Gaul

"""
Tests for the frontend highscores module (model/view).

"""

import datetime as dt
from collections.abc import Generator
from unittest import mock

import pytest
from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from minegauler.app.frontend.highscores import HighscoresModel, HighscoresWindow
from minegauler.app.frontend.state import HighscoreWindowState
from minegauler.app.highscores import HighscoreSettings, HighscoreStruct
from minegauler.app.shared.types import Difficulty, GameMode, ReachSetting

from . import utils


@pytest.fixture
def hs_settings() -> HighscoreSettings:
    return HighscoreSettings(
        game_mode=GameMode.REGULAR,
        difficulty=Difficulty.BEGINNER,
        per_cell=1,
        reach=ReachSetting.NORMAL,
        drag_select=False,
    )


@pytest.fixture(autouse=True)
def fake_highscores(hs_settings) -> Generator[list[HighscoreStruct], None, None]:
    highscores = [
        HighscoreStruct(
            settings=hs_settings,
            name="John Doe",
            timestamp=int(dt.datetime(2023, 2, 28, i).timestamp()),
            elapsed=100 + i,
            bbbv=4,
            flagging=0.96,
        )
        for i in range(10)
    ]
    with mock.patch(
        "minegauler.app.highscores.get_highscores", return_value=highscores
    ):
        yield highscores


@pytest.fixture
def hs_win_state() -> HighscoreWindowState:
    return HighscoreWindowState()


class TestHighscoresWindow:
    """Test the highscores window."""

    def test_basic_create(self, qtbot: QtBot, hs_settings, hs_win_state):
        """Test basic initialisation of the class."""
        window = HighscoresWindow(None, hs_settings, hs_win_state)
        qtbot.addWidget(window)
        window.show()
        utils.maybe_stop_for_interaction(qtbot)
        assert window.windowTitle() == "Highscores"


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
            model.headerData(
                i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            ).value()
            for i in range(len(model._HEADERS))
        ]
        assert headers == [x.capitalize() for x in model._HEADERS]

        # Check row numbers.
        row_indices = [
            model.headerData(
                i, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole
            ).value()
            for i in range(10)
        ]
        assert row_indices == [str(x + 1) for x in range(10)]
