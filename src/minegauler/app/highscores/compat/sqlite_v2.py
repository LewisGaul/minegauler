# February 2022, Lewis Gaul

"""
Compatibility with v1 SQLite highscore format.

This version adds the 'reach' setting highscore support in v4.2.0 minegauler.

"""

__all__ = ("read_highscores",)

import sqlite3
from collections.abc import Iterable

from ...shared.types import PathLike
from ..base import HighscoreStruct


_TABLE_NAMES = ["regular", "split_cell"]


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    ret = set()
    with sqlite3.connect(path) as conn:
        for table_name in _TABLE_NAMES:
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            for row in cursor:
                ret.add(
                    HighscoreStruct(
                        game_mode=table_name,
                        difficulty=row[0],
                        per_cell=row[1],
                        reach=row[2],
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
