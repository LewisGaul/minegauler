# February 2022, Lewis Gaul

"""
Compatibility with v1 SQLite highscore format.

This version adds split-cell mode highscore support in v4.1.2 minegauler.

DB structure:
 - One table per game mode ('regular' and 'split_cell')
 - Columns:
   0. difficulty: str ("B", "I", "E", "M", "L")
   1. per_cell: int (1, 2, 3)
   2. drag_select: int (0, 1)
   3. name: str (max 20 characters)
   4. timestamp: int
   5. elapsed: float
   6. bbbv: int
   7. bbbvps: float
   8. flagging: float (in the range 0-1)

"""

__all__ = ("read_highscores",)

import sqlite3
from collections.abc import Iterable

from ...shared.types import PathLike, ReachSetting
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
                        reach=ReachSetting.NORMAL.value,
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
