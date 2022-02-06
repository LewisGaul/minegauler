# December 2019, Felix Gaul

__all__ = ("SQLiteDB",)

import os.path
import pathlib
import sqlite3
from typing import Iterable, Optional, Tuple

import attr

from ..shared.types import Difficulty, GameMode, PathLike
from .base import AbstractHighscoresDB, HighscoreStruct, SQLMixin


class SQLiteDB(SQLMixin, AbstractHighscoresDB):
    """Database of local highscores."""

    def __init__(self, path: pathlib.Path):
        self._path = path
        if os.path.exists(path):
            self._conn = sqlite3.connect(str(path))
        else:
            os.makedirs(path.parent, exist_ok=True)
            self._conn = sqlite3.connect(str(path))

            for t in self.TABLES.values():
                self.execute(self._get_create_table_sql(t))
            self.execute("PRAGMA user_version = 1")

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    @property
    def path(self) -> pathlib.Path:
        return self._path

    def get_db_version(self) -> int:
        """Get the database version number."""
        cursor = self.execute("PRAGMA user_version")
        return self.extract_single_elem(cursor)

    def get_highscores(
        self,
        *,
        game_mode: GameMode = GameMode.REGULAR,
        difficulty: Optional[Difficulty] = None,
        per_cell: Optional[int] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Iterable[HighscoreStruct]:
        super().get_highscores(
            game_mode=game_mode,
            difficulty=difficulty,
            per_cell=per_cell,
            drag_select=drag_select,
            name=name,
        )
        self._conn.row_factory = lambda cursor, row: HighscoreStruct(
            mode=game_mode,
            **{col[0]: row[i] for i, col in enumerate(cursor.description)},
        )
        cursor = self.execute(
            self._get_select_highscores_sql(
                game_mode=game_mode,
                difficulty=difficulty,
                per_cell=per_cell,
                drag_select=drag_select,
                name=name,
            )
        )
        self._conn.row_factory = None
        return cursor.fetchall()

    def count_highscores(self) -> int:
        """Count the number of rows in the highscores table."""
        super().count_highscores()
        return next(self.execute(self._get_highscores_count_sql()))[0]

    def merge_highscores(self, path: PathLike) -> int:
        """Merge in highscores from a given other SQLite DB."""
        if pathlib.Path(path) == self._path:
            raise ValueError("Cannot merge database into itself")

        for table in self.TABLES.values():
            tmp_table = "mergedTable"
            attach_db = "toMergeDB"

            first_count = self.count_highscores()
            self.execute(f"ATTACH DATABASE '{path!s}' AS {attach_db}")

            self.execute(
                f"CREATE TABLE IF NOT EXISTS {tmp_table} AS "
                f"SELECT * FROM {table} UNION SELECT * FROM {attach_db}.{table}"
            )
            # TODO: This is not completely atomic, can we do better?
            self.execute(f"DROP TABLE IF EXISTS {table}")
            self.execute(f"ALTER TABLE {tmp_table} RENAME TO {table}")
            self.execute(f"DETACH DATABASE {attach_db}")
            self.conn.commit()
            return self.count_highscores() - first_count

    def insert_highscore(self, highscore: HighscoreStruct) -> None:
        super().insert_highscore(highscore)
        self.execute(
            self._get_insert_highscore_sql(fmt="?", game_mode=highscore.mode),
            attr.astuple(highscore)[1:],
            commit=True,
        )

    def execute(
        self, cmd: str, params: Tuple = (), *, commit=False, **cursor_args
    ) -> sqlite3.Cursor:
        return super().execute(cmd, params, commit=commit, **cursor_args)
