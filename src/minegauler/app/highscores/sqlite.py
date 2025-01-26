# December 2019, Felix Gaul

from __future__ import annotations


__all__ = ("SQLiteHighscoresDB",)

import logging
import sqlite3
import textwrap
import time
import typing
from collections.abc import Iterable
from pathlib import Path
from typing import Optional

import attrs
from typing_extensions import Self

from ..shared.types import Difficulty, GameMode, PathLike, ReachSetting
from ..sqlite import SQLiteDB
from . import compat
from .types import HighscoresDB, HighscoreSettings, HighscoreStruct


logger = logging.getLogger(__name__)


def highscore_row_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> HighscoreStruct:
    row_dict = {col[0]: row[i] for i, col in enumerate(cursor.description)}
    return HighscoreStruct.from_flat_json(row_dict)


def highscore_to_row(highscore: HighscoreStruct) -> tuple:
    return tuple(highscore.to_flat_json().values())


class SQLiteHighscoresDB(SQLiteDB, HighscoresDB):
    """SQLite highscores DB."""

    VERSION: int = 3

    _TABLE_NAME: typing.Final = "highscores"
    _TABLE_FIELDS: typing.Final = [
        f.name
        for f in (*attrs.fields(HighscoreSettings), *attrs.fields(HighscoreStruct))
        if f.name != "settings"
    ]

    def __init__(self, path: PathLike):
        super().__init__(path)
        if (version := self.get_version()) != self.VERSION:
            raise RuntimeError(
                f"DB at {path} has version {version}, expected {self.VERSION}"
            )
        self.execute(self._get_create_table_sql(), commit=True)

    @classmethod
    def create(cls, path: PathLike, *, version: int = VERSION) -> Self:
        return super().create(path, version=version)

    @classmethod
    def create_or_open_with_compat(cls, path: PathLike) -> Self:
        path = Path(path)
        if not path.exists():
            self = cls.create(path)
        else:
            if (found_version := SQLiteDB(path).get_version()) != cls.VERSION:
                # NOTE: The mechanism of renaming DB files here assumes there is no
                #       other process with the DB open!
                logger.info(
                    "Found SQLite highscores DB on old version '%d', recreating...",
                    found_version,
                )
                # Read highscores into new DB using compat subpackage.
                tmp_db_path = path.with_suffix(".new.db")
                if tmp_db_path.exists():
                    logger.warning("DB already exists at %s, cleaning up", tmp_db_path)
                    tmp_db_path.unlink()
                with cls.create(tmp_db_path, version=cls.VERSION) as new_db:
                    try:
                        new_db.insert_highscores(compat.read_highscores(path))
                    except Exception:
                        archive_path = path.with_suffix(f".{int(time.time())}.db")
                        logger.error(
                            "Failed to port old highscores from DB version %d to new DB, "
                            "saving at %s",
                            found_version,
                            archive_path,
                        )
                        logger.debug("", exc_info=True)
                        path.rename(archive_path)
                    else:
                        path.rename(path.with_suffix(f".old-v{found_version}.db"))
                # Switch to the new DB.
                tmp_db_path.rename(path)
            self = cls(path)
        return self

    def get_highscores(
        self,
        *,
        game_mode: Optional[GameMode] = None,
        difficulty: Optional[Difficulty] = None,
        per_cell: Optional[int] = None,
        reach: Optional[ReachSetting] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Iterable[HighscoreStruct]:
        """Fetch highscores from the database using the given filters."""
        logger.debug("%s: Getting highscores", type(self).__name__)
        cursor = self._conn.cursor()
        cursor.row_factory = highscore_row_factory
        cursor.execute(
            self._get_select_highscores_sql(
                game_mode=game_mode,
                difficulty=difficulty,
                per_cell=per_cell,
                reach=reach,
                drag_select=drag_select,
                name=name,
            )
        )
        return cursor.fetchall()

    def count_highscores(self) -> int:
        """Count the number of rows in the highscores table."""
        logger.debug("%s: Counting number of highscores in DB", type(self).__name__)
        return self.extract_single_elem(self.execute(self._get_highscores_count_sql()))

    def insert_highscores(self, highscores: Iterable[HighscoreStruct]) -> int:
        """Insert highscores into the database."""
        logger.debug("%s: Inserting highscores into DB", type(self).__name__)
        orig_count = self.count_highscores()
        self.executemany(
            self._get_insert_highscore_sql(),
            [highscore_to_row(h) for h in highscores],
            commit=True,
        )
        return self.count_highscores() - orig_count

    @classmethod
    def _get_create_table_sql(cls) -> str:
        return textwrap.dedent(
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

    @classmethod
    def _get_select_highscores_sql(
        cls,
        *,
        game_mode: Optional[GameMode] = None,
        difficulty: Optional[Difficulty] = None,
        per_cell: Optional[int] = None,
        reach: Optional[ReachSetting] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> str:
        """Get the SQL command to get/select highscores from a DB."""
        conditions = []
        if game_mode is not None:
            conditions.append(f"game_mode='{game_mode.value}'")
        if difficulty is not None:
            conditions.append(f"difficulty='{difficulty.value}'")
        if per_cell is not None:
            conditions.append(f"per_cell={per_cell:d}")
        if reach is not None:
            conditions.append(f"reach={reach:d}")
        if drag_select is not None:
            conditions.append(f"drag_select={drag_select:d}")
        if name is not None:
            conditions.append(f"LOWER(name)='{name.lower()}'")
        return "SELECT {fields} FROM {table} {where} ORDER BY elapsed ASC".format(
            fields=", ".join(cls._TABLE_FIELDS),
            table=cls._TABLE_NAME,
            where="WHERE " + " AND ".join(conditions) if conditions else "",
        )

    @classmethod
    def _get_insert_highscore_sql(cls) -> str:
        """Get the SQL command to insert a highscore into a DB."""
        return "INSERT OR IGNORE INTO {table} ({fields}) VALUES ({fmt})".format(
            table=cls._TABLE_NAME,
            fields=", ".join(cls._TABLE_FIELDS),
            fmt=", ".join("?" for _ in cls._TABLE_FIELDS),
        )

    @classmethod
    def _get_highscores_count_sql(cls) -> str:
        """Get the SQL command to count the rows of the highscores table."""
        return f"SELECT COUNT(*) FROM {cls._TABLE_NAME}"
