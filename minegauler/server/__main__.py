# January 2020, Lewis Gaul

"""
Server entry-point.

"""

import argparse
import logging
import os
import re
import sys
from typing import Dict, Optional

import attr
import bot
from flask import Flask, abort, jsonify, redirect, request

from minegauler.app.shared.types import Difficulty, GameMode

from . import get_new_highscore_hooks


logger = logging.getLogger(__name__)

app = Flask(__name__)

SQLITE_DB_PATH = "/home/pi/.local/var/lib/minegauler-highscores.db"


# ------------------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------------------


@app.route("/api/v1/highscore", methods=["POST"])
def api_v1_highscore():
    """
    Notification of a new highscore being set.

    Perform any desired handling for each highscore (e.g. usage logging), and
    also perform special handling for new records (e.g. add to the remote DB).
    """
    try:
        highscore = get_highscore_from_json(request.get_json())
    except Exception:
        logger.debug(
            "Unrecognised highscore posted: %s", request.get_json(), exc_info=True
        )
        return "Unrecognised highscore", 400
    else:
        logger.debug("POST highscore: %s", highscore)

    new_best = is_highscore_new_best(highscore)
    if new_best is None:
        logger.debug("Not a new best, ignoring the highscore")
        return "", 200

    try:
        hs.SQLiteDB(SQLITE_DB_PATH).insert_highscores([highscore])
    except Exception as e:
        logger.exception("Failed to insert highscore into remote DB")
        # TODO: I want to know if this is hit!
        return str(e), 503

    for func in get_new_highscore_hooks():
        try:
            func(highscore)
        except BaseException:
            logger.exception(f"Error in 'new highscore' hook {func.__name__}()")

    return "", 200


@app.route("/api/v1/highscores", methods=["GET"])
def api_v1_highscores():
    """Provide a REST API to get highscores from the DB."""
    logger.debug("GET highscores with args: %s", dict(request.args))
    kwargs = {}
    game_mode = request.args.get("game_mode")
    if game_mode:
        kwargs["game_mode"] = GameMode.from_str(game_mode)
    difficulty = request.args.get("difficulty")
    if difficulty:
        kwargs["difficulty"] = Difficulty.from_str(difficulty)
    per_cell = request.args.get("per_cell")
    if per_cell:
        kwargs["per_cell"] = int(per_cell)
    drag_select = request.args.get("drag_select")
    if drag_select:
        kwargs["drag_select"] = bool(int(drag_select))
    kwargs["name"] = request.args.get("name")
    return jsonify(
        [
            attr.asdict(h)
            for h in hs.get_highscores(database=hs.SQLiteDB(SQLITE_DB_PATH), **kwargs)
        ]
    )


@app.route("/api/v1/highscores/ranks", methods=["GET"])
def api_v1_highscores_ranks():
    """Provide a REST API to get highscores from the DB."""
    logger.debug("GET highscores with args: %s", dict(request.args))
    game_mode = request.args.get("game_mode", "regular")
    difficulty = request.args.get("difficulty")
    per_cell = request.args.get("per_cell")
    drag_select = request.args.get("drag_select")
    if not difficulty or not per_cell or not drag_select:
        abort(404)
    game_mode = GameMode.from_str(game_mode)
    difficulty = Difficulty.from_str(difficulty)
    per_cell = int(per_cell)
    drag_select = bool(int(drag_select))
    return jsonify(
        [
            attr.asdict(h)
            for h in hs.filter_and_sort(
                hs.get_highscores(
                    database=hs.SQLiteDB(SQLITE_DB_PATH),
                    game_mode=game_mode,
                    difficulty=difficulty,
                    per_cell=per_cell,
                    drag_select=drag_select,
                )
            )
        ]
    )


# ------------------------------------------------------------------------------
# Webpage serving
# ------------------------------------------------------------------------------


@app.route("/")
def index():
    return redirect("https://www.lewisgaul.co.uk/minegauler", 302)


@app.route("/highscores")
def highscores():
    return api_v1_highscores()


# ------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------


def is_highscore_new_best(h: hs.HighscoreStruct) -> Optional[str]:
    all_highscores = hs.get_highscores(database=hs.SQLiteDB(SQLITE_DB_PATH), settings=h)
    return hs.is_highscore_new_best(h, all_highscores)


def get_highscore_from_json(obj: Dict) -> hs.HighscoreStruct:
    # Accept pre v4.1.2 versions that only contain the highscore.
    if "app_version" not in obj:
        logger.debug("Parsing highscore from pre-v4.1.2 app")
        obj["game_mode"] = "regular"
        highscore = hs.HighscoreStruct(**obj)
    else:
        app_version = obj["app_version"].lstrip("v")
        logger.debug("Parsing highscore from app v%s", app_version)
        stripped_version = re.sub(r"((?:\d+\.)+\d+)-?[a-zA-Z].+", r"\1", app_version)
        version_tuple = tuple(int(x) for x in stripped_version.split("."))
        if version_tuple < (4, 1, 2):
            raise ValueError(
                f"Expected app v4.1.2+ with 'app_version' field, got {app_version!r}"
            )
        highscore = hs.HighscoreStruct(**obj["highscore"])
    return highscore


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, help="Override the default port")
    parser.add_argument("--bot", action="store_true", help="Handle bot messages")
    parser.add_argument("--log-path", default="./server.log", help="Path to log file")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    return parser.parse_args(argv)


def main(argv):
    args = _parse_args(argv)

    logging.basicConfig(
        filename=args.log_path,
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )

    if args.bot:
        bot.routes.init_route_handling(app)

    logger.info("Starting up")
    if args.dev:
        os.environ["FLASK_ENV"] = "development"
        app.run(debug=True, port=args.port)
    else:
        from waitress import serve

        serve(app, port=args.port if args.port else 80)


if __name__ == "__main__":
    main(sys.argv[1:])
