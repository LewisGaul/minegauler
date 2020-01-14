"""
server.py - Server entry-point

January 2020, Lewis Gaul
"""

import logging
import os
import sys

import attr

from flask import Flask, jsonify, request
from minegauler.shared import highscores as hs


logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/api/highscore", methods=["POST"])
def api_highscore():
    """Post a highscore to be added to the remote DB."""
    data = request.get_json()
    # verify_highscore(data)  TODO
    highscore = hs.HighscoreStruct.from_dict(data)
    logger.info("POST highscore: %s", highscore)
    try:
        hs.RemoteHighscoresDB().insert_highscore(highscore)
    except hs.DBConnectionError as e:
        logger.exception("Failed to insert highscore into remote DB")
        return str(e), 503
    return "", 200


@app.route("/api/highscores", methods=["GET"])
def api_highscores():
    """Provide a REST API to get highscores from the DB."""
    logger.info("GET highscores with args: %s", dict(request.args))
    difficulty = request.args.get("difficulty")
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


@app.route("/")
def index():
    # TODO
    return "Hello, World!\n"


@app.route("/highscores")
def highscores():
    # TODO: Serve a webpage.
    return "highscores"


def main():
    if "SQL_DB_PASSWORD" not in os.environ:
        logger.error("No 'SQL_DB_PASSWORD' env var set")
        sys.exit(1)

    logging.basicConfig(filename="server.log", level=logging.DEBUG)

    logger.info("Starting up")
    if "--dev" in sys.argv:
        os.environ["FLASK_ENV"] = "development"
        app.run(debug=True)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
