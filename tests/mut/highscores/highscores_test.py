# June 2020, Lewis Gaul

"""
Tests for the highscores sub-package.

"""

import pathlib
from unittest import mock

import pytest
import requests

import minegauler
from minegauler.app import highscores
from minegauler.app.highscores import HighscoreSettingsStruct, HighscoreStruct
from minegauler.app.shared.types import Difficulty, GameMode


@pytest.fixture
def tmp_local_db_path(tmp_path: pathlib.Path) -> pathlib.Path:
    """File path for creating a temporary local DB."""
    yield tmp_path / "highscores.db"


fake_hs = HighscoreStruct(
    GameMode.REGULAR, "M", 1, True, "testname", 1234, 166.49, 322, 1.94, 0.0
)

fake_hs_json = {
    "game_mode": "regular",
    "difficulty": "M",
    "per_cell": 1,
    "drag_select": True,
    "name": "testname",
    "timestamp": 1234,
    "elapsed": 166.49,
    "bbbv": 322,
    "bbbvps": 1.94,
    "flagging": 0.0,
}


class TestLocalHighscoreDatabase:
    """Tests for interacting with a local highscores database."""

    def test_create_db(self, tmp_local_db_path: pathlib.Path):
        """Test creating a new highscores DB."""
        db = highscores.SQLiteDB(tmp_local_db_path)
        assert db.path == tmp_local_db_path
        assert db.get_db_version() == 1
        tables = list(
            db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        )
        assert list(tables) == [("regular",), ("split_cell",)]

    def test_insert_count_get(self, tmp_local_db_path: pathlib.Path):
        """Test inserting, counting and getting highscores."""
        db = highscores.SQLiteDB(tmp_local_db_path)
        # Empty DB
        assert db.count_highscores() == 0
        assert db.get_highscores() == []

        # Single highscore
        db.insert_highscores([fake_hs])
        hscores = {fake_hs}
        assert db.count_highscores() == 1
        assert set(db.get_highscores()) == hscores

        # Multiple highscores
        multiple_hs = {
            HighscoreStruct(
                GameMode.REGULAR, "B", 1, False, "NAME1", 123400, 3.00, 5, 1.56, 0.0
            ),
            HighscoreStruct(
                GameMode.REGULAR, "B", 1, False, "NAME2", 123401, 3.11, 5, 1.56, 0.0
            ),
            HighscoreStruct(
                GameMode.REGULAR, "B", 1, True, "NAME1", 123402, 3.22, 5, 1.56, 0.0
            ),
            HighscoreStruct(
                GameMode.REGULAR, "B", 2, False, "NAME1", 123403, 3.33, 5, 1.56, 0.0
            ),
            HighscoreStruct(
                GameMode.REGULAR, "I", 1, False, "NAME1", 123404, 3.44, 5, 1.56, 0.0
            ),
            HighscoreStruct(
                GameMode.SPLIT_CELL, "I", 1, False, "NAME1", 123404, 3.55, 5, 1.56, 0.0
            ),
        }
        db.insert_highscores(multiple_hs)
        hscores.update(multiple_hs)
        assert db.count_highscores() == len(hscores)
        assert set(db.get_highscores()) == hscores

        # Filtered highscores
        exp_highscores = {h for h in hscores if h.game_mode is GameMode.SPLIT_CELL}
        assert set(db.get_highscores(game_mode=GameMode.SPLIT_CELL)) == exp_highscores

        exp_highscores = {h for h in hscores if h.difficulty is Difficulty.BEGINNER}
        assert set(db.get_highscores(difficulty=Difficulty.BEGINNER)) == exp_highscores

        exp_highscores = {h for h in hscores if h.per_cell == 1}
        assert set(db.get_highscores(per_cell=1)) == exp_highscores

        exp_highscores = {h for h in hscores if h.drag_select is False}
        assert set(db.get_highscores(drag_select=False)) == exp_highscores

        exp_highscores = {h for h in hscores if h.name == "NAME1"}
        assert set(db.get_highscores(name="NAME1")) == exp_highscores

        assert list(
            db.get_highscores(
                game_mode=GameMode.REGULAR,
                difficulty=Difficulty.BEGINNER,
                per_cell=1,
                drag_select=False,
                name="NAME1",
            )
        ) == [
            HighscoreStruct(
                GameMode.REGULAR, "B", 1, False, "NAME1", 123400, 3, 5, 1.56, 0
            )
        ]

        # Case insensitive name match.
        assert db.get_highscores(name="TEStnaME") == [fake_hs]

    def test_no_duplication(self, tmp_local_db_path: pathlib.Path):
        """Test duplicate highscores are not stored."""
        db = highscores.SQLiteDB(tmp_local_db_path)
        db.insert_highscores([fake_hs, fake_hs])
        db.insert_highscores([fake_hs])
        assert db.count_highscores() == 1
        assert db.get_highscores() == [fake_hs]


class TestModuleAPIs:
    """
    Tests for the public module APIs.

    These tests mock out the actual DB classes, simply checking they are called
    correctly.
    """

    def test_get_highscores(self):
        """Test getting highscores."""
        mock_db = mock.MagicMock()
        mock_get_hs = mock_db.get_highscores
        mock_get_hs.return_value = "DUMMY_RESULT"

        # Basic call passed onto local DB.
        result = highscores.get_highscores(database=mock_db)
        assert result == "DUMMY_RESULT"
        mock_get_hs.assert_called_once_with(
            game_mode=None,
            difficulty=None,
            per_cell=None,
            drag_select=None,
            name=None,
        )
        mock_get_hs.reset_mock()

        # Pass filters through.
        highscores.get_highscores(
            game_mode=GameMode.SPLIT_CELL,
            database=mock_db,
            drag_select=True,
            name="FOO",
        )
        mock_get_hs.assert_called_once_with(
            game_mode=GameMode.SPLIT_CELL,
            difficulty=None,
            per_cell=None,
            drag_select=True,
            name="FOO",
        )
        mock_get_hs.reset_mock()

        # Settings take precedent.
        highscores.get_highscores(
            database=mock_db,
            settings=HighscoreSettingsStruct.get_default(),
            game_mode="NONSENSE",
            drag_select=True,
            name="BAR",
        )
        mock_get_hs.assert_called_once_with(
            game_mode=GameMode.REGULAR,
            difficulty=Difficulty.BEGINNER,
            per_cell=1,
            drag_select=False,
            name="BAR",
        )

    def test_insert_highscore(self, sync_threads):
        """Test inserting a highscore."""
        mock_db = mock.MagicMock()
        mock_insert_hs = mock_db.insert_highscores

        # Basic call passed onto local DB, no post to remote.
        highscores.insert_highscore(fake_hs, database=mock_db, post_remote=False)
        mock_insert_hs.assert_called_once_with([fake_hs])
        mock_insert_hs.reset_mock()

        # Post to remote.
        result = highscores.insert_highscore(fake_hs, database=mock_db)
        mock_insert_hs.assert_called_once_with([fake_hs])
        requests.post.assert_called_once_with(
            highscores._REMOTE_POST_URL,
            json={
                "highscore": fake_hs_json,
                "app_version": minegauler.__version__,
            },
            timeout=5,
        )
        mock_insert_hs.reset_mock()
        requests.post.reset_mock()
