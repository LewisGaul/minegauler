# February 2022, Lewis Gaul

"""
Compatibility with old highscore formats.

The submodule implementations are expected to never change, to maintain
compatibility with old versions of the app. For this reason there should also
be no dependency on the rest of the highscores package, which is free to evolve
alongside the app.

"""

__all__ = ("ConversionFunc", "HighscoreReadError", "read_highscores")

from collections.abc import Iterable
from pathlib import Path
from typing import Callable

from typing_extensions import TypeAlias

from ...shared.types import PathLike
from ..sqlite import SQLiteDB
from ..types import HighscoreStruct
from . import sqlite_v0, sqlite_v1, sqlite_v2, sqlite_v3


ConversionFunc: TypeAlias = Callable[[PathLike], Iterable[HighscoreStruct]]


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
    path = Path(path)
    if not path.is_file():
        raise HighscoreReadError(f"DB file not found: {path}")
    if path.suffix != ".db":
        raise HighscoreReadError(f"Unrecognised DB extension: {path.suffix}")

    with SQLiteDB(path) as db:
        db_version = db.get_version()
    func: ConversionFunc
    if db_version == 0:
        func = sqlite_v0.read_highscores
    elif db_version == 1:
        func = sqlite_v1.read_highscores
    elif db_version == 2:
        func = sqlite_v2.read_highscores
    elif db_version == 3:
        func = sqlite_v3.read_highscores
    else:
        raise HighscoreReadError(f"Unrecognised SQLite DB version: {db_version}")
    try:
        return func(path)
    except Exception as e:
        raise HighscoreReadError(f"Failed to read v{db_version} SQLite DB") from e
