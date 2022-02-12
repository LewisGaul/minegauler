# February 2022, Lewis Gaul

"""
Compatibility with v0 SQLite highscore format.

This is the initial SQLite format that comes with v4.0 minegauler.

"""

__all__ = ("read_highscores",)

import sqlite3
from typing import Iterable

from ...shared.types import PathLike
from ..base import HighscoreStruct


_TABLE_NAME = "highscores"


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    ret = set()
    with sqlite3.connect(str(path)) as conn:
        cursor = conn.execute(f"SELECT * FROM {_TABLE_NAME}")
        for row in cursor:
            # First row entry is 'index' (ignore).
            ret.add(
                HighscoreStruct(
                    game_mode="regular",  # only mode supported
                    difficulty=row[1],
                    per_cell=row[2],
                    drag_select=row[3],
                    name=row[4],
                    timestamp=row[5],
                    elapsed=row[6],
                    bbbv=row[7],
                    bbbvps=row[8],
                    flagging=row[9],
                )
            )
    return ret
