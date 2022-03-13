# February 2022, Lewis Gaul

"""
Highscores handling.

"""

__all__ = (
    "HighscoreReadError",
    "HighscoreSettingsStruct",
    "HighscoreStruct",
    "SQLiteDB",
    "filter_and_sort",
    "get_highscores",
    "insert_highscore",
    "is_highscore_new_best",
)

import logging
import threading
from typing import Dict, Iterable, List, Optional

import attr
import requests

from .. import paths
from .._version import __version__
from ..shared import utils
from ..shared.types import Difficulty, GameMode, PathLike
from . import compat
from .base import AbstractHighscoresDB, HighscoreSettingsStruct, HighscoreStruct
from .compat import HighscoreReadError
# from .mysql import MySQLDB  # Do not uncomment this without adding dependency on mysql connector
from .sqlite import SQLiteDB


logger = logging.getLogger(__name__)

_REMOTE_POST_URL = "http://minegauler.lewisgaul.co.uk/api/v1/highscore"

_default_local_db = SQLiteDB(paths.HIGHSCORES_FILE)


def get_highscores(
    *,
    database: Optional[AbstractHighscoresDB] = None,
    settings: Optional[HighscoreSettingsStruct] = None,
    game_mode: Optional[GameMode] = None,
    difficulty: Optional[Difficulty] = None,
    per_cell: Optional[int] = None,
    drag_select: Optional[bool] = None,
    name: Optional[str] = None,
) -> Iterable[HighscoreStruct]:
    """
    Fetch highscores from a database.

    :param database:
        The database to fetch from, defaults to the local highscores DB.
    :param settings:
        Optionally specify settings to filter by.
    :param game_mode:
        Optionally specify game mode to filter by. Ignored if settings given.
    :param difficulty:
        Optionally specify difficulty to filter by. Ignored if settings given.
    :param per_cell:
        Optionally specify per-cell to filter by. Ignored if settings given.
    :param drag_select:
        Optionally specify drag-select to filter by. Ignored if settings given.
    :param name:
        Optionally specify a name to filter by.
    """
    if database is None:
        database = _default_local_db
    if settings is not None:
        game_mode = settings.game_mode
        difficulty = settings.difficulty
        per_cell = settings.per_cell
        drag_select = settings.drag_select
    return database.get_highscores(
        game_mode=game_mode,
        difficulty=difficulty,
        per_cell=per_cell,
        drag_select=drag_select,
        name=name,
    )


def insert_highscore(
    highscore: HighscoreStruct,
    *,
    database: Optional[AbstractHighscoresDB] = None,
    post_remote: bool = True,
) -> None:
    """
    Insert a highscore into a database.

    :param highscore:
        The highscore to insert.
    :param database:
        The database to insert into, defaults to the local highscores DB.
    :param post_remote:
        Whether to post the highscore to the remote master DB.
    """
    if database is None:
        database = _default_local_db
    database.insert_highscores([highscore])

    if post_remote:

        def _post_catch_exc():
            try:
                _post_highscore_to_remote(highscore)
            except Exception:
                logger.exception("Failed to insert highscore into remote DB")

        threading.Thread(target=_post_catch_exc).start()


def retrieve_highscores(path: PathLike) -> int:
    """
    Insert highscores from another DB at the given path.

    Handles reading in older highscore formats.

    :param path:
        Path to highscores, may be file or directory as required.
    :return:
        Number of inserted highscores.
    :raise HighscoreReadError:
        If unable to read highscores from the given path.
    """
    return _default_local_db.insert_highscores(compat.read_highscores(path))


def filter_and_sort(
    highscores: Iterable[HighscoreStruct],
    sort_key: str = "time",
    filters: Dict[str, Optional[str]] = {},
) -> List[HighscoreStruct]:
    """
    Filter and sort an iterable of highscores.

    :param highscores:
        The iterable of highscores to filter and sort.
    :param sort_key:
        What to sort by.
    :param filters:
        What filters to apply.
    :return:
        A new list of highscores.
    """
    # TODO: Generalise/tidy up...
    ret = []
    filters = {k: f for k, f in filters.items() if f}
    for hs in highscores:
        all_pass = True
        if "flagging" in filters:
            if (
                filters["flagging"] == "F"
                and not utils.is_flagging_threshold(hs.flagging)
                or filters["flagging"] == "NF"
                and utils.is_flagging_threshold(hs.flagging)
            ):
                all_pass = False
        if "name" in filters and filters["name"].lower() != hs.name.lower():
            all_pass = False
        if all_pass:
            # All filters satisfied.
            ret.append(hs)
    # Sort first by either time or 3bv/s, then by 3bv if there's a tie
    #  (higher 3bv higher for equal time, lower for equal 3bv/s).
    if sort_key == "time":
        ret.sort(key=lambda h: (h.elapsed, -h.bbbv))
    elif sort_key == "3bv/s":
        ret.sort(key=lambda h: (h.bbbvps, -h.bbbv), reverse=True)
    if "name" not in filters:
        # If no name filter, only include best highscore for each name.
        names = []
        i = 0
        while i < len(ret):
            hs = ret[i]
            name = hs.name.lower()
            if name in names:
                ret.pop(i)
            else:
                names.append(name)
                i += 1
    return ret


def is_highscore_new_best(
    highscore: HighscoreStruct, all_highscores: Iterable[HighscoreStruct]
) -> Optional[str]:
    """
    Test to see if a new top highscore has been set.

    :param highscore:
        The highscore to check.
    :param all_highscores:
        The list of highscores to check against. May or may not include the
        highscore being checked.
    :return:
        If a new highscore was set, return which category it was set in. If not,
        return None.
    """
    all_highscores = list(all_highscores)
    top_time = filter_and_sort(all_highscores, "time", {"name": highscore.name})
    top_3bvps = filter_and_sort(all_highscores, "3bv/s", {"name": highscore.name})
    if not top_time or highscore.elapsed <= top_time[0].elapsed:
        return "time"
    elif not top_3bvps or highscore.bbbvps >= top_3bvps[0].bbbvps:
        return "3bv/s"
    else:
        return None


def _post_highscore_to_remote(highscore: HighscoreStruct):
    """Send a highscore to the remote server to be added to the remote DB."""
    logger.info("Posting highscore to remote")
    requests.post(
        _REMOTE_POST_URL,
        json={
            "highscore": attr.asdict(highscore),
            "app_version": __version__,
        },
        timeout=5,
    )
