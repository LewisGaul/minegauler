# February 2020, Lewis Gaul

"""
Bot utilities.

"""

__all__ = (
    "USER_NAMES",
    "Matchup",
    "PlayerInfo",
    "get_highscores",
    "get_matchups",
    "get_highscore_times",
    "get_player_info",
    "set_user_nickname",
)

import collections
import json
import logging
import os
import pathlib
import sys
from typing import Iterable, List, Optional, Tuple

import requests

from minegauler.app import highscores as hs
from minegauler.app.shared.types import Difficulty, GameMode, ReachSetting


logger = logging.getLogger(__name__)


USER_NAMES = dict()
if hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS"):  # in pyinstaller EXE
    _USER_NAMES_FILE = pathlib.Path(__file__).parents[2] / "bot/users.json"
    os.makedirs(_USER_NAMES_FILE.parent, exist_ok=True)
else:
    _USER_NAMES_FILE = pathlib.Path(__file__).parent / "users.json"

_API_BASEURL = "http://minegauler.lewisgaul.co.uk/api/v1/highscores"


# ------------------------------------------------------------------------------
# External
# ------------------------------------------------------------------------------


def read_users_file():
    global USER_NAMES
    try:
        with open(_USER_NAMES_FILE) as f:
            USER_NAMES = json.load(f)
    except FileNotFoundError:
        logger.info("%s file not found", _USER_NAMES_FILE)


def save_users_file():
    with open(_USER_NAMES_FILE, "w") as f:
        json.dump(USER_NAMES, f)


def set_user_nickname(user: str, nickname: str) -> None:
    USER_NAMES[user] = nickname
    save_users_file()


def get_highscore_times(
    difficulty: Optional[Difficulty],
    *,
    game_mode: GameMode = GameMode.REGULAR,
    drag_select: Optional[bool] = None,
    per_cell: Optional[int] = None,
    reach: Optional[ReachSetting] = None,
    users: Optional[Iterable[str]] = None,
) -> List[Tuple[str, float]]:
    if difficulty is Difficulty.CUSTOM:
        raise ValueError("No highscores for custom difficulty")
    if users is None:
        users = USER_NAMES.values()
    lower_users = {u.lower(): u for u in users}

    if difficulty:
        highscores = hs.filter_and_sort(
            get_highscores(
                game_mode=game_mode,
                difficulty=difficulty,
                drag_select=drag_select,
                per_cell=per_cell,
                reach=reach,
            )
        )
        times = {
            lower_users[h.name.lower()]: h.elapsed
            for h in highscores
            if h.name.lower() in lower_users
        }
    else:
        times = {
            u: _get_combined_highscore(
                u,
                game_mode=game_mode,
                drag_select=drag_select,
                per_cell=per_cell,
                reach=reach,
            )
            for u in users
        }

    return sorted(times.items(), key=lambda x: x[1])


Matchup = collections.namedtuple("Matchup", "user1, time1, user2, time2, percent")


def get_matchups(
    times: Iterable[Tuple[str, float]], include_users: Optional[Iterable[str]] = None
) -> List[Matchup]:
    times = sorted(times, key=lambda x: x[1], reverse=True)
    matchups = set()
    while times:
        # Avoid repeating matchups or comparing users against themselves.
        user1, time1 = times.pop()
        for user2, time2 in times:
            if (
                include_users
                and user1 not in include_users
                and user2 not in include_users
            ):
                continue
            assert time2 >= time1
            percent = 100 * (time2 - time1) / time1
            matchups.add(Matchup(user1, time1, user2, time2, percent))

    return sorted(matchups, key=lambda x: x.percent)


PlayerInfo = collections.namedtuple(
    "PlayerInfo", "username, nickname, combined_time, types_beaten, last_highscore"
)


def get_player_info(username: str) -> PlayerInfo:
    name = USER_NAMES[username]
    highscores = [h for m in GameMode for h in get_highscores(game_mode=m, name=name)]
    combined_time = _get_combined_highscore(name)
    last_highscore = max(h.timestamp for h in highscores) if highscores else None
    hs_types = len(
        {
            (h.game_mode, h.difficulty.lower(), h.drag_select, h.per_cell, h.reach)
            for h in highscores
        }
    )
    return PlayerInfo(username, name, combined_time, hs_types, last_highscore)


def get_highscores(
    *,
    settings: Optional[hs.HighscoreSettingsStruct] = None,
    game_mode: GameMode = GameMode.REGULAR,
    difficulty: Optional[Difficulty] = None,
    per_cell: Optional[int] = None,
    reach: Optional[ReachSetting] = None,
    drag_select: Optional[bool] = None,
    name: Optional[str] = None,
) -> Iterable[hs.HighscoreStruct]:
    """
    Get highscores using the REST API.

    :param settings:
        Highscore filter to apply.
    :param game_mode:
        The game mode to get highscores for. Ignored if settings given.
    :param difficulty:
        Optionally specify difficulty to filter by. Ignored if settings given.
    :param per_cell:
        Optionally specify per-cell to filter by. Ignored if settings given.
    :param reach:
        Optionally specify reach to filter by. Ignored if settings given.
    :param drag_select:
        Optionally specify drag-select to filter by. Ignored if settings given.
    :param name:
        Optionally specify a name to filter by.
    :raises Exception:
        If the HTTP request fails or returns bad data.
    :return:
        Matching highscores.
    """
    if settings is not None:
        game_mode = settings.game_mode
        difficulty = settings.difficulty
        per_cell = settings.per_cell
        reach = settings.reach
        drag_select = settings.drag_select
    args = [f"game_mode={game_mode.name.lower()}"]
    if difficulty is not None:
        args.append(f"difficulty={difficulty.name[0]}")
    if per_cell is not None:
        args.append(f"per_cell={per_cell}")
    if reach is not None:
        args.append(f"reach={int(reach)}")
    if drag_select is not None:
        args.append(f"drag_select={int(drag_select)}")
    if name is not None:
        args.append(f"name={name}")
    url = _API_BASEURL + "?" + "&".join(args)
    response = requests.get(url)
    return [hs.HighscoreStruct.from_dict(h) for h in response.json()]


# ------------------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------------------


def _get_combined_highscore(
    name: str,
    *,
    game_mode: GameMode = GameMode.REGULAR,
    per_cell: Optional[int] = None,
    reach: Optional[ReachSetting] = None,
    drag_select: Optional[bool] = None,
) -> float:
    total = 0
    for diff in ["b", "i", "e"]:
        all_highscores = get_highscores(
            game_mode=game_mode,
            name=name,
            drag_select=drag_select,
            per_cell=per_cell,
            reach=reach,
        )
        highscores = [h.elapsed for h in all_highscores if h.difficulty.lower() == diff]
        total += min(highscores) if highscores else 1000
    return total
