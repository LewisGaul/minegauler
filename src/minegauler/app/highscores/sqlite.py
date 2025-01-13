# December 2019, Felix Gaul

from __future__ import annotations

__all__ = ("SQLiteHighscoresDB",)

import logging
import os
import textwrap
from pathlib import Path
from typing import Iterable, Optional, Mapping

import attrs
from typing_extensions import Self

from . import compat
from ..shared.types import Difficulty, GameMode, ReachSetting, PathLike
from .base import HighscoresDB, HighscoreStruct
from ..sqlite import SQLiteDB


logger = logging.getLogger(__name__)


class SQLiteHighscoresDB(SQLiteDB, HighscoresDB):
    """SQLite highscores DB."""

    VERSION: int = 2

    TABLES: Mapping[GameMode, str] = {m: m.name.lower() for m in GameMode}

    _table_fields = [f.name for f in attrs.fields(HighscoreStruct)][1:]

    def __init__(self, path: PathLike):
        super().__init__(path)
        if (version := self.get_version()) != self.VERSION:
            raise RuntimeError(
                f"DB at {path} has version {version}, expected {self.VERSION}"
            )
        for t in self.TABLES.values():
            self.execute(self._get_create_table_sql(t), commit=True)

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
                tmp_db_path = Path.with_suffix(".new")
                new_db = cls.create(tmp_db_path, version=cls.VERSION)
                new_db.insert_highscores(compat.read_highscores(path))
                # Switch to the new DB.
                new_db.close()
                os.rename(path, path.with_suffix(f".old-v{found_version}"))
                os.rename(tmp_db_path, path)
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
        if game_mode is None:
            modes = list(GameMode)
        else:
            modes = [game_mode]
        ret = []
        for mode in modes:
            self._conn.row_factory = lambda cursor, row: HighscoreStruct(
                game_mode=mode,
                **{col[0]: row[i] for i, col in enumerate(cursor.description)},
            )
            cursor = self.execute(
                self._get_select_highscores_sql(
                    game_mode=mode,
                    difficulty=difficulty,
                    per_cell=per_cell,
                    reach=reach,
                    drag_select=drag_select,
                    name=name,
                )
            )
            ret.extend(cursor.fetchall())
        self._conn.row_factory = None
        return ret

    def count_highscores(self) -> int:
        """Count the number of rows in the highscores table."""
        logger.debug("%s: Counting number of highscores in DB", type(self).__name__)
        return sum(
            self.extract_single_elem(
                self.execute(self._get_highscores_count_sql(game_mode=mode))
            )
            for mode in GameMode
        )

    def insert_highscores(self, highscores: Iterable[HighscoreStruct]) -> int:
        """Insert highscores into the database."""
        logger.debug("%s: Inserting highscores into DB", type(self).__name__)
        orig_count = self.count_highscores()
        for mode in GameMode:
            mode_rows = [h.to_row() for h in highscores if h.game_mode is mode]
            self.executemany(
                self._get_insert_highscore_sql(game_mode=mode),
                mode_rows,
                commit=True,
            )
        return self.count_highscores() - orig_count

    @staticmethod
    def _get_create_table_sql(table_name: str) -> str:
        return textwrap.dedent(
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

    def _get_select_highscores_sql(
        self,
        *,
        game_mode: GameMode,
        difficulty: Optional[Difficulty] = None,
        per_cell: Optional[int] = None,
        reach: Optional[ReachSetting] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> str:
        """Get the SQL command to get/select highscores from a DB."""
        conditions = []
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
            fields=", ".join(self._table_fields),
            table=self.TABLES[game_mode],
            where="WHERE " + " AND ".join(conditions) if conditions else "",
        )

    def _get_insert_highscore_sql(self, *, game_mode: GameMode) -> str:
        """Get the SQL command to insert a highscore into a DB."""
        return "INSERT OR IGNORE INTO {table} ({fields}) VALUES ({fmt})".format(
            table=self.TABLES[game_mode],
            fields=", ".join(self._table_fields),
            fmt=", ".join("?" for _ in self._table_fields),
        )

    def _get_highscores_count_sql(self, *, game_mode: GameMode) -> str:
        """Get the SQL command to count the rows of the highscores table."""
        return f"SELECT COUNT(*) FROM {self.TABLES[game_mode]}"
