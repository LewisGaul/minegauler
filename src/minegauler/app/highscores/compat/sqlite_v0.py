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

import contextlib
import sqlite3
from collections.abc import Iterable
from sqlite3 import Cursor, Row

from ...shared.types import GameMode, PathLike, ReachSetting
from ..types import HighscoreStruct


_TABLE_NAME = "highscores"


def highscore_row_factory(cursor: Cursor, row: Row) -> HighscoreStruct:
    row_dict = {col[0]: row[i] for i, col in enumerate(cursor.description)}
    row_dict["game_mode"] = GameMode.REGULAR.value
    row_dict["reach"] = ReachSetting.NORMAL.value
    return HighscoreStruct.from_flat_json(row_dict)


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    with contextlib.closing(sqlite3.connect(path)) as conn:
        cursor = conn.cursor()
        cursor.row_factory = highscore_row_factory
        cursor.execute(f"SELECT * FROM {_TABLE_NAME}")
        yield from cursor
