# February 2022, Lewis Gaul

"""
MySQL highscores database interface.
"""

__all__ = ("MySQLDB",)

import logging
import os
from typing import Iterable, Optional, Tuple

import attr
import mysql.connector
import mysql.connector.cursor

from ..shared.types import Difficulty, GameMode
from .base import AbstractHighscoresDB, HighscoreStruct, SQLMixin


################################################################################
# WARNING: This module should not be used by the minegauler package directly as
#          it adds the mysql-connector dependency.
################################################################################


logger = logging.getLogger(__name__)


class MySQLDB(SQLMixin, AbstractHighscoresDB):
    """MySQL highscores database."""

    _USER = "admin"
    _HOST = "minegauler-highscores.cb4tvkuqujyi.eu-west-2.rds.amazonaws.com"
    _DB_NAME = "minegauler"

    _cached_conn: Optional[mysql.connector.MySQLConnection] = None

    def __init__(self):
        """
        :raise mysql.connector.Error:
            If connecting to the DB fails for any reason.
        """
        cls = type(self)
        if not cls._cached_conn:
            logger.info("Initialising connection to MySQL highscores DB")
            cls._cached_conn = mysql.connector.connect(
                user=self._USER,
                password=self._PASSWORD,
                host=self._HOST,
                database=self._DB_NAME,
            )
        self._conn = cls._cached_conn

    @property
    def conn(self) -> mysql.connector.MySQLConnection:
        return self._conn

    @property
    def _PASSWORD(self):
        return os.environ.get("MINEGAULER_MYSQL_DB_PASSWORD")

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
            difficulty=difficulty,
            per_cell=per_cell,
            drag_select=drag_select,
            game_mode=game_mode,
            name=name,
        )
        cursor = self.execute(
            self._get_select_highscores_sql(
                game_mode=game_mode,
                difficulty=difficulty,
                per_cell=per_cell,
                drag_select=drag_select,
                name=name,
            ),
            dictionary=True,
        )
        return [HighscoreStruct(mode=game_mode, **r) for r in cursor.fetchall()]

    def count_highscores(self) -> int:
        """Count the number of rows in the highscores table."""
        super().count_highscores()
        return next(self.execute(self._get_highscores_count_sql()))[0]

    def insert_highscores(self, highscores: Iterable[HighscoreStruct]) -> None:
        super().insert_highscores(highscores)
        orig_count = self.count_highscores()
        for mode in GameMode:
            mode_rows = [attr.astuple(h)[1:] for h in highscores if h.mode is mode]
            self.executemany(
                self._get_insert_highscore_sql(fmt="?", game_mode=mode),
                mode_rows,
                commit=True,
            )
        return self.count_highscores() - orig_count

    def execute(
        self, cmd: str, params: Tuple = (), *, commit=False, **cursor_args
    ) -> mysql.connector.cursor.MySQLCursor:
        return super().execute(cmd, params, commit=commit, **cursor_args)

    def executemany(
        self, cmd: str, params: Iterable[Tuple] = (), *, commit=False, **cursor_args
    ) -> mysql.connector.cursor.MySQLCursor:
        return super().executemany(cmd, params, commit=commit, **cursor_args)
