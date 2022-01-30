# June 2020, Lewis Gaul

"""
Tests for the highscores module.

"""

import pathlib
import tempfile
from unittest import mock

import pytest

from minegauler.shared.highscores import (
    HighscoresDatabases,
    HighscoreSettingsStruct,
    HighscoreStruct,
    LocalHighscoresDB,
    get_highscores,
)
from minegauler.shared.types import Difficulty


@pytest.fixture(scope="module")
def tmpdir() -> pathlib.Path:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.fixture
def tmp_local_db_path(tmpdir) -> pathlib.Path:
    """File path for creating a temporary local DB."""
    f = tmpdir / "highscores.db"
    yield f
    f.unlink()


class TestLocalHighscoreDatabase:
    """Tests for interacting with a local highscores database."""

    def test_create_db(self, tmp_local_db_path):
        """Test creating a new highscores DB."""
        db = LocalHighscoresDB(tmp_local_db_path)
        assert db._path == tmp_local_db_path
        assert db.get_db_version() == 0
        tables = list(
            db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        )
        assert list(tables) == [("highscores",)]

    def test_insert_count_get(self, tmp_local_db_path):
        """Test inserting, counting and getting highscores."""
        db = LocalHighscoresDB(tmp_local_db_path)
        # Empty DB
        highscores = []
        assert db.count_highscores() == 0
        assert db.get_highscores() == []

        # Single highscore
        my_hs = HighscoreStruct("M", 1, True, "Siwel G", 1234, 166.49, 322, 1.94, 0.0)
        db.insert_highscore(my_hs)
        highscores.append(my_hs)
        assert db.count_highscores() == 1
        assert db.get_highscores() == highscores

        # Multiple highscores
        for hs in [
            HighscoreStruct("B", 1, False, "NAME1", 1234, 3.00, 5, 1.56, 0.0),
            HighscoreStruct("B", 1, False, "NAME2", 1234, 3.11, 5, 1.56, 0.0),
            HighscoreStruct("B", 1, True, "NAME1", 1234, 3.22, 5, 1.56, 0.0),
            HighscoreStruct("B", 2, False, "NAME1", 1234, 3.33, 5, 1.56, 0.0),
            HighscoreStruct("I", 1, False, "NAME1", 1234, 3.44, 5, 1.56, 0.0),
        ]:
            db.insert_highscore(hs)
            highscores.append(hs)
        highscores.sort(key=lambda h: h.elapsed)
        assert db.count_highscores() == len(highscores)
        assert db.get_highscores() == highscores

        # Filtered highscores
        exp_highscores = [h for h in highscores if h.difficulty is Difficulty.BEGINNER]
        assert db.get_highscores(difficulty=Difficulty.BEGINNER) == exp_highscores

        exp_highscores = [h for h in highscores if h.per_cell == 1]
        assert db.get_highscores(per_cell=1) == exp_highscores

        exp_highscores = [h for h in highscores if h.drag_select is False]
        assert db.get_highscores(drag_select=False) == exp_highscores

        exp_highscores = [h for h in highscores if h.name == "NAME1"]
        assert db.get_highscores(name="NAME1") == exp_highscores

        assert db.get_highscores(
            difficulty=Difficulty.BEGINNER,
            per_cell=1,
            drag_select=False,
            name="NAME1",
        ) == [HighscoreStruct("B", 1, False, "NAME1", 1234, 3, 5, 1.56, 0)]

        # Case insensitive name match.
        assert db.get_highscores(name="SIWel g") == [my_hs]

    def test_merge_db(self, tmpdir):
        """Test merging DBs together."""
        # Setup
        base_db = LocalHighscoresDB(tmpdir / "merge-base.db")
        merge_db = LocalHighscoresDB(tmpdir / "merge-from.db")
        base_highscores = sorted(
            [
                HighscoreStruct("B", 1, False, "NAME1", 1234, 3.00, 5, 1.56, 0.0),
                HighscoreStruct("B", 1, False, "NAME2", 1234, 3.11, 5, 1.56, 0.0),
                HighscoreStruct("B", 1, True, "NAME1", 1234, 3.22, 5, 1.56, 0.0),
                HighscoreStruct("B", 2, False, "NAME1", 1234, 3.33, 5, 1.56, 0.0),
                HighscoreStruct("I", 1, False, "NAME1", 1234, 3.44, 5, 1.56, 0.0),
            ],
            key=lambda h: h.elapsed,
        )
        merge_highscores = sorted(
            [
                *base_highscores[:3],
                HighscoreStruct("E", 3, True, "", 1234, 4.00, 5, 1.56, 0.0),
                HighscoreStruct("E", 3, True, "blob", 1234, 4.01, 5, 1.56, 0.0),
                HighscoreStruct("B", 1, False, "blob", 1234, 4.11, 5, 1.56, 0.0),
            ],
            key=lambda h: h.elapsed,
        )
        for hs in base_highscores:
            base_db.insert_highscore(hs)
        for hs in merge_highscores:
            merge_db.insert_highscore(hs)

        assert base_db.count_highscores() == len(base_highscores)
        assert base_db.get_highscores() == base_highscores
        assert merge_db.count_highscores() == len(merge_highscores)
        assert merge_db.get_highscores() == merge_highscores

        # Merge
        base_db.merge_highscores(merge_db.path)
        combined_highscores = sorted(
            set(base_highscores) | set(merge_highscores), key=lambda h: h.elapsed
        )
        assert base_db.count_highscores() == len(combined_highscores)
        assert base_db.get_highscores() == combined_highscores
        assert merge_db.count_highscores() == len(merge_highscores)
        assert merge_db.get_highscores() == merge_highscores

    def test_merge_db_into_itself_error(self, tmp_local_db_path):
        """Test error is raised when trying to merge DB into itself."""
        db = LocalHighscoresDB(tmp_local_db_path)
        with pytest.raises(ValueError):
            db.merge_highscores(db.path)


class TestModuleAPIs:
    """
    Tests for the public module APIs.

    These tests mock out the actual DB classes, simply checking they are called
    correctly.
    """

    @mock.patch.object(HighscoresDatabases, "get_db_instance")
    def test_get_highscores(self, mock_get_db):
        """Test getting highscores."""
        mock_get_hs = mock_get_db.return_value.get_highscores
        mock_get_hs.return_value = "DUMMY_RESULT"

        # Basic call passed onto local DB.
        result = get_highscores()
        assert result == "DUMMY_RESULT"
        mock_get_hs.assert_called_once_with(
            difficulty=None, per_cell=None, drag_select=None, name=None
        )
        mock_get_hs.reset_mock()

        # Pass filters through.
        get_highscores(drag_select=True, name="FOO")
        mock_get_hs.assert_called_once_with(
            difficulty=None, per_cell=None, drag_select=True, name="FOO"
        )
        mock_get_hs.reset_mock()

        # Settings take precedent.
        get_highscores(
            settings=HighscoreSettingsStruct.get_default(),
            drag_select=True,
            name="BAR",
        )
        mock_get_hs.assert_called_once_with(
            difficulty=Difficulty.BEGINNER,
            per_cell=1,
            drag_select=False,
            name="BAR",
        )
