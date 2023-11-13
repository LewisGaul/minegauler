# December 2019, Felix Gaul

__all__ = ("SQLiteDB",)

import logging
import os.path
import pathlib
import sqlite3
from typing import Iterable, Optional, Tuple

from ..shared.types import Difficulty, GameMode, PathLike, ReachSetting
from . import compat
from .base import AbstractHighscoresDB, HighscoreStruct, SQLMixin


logger = logging.getLogger(__name__)


class SQLiteDB(SQLMixin, AbstractHighscoresDB):
    """Database of local highscores."""

    VERSION: int = 2

    def __init__(self, path: PathLike):
        self._path = pathlib.Path(path)
        if self._path.is_file():
            self._conn = sqlite3.connect(str(self._path))
            if self.get_db_version() != self.VERSION:
                logger.warning(
                    "Got SQLite highscore DB on old version '%d', recreating...",
                    self.get_db_version(),
                )
                # Read highscores into new DB using compat subpackage.
                tmp_db_path = str(path) + ".new"
                new_db = self.__class__(tmp_db_path)
                new_db.insert_highscores(compat.read_highscores(self._path))
                # Switch to the new DB.
                new_db.close()
                self._conn.close()
                os.rename(self._path, str(self._path) + ".old")
                os.rename(tmp_db_path, self._path)
                self._conn = sqlite3.connect(str(self._path))
        else:
            logger.debug("Creating SQLite highscores DB")
            os.makedirs(self._path.parent, exist_ok=True)
            self._conn = sqlite3.connect(str(self._path))

            for t in self.TABLES.values():
                self.execute(self._get_create_table_sql(t), commit=True)
            self.execute(f"PRAGMA user_version = {self.VERSION}")

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    @property
    def path(self) -> pathlib.Path:
        return self._path

    def close(self) -> None:
        self._conn.close()

    def get_db_version(self) -> int:
        """Get the database version number."""
        cursor = self.execute("PRAGMA user_version")
        return self.extract_single_elem(cursor)

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
        super().get_highscores(
            game_mode=game_mode,
            difficulty=difficulty,
            per_cell=per_cell,
            reach=reach,
            drag_select=drag_select,
            name=name,
        )
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
        super().count_highscores()
        return sum(
            self.extract_single_elem(
                self.execute(self._get_highscores_count_sql(game_mode=mode))
            )
            for mode in GameMode
        )

    def insert_highscores(self, highscores: Iterable[HighscoreStruct]) -> int:
        super().insert_highscores(highscores)
        orig_count = self.count_highscores()
        for mode in GameMode:
            mode_rows = [h.to_row() for h in highscores if h.game_mode is mode]
            self.executemany(
                self._get_insert_highscore_sql(fmt="?", game_mode=mode),
                mode_rows,
                commit=True,
            )
        return self.count_highscores() - orig_count

    def execute(
        self, cmd: str, params: Tuple = (), *, commit=False, **cursor_args
    ) -> sqlite3.Cursor:
        return super().execute(cmd, params, commit=commit, **cursor_args)

    def executemany(
        self, cmd: str, params: Iterable[Tuple] = (), *, commit=False, **cursor_args
    ) -> sqlite3.Cursor:
        return super().executemany(cmd, params, commit=commit, **cursor_args)
