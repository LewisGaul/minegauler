# February 2022, Lewis Gaul

"""
Compatibility with old highscore formats.

The submodule implementations are expected to never change, to maintain
compatibility with old versions of the app. For this reason there should also
be no dependency on the rest of the highscores package, which is free to evolve
alongside the app.

"""

__all__ = ("ConversionFunc", "HighscoreReadError", "read_highscores")

import pathlib
import sqlite3
from typing import Callable, Iterable

from ...shared.types import PathLike
from ..base import HighscoreStruct
from . import sqlite_v0, sqlite_v1


ConversionFunc = Callable[[PathLike], Iterable[HighscoreStruct]]


class HighscoreReadError(Exception):
    pass


def read_highscores(path: PathLike) -> Iterable[HighscoreStruct]:
    """
    Read highscores from the given path.

    Delegates to the appropriate submodule's implementation for older versions.

    :param path:
        Path to highscores, may be file or directory as required.
    :return:
        Iterable of retrieved highscores.
    :raise HighscoreReadError:
        If unable to read highscores from the given path.
    """
    path = pathlib.Path(path)
    if (path / "data" / "highscores.db").is_file():
        path = path / "data" / "highscores.db"
    elif (path / "highscores.db").is_file():
        path = path / "highscores.db"

    if path.suffix == ".db":
        with sqlite3.connect(str(path)) as conn:
            sqlite_db_version = next(conn.execute("PRAGMA user_version"))[0]
        func: ConversionFunc
        if sqlite_db_version == 0:
            func = sqlite_v0.read_highscores
        elif sqlite_db_version == 1:
            func = sqlite_v1.read_highscores
        else:
            raise HighscoreReadError(
                f"Unrecognised SQLite DB version '{sqlite_db_version}'"
            )
        try:
            return func(path)
        except Exception as e:
            raise HighscoreReadError(
                f"Failed to read v{sqlite_db_version} SQLite DB"
            ) from e
    else:
        raise HighscoreReadError(f"Unrecognised DB extension '{path.suffix}'")
