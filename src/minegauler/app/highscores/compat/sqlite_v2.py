# February 2022, Lewis Gaul

"""
Compatibility with v2 SQLite highscore format.

This version adds the 'reach' setting highscore support in v4.2.0 minegauler.

DB structure:
 - One table per game mode ('regular' and 'split_cell')
 - Columns:
   0. difficulty: str ("B", "I", "E", "M", "L")
   1. per_cell: int (1, 2, 3)
   2. reach: int (4, 8, 24)
   3. drag_select: int (0, 1)
   4. name: str (max 20 characters)
   5. timestamp: int
   6. elapsed: float
   7. bbbv: int
   8. bbbvps: float
   9. flagging: float (in the range 0-1)

"""

__all__ = ("read_highscores",)

import sqlite3
from collections.abc import Iterable

from ...shared.types import PathLike
from ..types import HighscoreStruct


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
