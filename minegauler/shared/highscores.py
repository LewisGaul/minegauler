"""
highscores.py - Highscores handling

December 2019, Felix Gaul
"""

__all__ = (
    "HighscoreSettingsStruct",
    "HighscoreStruct",
    "check_highscore",
    "get_highscores",
)

import os
import sqlite3
from typing import Iterable, Tuple

import attr

from .. import ROOT_DIR, utils


@attr.attrs(auto_attribs=True)
class HighscoreSettingsStruct:
    """A set of highscore settings."""

    difficulty: str
    per_cell: int
    # TODO: add 'drag_select: bool'
    # TODO: add 'name: str'

    def __getitem__(self, item):
        return getattr(self, item)


@attr.attrs(auto_attribs=True)
class HighscoreStruct(HighscoreSettingsStruct):
    """A single highscore."""

    timestamp: int
    elapsed: float
    bbbv: int
    bbbvps: float
    # TODO: add 'flagging: float' (% cells flagged)

    @classmethod
    def from_sql_row(cls, cursor: sqlite3.Cursor, row: Tuple) -> "HighscoreStruct":
        """Create an instance from an SQL row."""
        return cls(**{col[0]: row[i] for i, col in enumerate(cursor.description)})

    @classmethod
    def from_iterable(cls, container: Iterable) -> "HighscoreStruct":
        """Create an instance from an iterable."""
        return cls(*container)


_highscore_fields = attr.fields_dict(HighscoreStruct).keys()


def _init_db():
    db_file = ROOT_DIR / "data" / "highscores.db"
    os.makedirs(db_file.parent, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS highscores (
        id INTEGER PRIMARY KEY,
        difficulty TEXT,
        per_cell INTEGER,
        timestamp INTEGER,
        elapsed REAL NOT NULL,
        bbbv INTEGER,
        bbbvps REAL
    )"""
    cursor.execute(create_table_sql)

    return conn


def get_highscores(settings: HighscoreSettingsStruct) -> Iterable[HighscoreStruct]:
    conn = _init_db()
    conn.row_factory = HighscoreStruct.from_sql_row
    cursor = conn.cursor()
    query = (
        "SELECT {} "
        "FROM highscores "
        "WHERE difficulty='{}' AND per_cell={} "
        "ORDER BY elapsed DESC"
    ).format(
        ", ".join(_highscore_fields), settings.difficulty.upper(), settings.per_cell
    )
    return cursor.execute(query).fetchall()


def check_highscore(game: "core.game.Game") -> None:
    # Row values.
    timestamp = int(game.start_time)
    difficulty = utils.get_difficulty(game.mf.x_size, game.mf.y_size, game.mf.nr_mines)
    per_cell = game.mf.per_cell
    hs_time = game.get_elapsed()
    bbbv = game.mf.bbbv
    bbbvps = game.get_3bvps()
    # Insert into the DB.
    conn = _init_db()
    cursor = conn.cursor()
    insert_sql = "INSERT INTO highscores ({}) " "VALUES ({})".format(
        ", ".join(_highscore_fields), ", ".join(f":{f}" for f in _highscore_fields)
    )
    cursor.execute(
        insert_sql,
        {
            "timestamp": timestamp,
            "difficulty": difficulty.upper(),
            "per_cell": per_cell,
            # "name": "",
            "elapsed": hs_time,
            "bbbv": bbbv,
            "bbbvps": bbbvps,
        },
    )

    conn.commit()

    print(cursor.execute("SELECT * FROM highscores").fetchall())
