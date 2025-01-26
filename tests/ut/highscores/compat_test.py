"""
Tests for the highscore DB version compatibility.

"""

import abc
import sqlite3
import textwrap
from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

import minegauler.app
from minegauler.app.highscores import (
    HighscoreStruct,
    SQLiteHighscoresDB,
)
from minegauler.app.shared.types import GameMode, ReachSetting


class AbstractSQLiteDBVersion(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_create_tables_sql(cls) -> Iterable[str]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_insert_row_sql(cls, highscore: HighscoreStruct) -> str:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def highscore_to_row(cls, highscore: HighscoreStruct) -> tuple:
        raise NotImplementedError


class SQLiteDBVersion0(AbstractSQLiteDBVersion):
    # https://github.com/LewisGaul/minegauler/blob/v4.1.1/minegauler/shared/highscores.py

    _TABLE_NAME = "highscores"
    _TABLE_FIELDS = (
        "difficulty",
        "per_cell",
        "drag_select",
        "name",
        "timestamp",
        "elapsed",
        "bbbv",
        "bbbvps",
        "flagging",
    )

    @classmethod
    def get_create_tables_sql(cls) -> Iterable[str]:
        return [
            textwrap.dedent(
                f"""\
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                    id INTEGER PRIMARY KEY,
                    difficulty VARCHAR(1) NOT NULL,
                    per_cell INTEGER NOT NULL,
                    drag_select INTEGER NOT NULL,
                    name VARCHAR(20) NOT NULL,
                    timestamp INTEGER NOT NULL,
                    elapsed REAL NOT NULL,
                    bbbv INTEGER NOT NULL,
                    bbbvps REAL NOT NULL,
                    flagging REAL NOT NULL
                )"""
            )
        ]

    @classmethod
    def get_insert_row_sql(cls, highscore: HighscoreStruct) -> str:
        return "INSERT INTO {table} ({fields}) VALUES ({fmt_})".format(
            table=cls._TABLE_NAME,
            fields=", ".join(cls._TABLE_FIELDS),
            fmt_=", ".join("?" for _ in cls._TABLE_FIELDS),
        )

    @classmethod
    def highscore_to_row(cls, highscore: HighscoreStruct) -> tuple:
        if highscore.settings.game_mode is not GameMode.REGULAR:
            raise ValueError(
                f"Unsupported game mode {highscore.settings.game_mode.value!r}"
            )
        if highscore.settings.reach is not ReachSetting.NORMAL:
            raise ValueError(
                f"Unsupported reach setting {highscore.settings.reach.value!r}"
            )
        return (
            highscore.settings.difficulty.value,
            highscore.settings.per_cell,
            int(highscore.settings.drag_select),
            highscore.name,
            highscore.timestamp,
            highscore.elapsed,
            highscore.bbbv,
            highscore.bbbv / highscore.elapsed,
            highscore.flagging,
        )


class SQLiteDBVersion1(AbstractSQLiteDBVersion):
    # https://github.com/LewisGaul/minegauler/blob/v4.1.2/minegauler/highscores/base.py

    _TABLE_NAMES = ("regular", "split_cell")
    _TABLE_FIELDS = (
        "difficulty",
        "per_cell",
        "drag_select",
        "name",
        "timestamp",
        "elapsed",
        "bbbv",
        "bbbvps",
        "flagging",
    )

    @classmethod
    def get_create_tables_sql(cls) -> Iterable[str]:
        return [
            textwrap.dedent(
                f"""\
                CREATE TABLE IF NOT EXISTS {table_name} (
                    difficulty VARCHAR(1) NOT NULL,
                    per_cell INTEGER NOT NULL,
                    drag_select INTEGER NOT NULL,
                    name VARCHAR(20) NOT NULL,
                    timestamp INTEGER NOT NULL,
                    elapsed REAL NOT NULL,
                    bbbv INTEGER NOT NULL,
                    bbbvps REAL NOT NULL,
                    flagging REAL NOT NULL,
                    PRIMARY KEY(difficulty, name, timestamp)
                )"""
            )
            for table_name in cls._TABLE_NAMES
        ]

    @classmethod
    def get_insert_row_sql(cls, highscore: HighscoreStruct) -> str:
        if highscore.settings.game_mode not in [GameMode.REGULAR, GameMode.SPLIT_CELL]:
            raise ValueError(
                f"Unsupported game mode {highscore.settings.game_mode.value!r}"
            )
        return "INSERT INTO {table} ({fields}) VALUES ({fmt_})".format(
            table=highscore.settings.game_mode.name.lower(),
            fields=", ".join(cls._TABLE_FIELDS),
            fmt_=", ".join("?" for _ in cls._TABLE_FIELDS),
        )

    @classmethod
    def highscore_to_row(cls, highscore: HighscoreStruct) -> tuple:
        if highscore.settings.reach is not ReachSetting.NORMAL:
            raise ValueError(
                f"Unsupported reach setting {highscore.settings.reach.value!r}"
            )
        return (
            highscore.settings.difficulty.value,
            highscore.settings.per_cell,
            int(highscore.settings.drag_select),
            highscore.name,
            highscore.timestamp,
            highscore.elapsed,
            highscore.bbbv,
            highscore.bbbv / highscore.elapsed,
            highscore.flagging,
        )


class SQLiteDBVersion2(AbstractSQLiteDBVersion):
    # https://github.com/LewisGaul/minegauler/blame/v4.2.0/src/minegauler/app/highscores/base.py

    _TABLE_NAMES = ("regular", "split_cell")
    _TABLE_FIELDS = (
        "difficulty",
        "per_cell",
        "reach",
        "drag_select",
        "name",
        "timestamp",
        "elapsed",
        "bbbv",
        "bbbvps",
        "flagging",
    )

    @classmethod
    def get_create_tables_sql(cls) -> Iterable[str]:
        return [
            textwrap.dedent(
                f"""\
                CREATE TABLE IF NOT EXISTS {table_name} (
                    difficulty VARCHAR(1) NOT NULL,
                    per_cell INTEGER NOT NULL,
                    reach INTEGER NOT NULL,
                    drag_select INTEGER NOT NULL,
                    name VARCHAR(20) NOT NULL,
                    timestamp INTEGER NOT NULL,
                    elapsed REAL NOT NULL,
                    bbbv INTEGER NOT NULL,
                    bbbvps REAL NOT NULL,
                    flagging REAL NOT NULL,
                    PRIMARY KEY(difficulty, name, timestamp)
                )"""
            )
            for table_name in cls._TABLE_NAMES
        ]

    @classmethod
    def get_insert_row_sql(cls, highscore: HighscoreStruct) -> str:
        if highscore.settings.game_mode not in [GameMode.REGULAR, GameMode.SPLIT_CELL]:
            raise ValueError(
                f"Unsupported game mode {highscore.settings.game_mode.value!r}"
            )
        return "INSERT INTO {table} ({fields}) VALUES ({fmt_})".format(
            table=highscore.settings.game_mode.name.lower(),
            fields=", ".join(cls._TABLE_FIELDS),
            fmt_=", ".join("?" for _ in cls._TABLE_FIELDS),
        )

    @classmethod
    def highscore_to_row(cls, highscore: HighscoreStruct) -> tuple:
        return (
            highscore.settings.difficulty.value,
            highscore.settings.per_cell,
            highscore.settings.reach.value,
            int(highscore.settings.drag_select),
            highscore.name,
            highscore.timestamp,
            highscore.elapsed,
            highscore.bbbv,
            highscore.bbbv / highscore.elapsed,
            highscore.flagging,
        )


class SQLiteDBVersion3(AbstractSQLiteDBVersion):
    # src/minegauler/app/highscores/sqlite.py

    _TABLE_NAME = "highscores"
    _TABLE_FIELDS = (
        "game_mode",
        "difficulty",
        "per_cell",
        "reach",
        "drag_select",
        "name",
        "timestamp",
        "elapsed",
        "bbbv",
        "flagging",
    )

    @classmethod
    def get_create_tables_sql(cls) -> Iterable[str]:
        return [
            textwrap.dedent(
                f"""\
                CREATE TABLE IF NOT EXISTS {cls._TABLE_NAME} (
                    game_mode TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    per_cell INTEGER NOT NULL,
                    reach INTEGER NOT NULL,
                    drag_select INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    elapsed REAL NOT NULL,
                    bbbv INTEGER NOT NULL,
                    flagging REAL NOT NULL,
                    PRIMARY KEY (name, timestamp)
                )"""
            )
        ]

    @classmethod
    def get_insert_row_sql(cls, highscore: HighscoreStruct) -> str:
        return "INSERT INTO {table} ({fields}) VALUES ({fmt_})".format(
            table=cls._TABLE_NAME,
            fields=", ".join(cls._TABLE_FIELDS),
            fmt_=", ".join("?" for _ in cls._TABLE_FIELDS),
        )

    @classmethod
    def highscore_to_row(cls, highscore: HighscoreStruct) -> tuple:
        return (
            highscore.settings.game_mode.value,
            highscore.settings.difficulty.value,
            highscore.settings.per_cell,
            highscore.settings.reach.value,
            int(highscore.settings.drag_select),
            highscore.name,
            highscore.timestamp,
            highscore.elapsed,
            highscore.bbbv,
            highscore.flagging,
        )


SQLITE_DB_VERSIONS: Mapping[int, AbstractSQLiteDBVersion] = {
    0: SQLiteDBVersion0,
    1: SQLiteDBVersion1,
    2: SQLiteDBVersion2,
    3: SQLiteDBVersion3,
}

# Ensure any new SQLite DB versions are added.
assert list(SQLITE_DB_VERSIONS) == list(range(SQLiteHighscoresDB.VERSION + 1))


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "highscores.db"


@pytest.mark.parametrize(
    ("version", "db_info"),
    SQLITE_DB_VERSIONS.items(),
    ids=(f"v{n}" for n in SQLITE_DB_VERSIONS),
)
def test_read_highscores(version: int, db_info: AbstractSQLiteDBVersion, tmp_db: Path):
    db_conn = sqlite3.connect(tmp_db)
    if version > 0:
        # Initial DB did not have version explicitly set.
        with db_conn:
            db_conn.execute(f"PRAGMA user_version = {version}")
    with db_conn:
        for create_table_sql in db_info.get_create_tables_sql():
            db_conn.execute(create_table_sql)
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
    with db_conn:
        for hs in highscores:
            insert_row_sql = db_info.get_insert_row_sql(hs)
            hs_row = db_info.highscore_to_row(hs)
            db_conn.execute(insert_row_sql, hs_row)

    compat_read = minegauler.app.highscores.compat.read_highscores(tmp_db)

    assert set(compat_read) == set(highscores)
