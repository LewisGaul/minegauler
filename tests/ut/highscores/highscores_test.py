# June 2020, Lewis Gaul

"""
Tests for the highscores sub-package.

"""

from pathlib import Path
from unittest import mock

import pytest
import requests

import minegauler.app
from minegauler.app import highscores
from minegauler.app.highscores import (
    HighscoreSettings,
    HighscoreStruct,
    SQLiteHighscoresDB,
)
from minegauler.app.shared.types import Difficulty, GameMode, ReachSetting


@pytest.fixture
def tmp_local_db_path(tmp_path: Path) -> Path:
    """File path for creating a temporary local DB."""
    return tmp_path / "highscores.db"


fake_hs_settings = HighscoreSettings(
    game_mode=GameMode.REGULAR,
    difficulty=Difficulty.MASTER,
    per_cell=1,
    reach=ReachSetting.NORMAL,
    drag_select=True,
)
fake_hs = HighscoreStruct(
    settings=fake_hs_settings,
    name="testname",
    timestamp=1234,
    elapsed=166.49,
    bbbv=322,
    flagging=0.2,
)

fake_hs_json = {
    "game_mode": "regular",
    "difficulty": "M",
    "per_cell": 1,
    "reach": 8,
    "drag_select": True,
    "name": "testname",
    "timestamp": 1234,
    "elapsed": 166.49,
    "bbbv": 322,
    "flagging": 0.2,
}


class TestLocalHighscoreDatabase:
    """Tests for interacting with a local highscores database."""

    def test_create_db(self, tmp_local_db_path: Path):
        """Test creating a new highscores DB."""
        db = SQLiteHighscoresDB.create(tmp_local_db_path)
        assert db.path == tmp_local_db_path
        assert db.get_version() == 2
        tables = list(
            db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        )
        assert tables == [("highscores",)]

    def test_insert_count_get(self, tmp_local_db_path: Path):
        """Test inserting, counting and getting highscores."""
        db = SQLiteHighscoresDB.create(tmp_local_db_path)
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
                settings=HighscoreSettings(
                    game_mode=GameMode.REGULAR,
                    difficulty=Difficulty.BEGINNER,
                    per_cell=1,
                    reach=ReachSetting.NORMAL,
                    drag_select=False,
                ),
                name="NAME1",
                timestamp=123400,
                elapsed=3.00,
                bbbv=5,
                flagging=0.2,
            ),
            HighscoreStruct(
                settings=HighscoreSettings(
                    game_mode=GameMode.REGULAR,
                    difficulty=Difficulty.BEGINNER,
                    per_cell=1,
                    reach=ReachSetting.SHORT,
                    drag_select=False,
                ),
                name="NAME2",
                timestamp=123401,
                elapsed=3.11,
                bbbv=5,
                flagging=0.2,
            ),
            HighscoreStruct(
                settings=HighscoreSettings(
                    game_mode=GameMode.REGULAR,
                    difficulty=Difficulty.BEGINNER,
                    per_cell=1,
                    reach=ReachSetting.LONG,
                    drag_select=True,
                ),
                name="NAME1",
                timestamp=123402,
                elapsed=3.22,
                bbbv=5,
                flagging=0.2,
            ),
            HighscoreStruct(
                settings=HighscoreSettings(
                    game_mode=GameMode.REGULAR,
                    difficulty=Difficulty.BEGINNER,
                    per_cell=2,
                    reach=ReachSetting.NORMAL,
                    drag_select=False,
                ),
                name="NAME1",
                timestamp=123403,
                elapsed=3.33,
                bbbv=5,
                flagging=0.2,
            ),
            HighscoreStruct(
                settings=HighscoreSettings(
                    game_mode=GameMode.REGULAR,
                    difficulty=Difficulty.INTERMEDIATE,
                    per_cell=1,
                    reach=ReachSetting.NORMAL,
                    drag_select=False,
                ),
                name="NAME1",
                timestamp=123404,
                elapsed=3.44,
                bbbv=5,
                flagging=0.2,
            ),
            HighscoreStruct(
                settings=HighscoreSettings(
                    game_mode=GameMode.SPLIT_CELL,
                    difficulty=Difficulty.INTERMEDIATE,
                    per_cell=1,
                    reach=ReachSetting.NORMAL,
                    drag_select=False,
                ),
                name="NAME1",
                timestamp=123404,
                elapsed=3.55,
                bbbv=5,
                flagging=0.2,
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

        exp_highscores = {h for h in hscores if h.reach is ReachSetting.NORMAL}
        assert set(db.get_highscores(reach=ReachSetting.NORMAL)) == exp_highscores

        exp_highscores = {h for h in hscores if h.drag_select is False}
        assert set(db.get_highscores(drag_select=False)) == exp_highscores

        exp_highscores = {h for h in hscores if h.name == "NAME1"}
        assert set(db.get_highscores(name="NAME1")) == exp_highscores

        assert list(
            db.get_highscores(
                game_mode=GameMode.REGULAR,
                difficulty=Difficulty.BEGINNER,
                per_cell=1,
                reach=ReachSetting.NORMAL,
                drag_select=False,
                name="NAME1",
            )
        ) == [
            HighscoreStruct(
                settings=HighscoreSettings(
                    game_mode=GameMode.REGULAR,
                    difficulty=Difficulty.BEGINNER,
                    per_cell=1,
                    reach=ReachSetting.NORMAL,
                    drag_select=False,
                ),
                name="NAME1",
                timestamp=123400,
                elapsed=3,
                bbbv=5,
                flagging=0.2,
            )
        ]

        # Case-insensitive name match.
        assert db.get_highscores(name="TEStnaME") == [fake_hs]

    def test_create_insert_reinit(self, tmp_local_db_path: Path):
        """Test creating, inserting a highscore, and re-initialising the DB."""
        assert not tmp_local_db_path.exists()
        db = SQLiteHighscoresDB.create_or_open_with_compat(tmp_local_db_path)
        assert tmp_local_db_path.exists()
        db.insert_highscores([fake_hs])
        db.close()

        db_reinit = SQLiteHighscoresDB.create_or_open_with_compat(tmp_local_db_path)
        assert db_reinit.get_highscores() == [fake_hs]

    def test_no_duplication(self, tmp_local_db_path: Path):
        """Test duplicate highscores are not stored."""
        db = SQLiteHighscoresDB.create(tmp_local_db_path)
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
            reach=None,
            drag_select=None,
            name=None,
        )
        mock_get_hs.reset_mock()

        # Pass filters through.
        highscores.get_highscores(
            game_mode=GameMode.SPLIT_CELL,
            database=mock_db,
            reach=ReachSetting.LONG,
            drag_select=True,
            name="FOO",
        )
        mock_get_hs.assert_called_once_with(
            game_mode=GameMode.SPLIT_CELL,
            difficulty=None,
            per_cell=None,
            reach=ReachSetting.LONG,
            drag_select=True,
            name="FOO",
        )
        mock_get_hs.reset_mock()

        # Settings take precedent.
        highscores.get_highscores(
            database=mock_db,
            settings=HighscoreSettings.original(),
            game_mode="NONSENSE",
            reach=ReachSetting.LONG,
            drag_select=True,
            name="BAR",
        )
        mock_get_hs.assert_called_once_with(
            game_mode=GameMode.REGULAR,
            difficulty=Difficulty.BEGINNER,
            per_cell=1,
            reach=ReachSetting.NORMAL,
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
        highscores.insert_highscore(fake_hs, database=mock_db)
        mock_insert_hs.assert_called_once_with([fake_hs])
        requests.post.assert_called_once_with(
            highscores._REMOTE_POST_URL,
            json={
                "highscore": fake_hs_json,
                "app_version": minegauler.app.__version__,
            },
            timeout=5,
        )
        mock_insert_hs.reset_mock()
        requests.post.reset_mock()
