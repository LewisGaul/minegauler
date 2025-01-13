from __future__ import annotations


__all__ = ("SQLiteDB",)

import logging
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from typing_extensions import Self

from .shared.types import PathLike


logger = logging.getLogger(__name__)


class SQLiteDB:
    """A mixin for SQLite databases."""

    def __init__(self, path: PathLike):
        self._path = Path(path)
        if not self._path.is_file():
            raise FileNotFoundError(f"SQLite DB path not found: {path}")
        self._conn = sqlite3.connect(str(self._path))

    @classmethod
    def create(cls, path: PathLike, *, version: int = 1) -> Self:
        logger.debug("Creating SQLite DB at %s, version=%d", path, version)
        with sqlite3.connect(path) as conn:
            conn.execute(f"PRAGMA user_version = {version}")
        return cls(path)

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    @property
    def path(self) -> Path:
        return self._path

    def close(self) -> None:
        self._conn.close()

    def get_version(self) -> int:
        """Get the database version number."""
        cursor = self.execute("PRAGMA user_version")
        return self.extract_single_elem(cursor)

    @staticmethod
    def extract_single_elem(cursor: sqlite3.Cursor):
        """Extract a single element using a cursor."""
        return next(cursor)[0]

    def execute(
        self, cmd: str, params: tuple = (), *, commit=False, **cursor_args
    ) -> sqlite3.Cursor:
        """
        Execute a command on the database.

        :param cmd:
            The command to execute.
        :param params:
            Parameters to pass to the command.
        :param commit:
            Whether to do a commit after executing the command.
        :param cursor_args:
            Keyword arguments to pass on when creating the DB cursor.
        :return:
            A cursor for the executed command.
        """
        cursor = self.conn.cursor(**cursor_args)
        logger.debug(
            "%s: Executing command %r with params: %s", type(self).__name__, cmd, params
        )
        cursor.execute(cmd, params)
        if commit:
            self.conn.commit()
        return cursor

    def executemany(
        self, cmd: str, params: Iterable[tuple] = (), *, commit=False, **cursor_args
    ) -> sqlite3.Cursor:
        """
        Execute multiple commands on the database.

        :param cmd:
            The commands to execute.
        :param params:
            Parameters to pass to the command.
        :param commit:
            Whether to do a commit after executing the command.
        :param cursor_args:
            Keyword arguments to pass on when creating the DB cursor.
        :return:
            A cursor for the executed command.
        """
        cursor = self.conn.cursor(**cursor_args)
        logger.debug("%s: Executing commands:\n%r", type(self).__name__, cmd)
        cursor.executemany(cmd, params)
        if commit:
            self.conn.commit()
        return cursor
