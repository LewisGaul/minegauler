"""
highscores.py - Highscores handling

December 2019, Felix Gaul
"""

__all__ = (
    "HighscoreSettingsStruct",
    "HighscoreStruct",
    "HighscoresDatabases",
    "filter_and_sort",
    "get_highscores",
    "insert_highscore",
)

import abc
import enum
import logging
import os
import sqlite3
import threading
from textwrap import dedent
from typing import Dict, Iterable, List, Optional, Tuple

import attr
import mysql.connector
import requests

from .. import ROOT_DIR
from ..utils import StructConstructorMixin
from . import utils


logger = logging.getLogger(__name__)

_REMOTE_POST_URL = "http://minegauler.lewisgaul.co.uk/api/v1/highscore"


@attr.attrs(auto_attribs=True)
class HighscoreSettingsStruct(StructConstructorMixin):
    """A set of highscore settings."""

    difficulty: str
    per_cell: int
    drag_select: bool

    def __getitem__(self, item):
        return getattr(self, item)

    @classmethod
    def get_default(cls) -> "HighscoreSettingsStruct":
        return cls("B", 1, False)


@attr.attrs(auto_attribs=True)
class HighscoreStruct(HighscoreSettingsStruct):
    """A single highscore."""

    name: str
    timestamp: int
    elapsed: float
    bbbv: int
    bbbvps: float
    flagging: float

    @classmethod
    def from_sqlite_row(cls, cursor: sqlite3.Cursor, row: Tuple) -> "HighscoreStruct":
        """Create an instance from an SQLite row."""
        return cls(**{col[0]: row[i] for i, col in enumerate(cursor.description)})


_highscore_fields = attr.fields_dict(HighscoreStruct).keys()


class DBConnectionError(Exception):
    """Unable to connect to a database."""


class AbstractHighscoresDB(abc.ABC):
    """Abstract base class for a highscores database."""

    @property
    @abc.abstractmethod
    def conn(self):
        """The active database connection."""
        return None

    @abc.abstractmethod
    def get_highscores(
        self,
        *,
        difficulty: Optional[str] = None,
        per_cell: Optional[int] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Iterable[HighscoreStruct]:
        """Fetch highscores from the database using the given filters."""
        logger.debug("%s: Getting highscores", type(self).__name__)

    @abc.abstractmethod
    def insert_highscore(self, highscore: HighscoreStruct) -> None:
        """Insert a single highscore into the database."""
        logger.debug(
            "%s: Inserting highscore into DB: %s", type(self).__name__, highscore
        )

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
        :raise DBConnectionError:
            If executing the command fails due to loss of connection.
        """
        cursor = self.conn.cursor(**cursor_args)
        logger.debug(
            "%s: Executing command %r with params: %s", type(self).__name__, cmd, params
        )
        cursor.execute(cmd, params)
        if commit:
            self.conn.commit()
        return cursor


class _SQLMixin:
    """A mixin for SQL-like highscores databases."""

    _TABLE_NAME = "highscores"
    _CREATE_TABLE_SQL = dedent(
        f"""\
        CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
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

    def _get_select_highscores_sql(
        self,
        *,
        difficulty: Optional[str] = None,
        per_cell: Optional[int] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> str:
        """Get the SQL command to get/select highscores from a DB."""
        conditions = []
        if difficulty is not None:
            conditions.append(f"difficulty='{difficulty}'")
        if per_cell is not None:
            conditions.append(f"per_cell={per_cell}")
        if drag_select is not None:
            conditions.append(f"drag_select={drag_select:d}")
        if name is not None:
            conditions.append(f"name='{name}'")
        return "SELECT {} FROM highscores {} ORDER BY elapsed ASC".format(
            ", ".join(_highscore_fields),
            "WHERE " + " AND ".join(conditions) if conditions else "",
        )

    def _get_insert_highscore_sql(self, format="%s") -> str:
        """Get the SQL command to insert a highscore into a DB."""
        return "INSERT INTO highscores ({}) " "VALUES ({})".format(
            ", ".join(_highscore_fields), ", ".join(format for _ in _highscore_fields)
        )


class LocalHighscoresDB(_SQLMixin, AbstractHighscoresDB):
    """Database of local highscores."""

    _DB_FILE = ROOT_DIR / "data" / "highscores.db"

    def __init__(self):
        if os.path.exists(self._DB_FILE):
            self._conn = sqlite3.connect(str(self._DB_FILE))
        else:
            os.makedirs(self._DB_FILE.parent, exist_ok=True)
            self._conn = sqlite3.connect(str(self._DB_FILE))

            cursor = self._conn.cursor()
            cursor.execute(self._CREATE_TABLE_SQL)
        self._conn.row_factory = HighscoreStruct.from_sqlite_row

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def get_highscores(
        self,
        *,
        difficulty: Optional[str] = None,
        per_cell: Optional[int] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Iterable[HighscoreStruct]:
        super().get_highscores(
            difficulty=difficulty, per_cell=per_cell, drag_select=drag_select, name=name
        )
        cursor = self.execute(
            self._get_select_highscores_sql(
                difficulty=difficulty,
                per_cell=per_cell,
                drag_select=drag_select,
                name=name,
            )
        )
        return cursor.fetchall()

    def insert_highscore(self, highscore: HighscoreStruct) -> None:
        super().insert_highscore(highscore)
        self.execute(
            self._get_insert_highscore_sql(format="?"),
            attr.astuple(highscore),
            commit=True,
        )

    def execute(
        self, cmd: str, params: Tuple = (), *, commit=False, **cursor_args
    ) -> sqlite3.Cursor:
        return super().execute(cmd, params, commit=commit, **cursor_args)


class RemoteHighscoresDB(_SQLMixin, AbstractHighscoresDB):
    """Remote highscores database."""

    _USER = "admin"
    _PASSWORD = os.environ.get("SQL_DB_PASSWORD")
    _HOST = "minegauler-highscores.cb4tvkuqujyi.eu-west-2.rds.amazonaws.com"
    _DB_NAME = "minegauler"
    _TABLE_NAME = "highscores"

    _cached_conn: Optional[mysql.connector.MySQLConnection] = None

    def __init__(self):
        """
        :raise DBConnectionError:
            If connecting to the DB fails for any reason.
        """
        if not self._cached_conn:
            logger.info("Initialising connection to remote highscores DB")
            try:
                self._cached_conn = mysql.connector.connect(
                    user=self._USER,
                    password=self._PASSWORD,
                    host=self._HOST,
                    database=self._DB_NAME,
                )
            except mysql.connector.Error as e:
                raise DBConnectionError(
                    "Unable to connect to remote highscores database"
                ) from e
        self._conn = self._cached_conn

    @property
    def conn(self) -> mysql.connector.MySQLConnection:
        return self._conn

    def get_highscores(
        self,
        *,
        difficulty: Optional[str] = None,
        per_cell: Optional[int] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Iterable[HighscoreStruct]:
        super().get_highscores(
            difficulty=difficulty, per_cell=per_cell, drag_select=drag_select, name=name
        )
        cursor = self.execute(
            self._get_select_highscores_sql(
                difficulty=difficulty,
                per_cell=per_cell,
                drag_select=drag_select,
                name=name,
            ),
            dictionary=True,
        )
        return [HighscoreStruct(**r) for r in cursor.fetchall()]

    def insert_highscore(self, highscore: HighscoreStruct) -> None:
        super().insert_highscore(highscore)
        self.execute(
            self._get_insert_highscore_sql(), attr.astuple(highscore), commit=True
        )

    def execute(
        self, cmd: str, params: Tuple = (), *, commit=False, **cursor_args
    ) -> sqlite3.Cursor:
        try:
            return super().execute(cmd, params, commit=commit, **cursor_args)
        except mysql.connector.Error as e:
            raise DBConnectionError("Error occurred trying to execute command") from e


class HighscoresDatabases(enum.Enum):
    """An enum of highscores databases."""

    LOCAL = LocalHighscoresDB
    REMOTE = RemoteHighscoresDB

    def get_db_instance(self) -> AbstractHighscoresDB:
        return self.value()


def get_highscores(
    database=HighscoresDatabases.LOCAL,
    *,
    settings: Optional[HighscoreSettingsStruct] = None,
    difficulty: Optional[str] = None,
    per_cell: Optional[int] = None,
    drag_select: Optional[bool] = None,
    name: Optional[str] = None,
) -> Iterable[HighscoreStruct]:
    """
    Fetch highscores from a database.

    :param database:
        The database type to fetch from.
    :param settings:
        Optionally specify settings to filter by.
    :param difficulty:
        Optionally specify difficulty to filter by. Ignored if settings given.
    :param per_cell:
        Optionally specify per_cell to filter by. Ignored if settings given.
    :param drag_select:
        Optionally specify drag_select to filter by. Ignored if settings given.
    :param name:
        Optionally specify a name to filter by.
    """
    if settings is not None:
        difficulty = settings.difficulty
        per_cell = settings.per_cell
        drag_select = settings.drag_select
    return database.get_db_instance().get_highscores(
        difficulty=difficulty, per_cell=per_cell, drag_select=drag_select, name=name
    )


def insert_highscore(highscore: HighscoreStruct) -> None:
    """Insert a highscore into DBs."""
    LocalHighscoresDB().insert_highscore(highscore)

    def _post_catch_exc():
        try:
            _post_highscore_to_remote(highscore)
        except Exception:
            logger.exception("Failed to insert highscore into remote DB")

    threading.Thread(target=_post_catch_exc).start()


def filter_and_sort(
    highscores: Iterable[HighscoreStruct],
    sort_key: str = "time",
    filters: Dict[str, Optional[str]] = {},
) -> List[HighscoreStruct]:
    """
    Filter and sort an iterable of highscores.

    :param highscores:
        The iterable of highscores to filter and sort.
    :param sort_key:
        What to sort by.
    :param filters:
        What filters to apply.
    :return:
        A new iterable of highscores.
    """
    ret = []
    filters = {k: f for k, f in filters.items() if f}
    for hs in highscores:
        all_pass = True
        if "flagging" in filters:
            if (
                filters["flagging"] == "F"
                and not utils.is_flagging_threshold(hs.flagging)
                or filters["flagging"] == "NF"
                and utils.is_flagging_threshold(hs.flagging)
            ):
                all_pass = False
        if "name" in filters and filters["name"] != hs.name:
            all_pass = False
        if all_pass:
            # All filters satisfied.
            ret.append(hs)
    # Sort first by either time or 3bv/s, then by 3bv if there's a tie
    #  (higher 3bv higher for equal time, lower for equal 3bv/s).
    if sort_key == "time":
        ret.sort(key=lambda h: (h.elapsed, -h.bbbv))
    elif sort_key == "3bv/s":
        ret.sort(key=lambda h: (h.bbbvps, -h.bbbv), reverse=True)
    if "name" not in filters:
        # If no name filter, only include best highscore for each name.
        names = []
        i = 0
        while i < len(ret):
            hs = ret[i]
            name = hs["name"].lower()
            if name in names:
                ret.pop(i)
            else:
                names.append(name)
                i += 1
    return ret


def is_highscore_new_best(
    highscore: HighscoreStruct, all_highscores: Iterable[HighscoreStruct]
) -> Optional[str]:
    """
    Test to see if a new top highscore has been set.

    :param highscore:
        The highscore to check.
    :param all_highscores:
        The list of highscores to check against. May or may not include the
        highscore being checked.
    :return:
        If a new highscore was set, return which category it was set in. If not,
        return None.
    """
    all_highscores = list(all_highscores)
    top_time = filter_and_sort(all_highscores, "time", {"name": highscore.name})
    top_3bvps = filter_and_sort(all_highscores, "3bv/s", {"name": highscore.name})
    if not top_time or highscore.elapsed <= top_time[0].elapsed:
        return "time"
    elif not top_3bvps or highscore.bbbvps >= top_3bvps[0].bbbvps:
        return "3bv/s"
    else:
        return None


def _post_highscore_to_remote(highscore: HighscoreStruct):
    """Send a highscore to the remote server to be added to the remote DB."""
    logger.info("Posting highscore to remote")
    requests.post(_REMOTE_POST_URL, json=attr.asdict(highscore), timeout=5)
