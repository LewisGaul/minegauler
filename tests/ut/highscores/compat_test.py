"""
Tests for the highscore DB version compatibility.

"""

from pathlib import Path

import pytest

import minegauler.app
from minegauler.app.highscores import (
    HighscoreStruct,
)

from . import SQLITE_DB_VERSIONS, create_sqlite_db


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "highscores.db"


@pytest.mark.parametrize(
    "version",
    SQLITE_DB_VERSIONS.keys(),
    ids=(f"v{n}" for n in SQLITE_DB_VERSIONS),
)
def test_read_highscores(version: int, tmp_db: Path):
    highscores = [
        HighscoreStruct.from_flat_json(
            dict(
                game_mode="regular",
                difficulty="B",
                per_cell=1,
                reach=8,
                drag_select=False,
                name="test",
                timestamp=1000,
                elapsed=6.49,
                bbbv=4,
                flagging=0.2,
            ),
        ),
        HighscoreStruct.from_flat_json(
            dict(
                game_mode="regular",
                difficulty="E",
                per_cell=2,
                reach=8,
                drag_select=True,
                name="test",
                timestamp=1001,
                elapsed=10,
                bbbv=40,
                flagging=0,
            ),
        ),
    ]
    if version >= 1:
        highscores.extend(
            [
                HighscoreStruct.from_flat_json(
                    dict(
                        game_mode="split-cell",
                        difficulty="E",
                        per_cell=1,
                        reach=8,
                        drag_select=True,
                        name="test",
                        timestamp=1101,
                        elapsed=100.23,
                        bbbv=65,
                        flagging=0.9,
                    ),
                )
            ]
        )
    if version >= 2:
        highscores.extend(
            [
                HighscoreStruct.from_flat_json(
                    dict(
                        game_mode="regular",
                        difficulty="I",
                        per_cell=1,
                        reach=4,
                        drag_select=True,
                        name="test",
                        timestamp=1201,
                        elapsed=57.1,
                        bbbv=34,
                        flagging=0.9,
                    ),
                ),
                HighscoreStruct.from_flat_json(
                    dict(
                        game_mode="split-cell",
                        difficulty="E",
                        per_cell=1,
                        reach=24,
                        drag_select=True,
                        name="test",
                        timestamp=1202,
                        elapsed=111.3,
                        bbbv=71,
                        flagging=0.9,
                    ),
                ),
            ]
        )
    if version >= 3:
        highscores.extend([])

    create_sqlite_db(tmp_db, version, highscores)

    compat_read = minegauler.app.highscores.compat.read_highscores(tmp_db)

    assert set(compat_read) == set(highscores)
