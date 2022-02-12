# February 2022, Lewis Gaul

"""
Compatibility with v1 SQLite highscore format.

This version adds split-cell mode highscore support in v4.1.2 minegauler.

"""

__all__ = ("read_highscores",)

import sqlite3
from typing import Iterable

from ...shared.types import PathLike
from ..base import HighscoreStruct


_TABLE_NAMES = ["regular", "split_cell"]


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    ret = set()
    with sqlite3.connect(str(path)) as conn:
        for table_name in _TABLE_NAMES:
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            for row in cursor:
                ret.add(
                    HighscoreStruct(
                        game_mode=table_name,
                        difficulty=row[0],
                        per_cell=row[1],
                        drag_select=row[2],
                        name=row[3],
                        timestamp=row[4],
                        elapsed=row[5],
                        bbbv=row[6],
                        bbbvps=row[7],
                        flagging=row[8],
                    )
                )
    return ret
