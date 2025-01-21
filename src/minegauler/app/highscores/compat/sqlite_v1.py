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
from sqlite3 import Cursor, Row
from typing import Callable

import attrs

from ...shared.types import PathLike, ReachSetting
from ..types import HighscoreSettings, HighscoreStruct


_TABLE_NAMES = ["regular", "split_cell"]


def get_highscore_row_factory(
    game_mode: str,
) -> Callable[[Cursor, Row], HighscoreStruct]:

    setting_fields = attrs.fields_dict(HighscoreSettings).keys()
    entry_fields = attrs.fields_dict(HighscoreStruct).keys()

    def highscore_row_factory(cursor: Cursor, row: Row) -> HighscoreStruct:
        row_dict = {col[0]: row[i] for i, col in enumerate(cursor.description)}
        row_dict["game_mode"] = game_mode
        row_dict["reach"] = ReachSetting.NORMAL.value
        return HighscoreStruct(
            settings=HighscoreSettings(**{f: row_dict[f] for f in setting_fields}),
            **{f: row_dict[f] for f in entry_fields if f not in ("settings")},
        )

    return highscore_row_factory


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    ret = set()
    with sqlite3.connect(path) as conn:
        for table_name in _TABLE_NAMES:
            cursor = conn.cursor()
            cursor.row_factory = get_highscore_row_factory(table_name)
            cursor.execute(f"SELECT * FROM {table_name}")
            ret.update(cursor)
    return ret
