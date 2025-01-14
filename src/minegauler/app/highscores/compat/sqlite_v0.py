# February 2022, Lewis Gaul

"""
Compatibility with v0 SQLite highscore format.

This is the initial SQLite format that comes with v4.0 minegauler.

DB structure:
 - One table containing all highscores
 - Columns:
   0. index (ignore)
   1. difficulty: str ("B", "I", "E", "M", "L")
   2. per_cell: int (1, 2, 3)
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

from ...shared.types import GameMode, PathLike, ReachSetting
from ..types import HighscoreStruct


_TABLE_NAME = "highscores"


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    ret = set()
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(f"SELECT * FROM {_TABLE_NAME}")
        for row in cursor:
            # First row entry is 'index' (ignore).
            ret.add(
                HighscoreStruct(
                    game_mode=GameMode.REGULAR.value,  # only mode supported
                    difficulty=row[1],
                    per_cell=row[2],
                    reach=ReachSetting.NORMAL.value,  # only mode supported
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
