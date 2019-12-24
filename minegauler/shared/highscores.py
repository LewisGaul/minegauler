"""
highscores.py - Highscores handling

December 2019, Felix Gaul
"""

import os
import sqlite3
from typing import Iterable

import attr

from minegauler import ROOT_DIR, core
from minegauler.utils import get_difficulty


@attr.attrs(auto_attribs=True)
class HighscoreStruct:
    """A single highscore."""

    timestamp: int
    difficulty: str
    per_cell: int
    elapsed: float
    bbbv: int
    bbbvps: float


_highscore_fields = [a.name for a in HighscoreStruct.__attrs_attrs__]


def init_db():
    db_file = ROOT_DIR / "data" / "highscores.db"
    os.makedirs(db_file.parent, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS highscores (
        id integer PRIMARY KEY,
        timestamp integer,
        difficulty text,
        per_cell integer,
        elapsed real NOT NULL,
        bbbv integer,
        bbbvps real
    );"""
    # TODO: add drag select
    cursor.execute(create_table_sql)

    return conn


def get_data(difficulty: str, per_cell: int) -> Iterable[HighscoreStruct]:
    conn = init_db()
    cursor = conn.cursor()
    query = (
        "SELECT {} "
        "FROM highscores "
        "WHERE difficulty = '{}' AND per_cell = {} "
        "ORDER BY elapsed DESC;"
    ).format(", ".join(_highscore_fields), difficulty, per_cell)
    result_list = cursor.execute(query).fetchall()
    return [HighscoreStruct(*result) for result in result_list]


def check_highscore(game: core.game.Game) -> None:
    # Row values.
    timestamp = int(game.start_time)
    difficulty = get_difficulty(game.mf.x_size, game.mf.y_size, game.mf.nr_mines)
    per_cell = game.mf.per_cell
    hs_time = game.get_elapsed()
    bbbv = game.mf.bbbv
    bbbvps = game.get_3bvps()
    # Insert into the DB.
    conn = init_db()
    cursor = conn.cursor()
    insert_sql = "INSERT INTO highscores ({}) " "VALUES ({});".format(
        ", ".join(_highscore_fields), ", ".join("?" for _ in _highscore_fields)
    )
    cursor.execute(insert_sql, (timestamp, difficulty, per_cell, hs_time, bbbv, bbbvps))

    conn.commit()

    print(cursor.execute("SELECT * FROM highscores;").fetchall())
