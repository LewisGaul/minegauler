import logging
import os
import sys

import attr

from flask import Flask, jsonify, request
from minegauler.shared import highscores as hs


logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello, World!\n"


@app.route("/api/highscore", methods=["POST"])
def api_highscore():
    logger.info("POST highscore: %s", request.args)
    return


@app.route("/api/highscores", methods=["GET"])
def api_highscores():
    logger.info("GET highscores with args: %s", request.args)
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


@app.route("/highscores")
def highscores():
    return "highscores"


if __name__ == "__main__":
    if "--dev" in sys.argv:
        os.environ["FLASK_ENV"] = "development"
        app.run(debug=True)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=8080)
