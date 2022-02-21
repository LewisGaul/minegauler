# February 2022, Lewis Gaul

"""
Base classes/implementations for highscore handling.

"""

__all__ = (
    "HighscoreSettingsStruct",
    "HighscoreStruct",
    "AbstractHighscoresDB",
    "SQLMixin",
)

import abc
import logging
import textwrap
from typing import Iterable, Mapping, Optional, Tuple

import attr

from ..shared.types import Difficulty, GameMode
from ..shared.utils import StructConstructorMixin


logger = logging.getLogger(__name__)


@attr.attrs(auto_attribs=True, frozen=True)
class HighscoreSettingsStruct(StructConstructorMixin):
    """A set of highscore settings."""

    game_mode: GameMode = attr.attrib(converter=GameMode.from_str)
    difficulty: Difficulty = attr.attrib(converter=Difficulty.from_str)
    per_cell: int
    drag_select: bool = attr.attrib(converter=bool)

    @classmethod
    def get_default(cls) -> "HighscoreSettingsStruct":
        return cls(GameMode.REGULAR, Difficulty.BEGINNER, 1, False)


@attr.attrs(auto_attribs=True, frozen=True)
class HighscoreStruct(HighscoreSettingsStruct):
    """A single highscore."""

    name: str
    timestamp: int
    elapsed: float
    bbbv: int
    bbbvps: float
    flagging: float


class AbstractHighscoresDB(abc.ABC):
    """Abstract base class for a highscores database."""

    @property
    @abc.abstractmethod
    def conn(self):
        """The active database connection."""
        return NotImplemented

    @staticmethod
    def extract_single_elem(cursor):
        """Extract a single element using a cursor."""
        return next(cursor)[0]

    @abc.abstractmethod
    def get_highscores(
        self,
        *,
        game_mode: Optional[GameMode] = None,
        difficulty: Optional[Difficulty] = None,
        per_cell: Optional[int] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Iterable[HighscoreStruct]:
        """Fetch highscores from the database using the given filters."""
        logger.debug("%s: Getting highscores", type(self).__name__)
        return NotImplemented

    @abc.abstractmethod
    def count_highscores(self) -> int:
        """Count the number of rows in the highscores table."""
        logger.debug("%s: Counting number of highscores in DB", type(self).__name__)
        return NotImplemented

    @abc.abstractmethod
    def insert_highscores(self, highscores: Iterable[HighscoreStruct]) -> int:
        """Insert highscores into the database."""
        logger.debug("%s: Inserting highscores into DB", type(self).__name__)
        return NotImplemented

    def execute(self, cmd: str, params: Tuple = (), *, commit=False, **cursor_args):
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
        self, cmd: str, params: Iterable[Tuple] = (), *, commit=False, **cursor_args
    ):
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
        """
        cursor = self.conn.cursor(**cursor_args)
        logger.debug("%s: Executing commands:\n%r", type(self).__name__, cmd)
        cursor.executemany(cmd, params)
        if commit:
            self.conn.commit()
        return cursor


class SQLMixin:
    """A mixin for SQL-like highscores databases."""

    TABLES: Mapping[GameMode, str] = {m: m.name.lower() for m in GameMode}

    _table_fields = [f.name for f in attr.fields(HighscoreStruct)][1:]

    def _get_create_table_sql(self, table_name: str) -> str:
        return textwrap.dedent(
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

    def _get_select_highscores_sql(
        self,
        *,
        game_mode: GameMode,
        difficulty: Optional[Difficulty] = None,
        per_cell: Optional[int] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> str:
        """Get the SQL command to get/select highscores from a DB."""
        conditions = []
        if difficulty is not None:
            conditions.append(f"difficulty='{difficulty.value}'")
        if per_cell is not None:
            conditions.append(f"per_cell={per_cell}")
        if drag_select is not None:
            conditions.append(f"drag_select={drag_select:d}")
        if name is not None:
            conditions.append(f"LOWER(name)='{name.lower()}'")
        return "SELECT {fields} FROM {table} {where} ORDER BY elapsed ASC".format(
            fields=", ".join(self._table_fields),
            table=self.TABLES[game_mode],
            where="WHERE " + " AND ".join(conditions) if conditions else "",
        )

    def _get_insert_highscore_sql(self, fmt="%s", *, game_mode: GameMode) -> str:
        """Get the SQL command to insert a highscore into a DB."""
        return "INSERT OR IGNORE INTO {table} ({fields}) VALUES ({fmt_})".format(
            table=self.TABLES[game_mode],
            fields=", ".join(self._table_fields),
            fmt_=", ".join(fmt for _ in self._table_fields),
        )

    def _get_highscores_count_sql(self, *, game_mode: GameMode) -> str:
        """Get the SQL command to count the rows of the highscores table."""
        return f"SELECT COUNT(*) FROM {self.TABLES[game_mode]}"
