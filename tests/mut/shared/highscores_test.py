# June 2020, Lewis Gaul

"""
Tests for the highscores module.

"""

import pathlib
import tempfile

import pytest

from minegauler.shared import highscores


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
        db = highscores.LocalHighscoresDB(tmp_local_db_path)
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
        db = highscores.LocalHighscoresDB(tmp_local_db_path)
        assert db.count_highscores() == 0
        assert db.get_highscores() == []


class TestModuleAPIs:
    """Tests for the public module APIs."""

    def test_get_highscores_local(self):
        result = highscores.get_highscores()
