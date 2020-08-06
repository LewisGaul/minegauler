# January 2020, Lewis Gaul

"""
Server entry-point.

"""

import argparse
import logging
import os
import sys

import attr
from flask import Flask, abort, jsonify, redirect, request

import bot
from minegauler.shared import highscores as hs
from minegauler.shared.types import Difficulty
from server.utils import is_highscore_new_best

from . import get_new_highscore_hooks


logger = logging.getLogger(__name__)

app = Flask(__name__)


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
    data = request.get_json()
    # verify_highscore(data)  TODO
    highscore = hs.HighscoreStruct.from_dict(data)
    logger.debug("POST highscore: %s", highscore)

    new_best = is_highscore_new_best(highscore)
    if new_best is None:
        logger.debug("Not a new best, ignoring the highscore")
        return "", 200

    try:
        hs.RemoteHighscoresDB().insert_highscore(highscore)
    except hs.DBConnectionError as e:
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
    difficulty = request.args.get("difficulty")
    if difficulty:
        difficulty = Difficulty.from_str(difficulty)
    per_cell = request.args.get("per_cell")
    if per_cell:
        per_cell = int(per_cell)
    drag_select = request.args.get("drag_select")
    if drag_select:
        drag_select = bool(int(drag_select))
    name = request.args.get("name")
    return jsonify(
        [
            attr.asdict(h)
            for h in hs.get_highscores(
                hs.HighscoresDatabases.REMOTE,
                drag_select=drag_select,
                per_cell=per_cell,
                difficulty=difficulty,
                name=name,
            )
        ]
    )


@app.route("/api/v1/highscores/ranks", methods=["GET"])
def api_v1_highscores_ranks():
    """Provide a REST API to get highscores from the DB."""
    logger.debug("GET highscores with args: %s", dict(request.args))
    difficulty = request.args.get("difficulty")
    per_cell = request.args.get("per_cell")
    drag_select = request.args.get("drag_select")
    if not difficulty or not per_cell or not drag_select:
        abort(404)
    difficulty = Difficulty.from_str(difficulty)
    per_cell = int(per_cell)
    drag_select = bool(int(drag_select))
    return jsonify(
        [
            attr.asdict(h)
            for h in hs.filter_and_sort(
                hs.get_highscores(
                    hs.HighscoresDatabases.REMOTE,
                    drag_select=drag_select,
                    per_cell=per_cell,
                    difficulty=difficulty,
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
# Main
# ------------------------------------------------------------------------------


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, help="Override the default port")
    parser.add_argument("--bot", action="store_true", help="Handle bot messages")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    return parser.parse_args(argv)


def main(argv):
    if "SQL_DB_PASSWORD" not in os.environ:
        logger.error("No 'SQL_DB_PASSWORD' env var set")
        sys.exit(1)

    args = _parse_args(argv)

    logging.basicConfig(
        filename="server.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )

    if args.bot:
        bot.init_route_handling(app)

    logger.info("Starting up")
    if args.dev:
        os.environ["FLASK_ENV"] = "development"
        app.run(debug=True, port=args.port)
    else:
        from waitress import serve

        serve(app, port=args.port if args.port else 80)


if __name__ == "__main__":
    main(sys.argv[1:])
