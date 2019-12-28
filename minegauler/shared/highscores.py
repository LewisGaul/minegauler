"""
highscores.py - Highscores handling

December 2019, Felix Gaul
"""

__all__ = (
    "HighscoreSettingsStruct",
    "HighscoreStruct",
    "get_highscores",
    "insert_highscore",
)

import logging
import os
import sqlite3
from typing import Dict, Iterable, Optional, Tuple

import attr

from .. import ROOT_DIR
from ..utils import StructConstructorMixin
from . import utils


logger = logging.getLogger(__name__)

_DB_FILE = ROOT_DIR / "data" / "highscores.db"


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
    def from_sql_row(cls, cursor: sqlite3.Cursor, row: Tuple) -> "HighscoreStruct":
        """Create an instance from an SQL row."""
        return cls(**{col[0]: row[i] for i, col in enumerate(cursor.description)})


_highscore_fields = attr.fields_dict(HighscoreStruct).keys()


def _init_db() -> sqlite3.Connection:
    """
    Initialise the SQL database.

    :return:
        An open connection to the database.
    """
    if os.path.exists(_DB_FILE):
        conn = sqlite3.connect(str(_DB_FILE))
    else:
        os.makedirs(_DB_FILE.parent, exist_ok=True)
        conn = sqlite3.connect(str(_DB_FILE))
        cursor = conn.cursor()

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS highscores (
            id INTEGER PRIMARY KEY,
            difficulty TEXT,
            per_cell INTEGER,
            drag_select INTEGER,
            name TEXT,
            timestamp INTEGER,
            elapsed REAL NOT NULL,
            bbbv INTEGER,
            bbbvps REAL,
            flagging REAL
        )"""
        cursor.execute(create_table_sql)

    return conn


def get_highscores(settings: HighscoreSettingsStruct) -> Iterable[HighscoreStruct]:
    """Fetch highscores from the database."""
    conn = _init_db()
    conn.row_factory = HighscoreStruct.from_sql_row
    cursor = conn.cursor()
    query = (
        "SELECT {} "
        "FROM highscores "
        "WHERE difficulty='{}' AND per_cell={} AND drag_select={:d} "
        "ORDER BY elapsed DESC"
    ).format(
        ", ".join(_highscore_fields),
        settings.difficulty.upper(),
        settings.per_cell,
        settings.drag_select,
    )
    logger.debug("Getting highscores with SQL query: %r", query)
    return cursor.execute(query).fetchall()


def filter_and_sort(
    highscores: Iterable[HighscoreStruct],
    sort_key: str,
    filters: Dict[str, Optional[str]],
) -> Iterable[HighscoreStruct]:
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


def insert_highscore(highscore: HighscoreStruct) -> None:
    # Insert into the DB.
    conn = _init_db()
    cursor = conn.cursor()
    insert_sql = "INSERT INTO highscores ({}) " "VALUES ({})".format(
        ", ".join(_highscore_fields), ", ".join(f":{f}" for f in _highscore_fields)
    )
    logger.info(
        "Inserting highscore into DB: (%d, %s, %d, %s, %s, %.2f, %d, %.2f, %.2f)",
        highscore.timestamp,
        highscore.difficulty,
        highscore.per_cell,
        highscore.drag_select,
        highscore.name,
        highscore.elapsed,
        highscore.bbbv,
        highscore.bbbvps,
        highscore.flagging,
    )
    cursor.execute(
        insert_sql,
        {
            "timestamp": highscore.timestamp,
            "difficulty": highscore.difficulty,
            "per_cell": highscore.per_cell,
            "drag_select": int(highscore.drag_select),
            "name": highscore.name,
            "elapsed": highscore.elapsed,
            "bbbv": highscore.bbbv,
            "bbbvps": highscore.bbbvps,
            "flagging": highscore.flagging,
        },
    )
    conn.commit()


def is_highscore_new_best(highscore: HighscoreStruct) -> Optional[str]:
    """
    Test to see if a new top highscore has been set.

    :param highscore:
        The highscore to check.
    :return:
        If a new highscore was set, return which category it was set in. If not, return None.
    """

    highscore_list = get_highscores(highscore)
    top_time = filter_and_sort(highscore_list, "time", {"name": highscore.name})
    top_3bvps = filter_and_sort(highscore_list, "3bv/s", {"name": highscore.name})
    if highscore.elapsed <= top_time[0].elapsed:
        return "time"
    elif highscore.bbbvps >= top_3bvps[0].bbbvps:
        return "3bv/s"
    else:
        return None
