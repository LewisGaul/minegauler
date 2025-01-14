# January 2025, Lewis Gaul

"""
Compatibility with v3 SQLite highscore format.

This version changes the following:
 - Combine game modes (regular and split-cell) into a single table
 - Remove 'bbbvps' field, since this can be computed from bbbv and elapsed

DB structure:
 - One table containing all highscores
 - Columns:
   0. game_mode: str ("regular", "split-cell")
   1. difficulty: str ("B", "I", "E", "M", "L")
   2. per_cell: int (1, 2, 3)
   3. reach: int (4, 8, 24)
   4. drag_select: int (0, 1)
   5. name: str (max 20 characters)
   6. timestamp: int
   7. elapsed: float
   8. bbbv: int
   9. flagging: float (in the range 0-1)

"""

__all__ = ("read_highscores",)

import sqlite3
from collections.abc import Iterable

from ...shared.types import PathLike
from ..types import HighscoreStruct


_TABLE_NAME = "highscores"


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(f"SELECT * FROM {_TABLE_NAME}")
        for row in cursor:
            yield HighscoreStruct(
                game_mode=row[0],
                difficulty=row[1],
                per_cell=row[2],
                reach=row[3],
                drag_select=row[4],
                name=row[5],
                timestamp=row[6],
                elapsed=row[7],
                bbbv=row[8],
                flagging=row[9],
            )
