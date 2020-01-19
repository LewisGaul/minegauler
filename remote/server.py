"""
server.py - Server entry-point

January 2020, Lewis Gaul
"""

import logging
import os
import re
import sys
from typing import Iterable

import attr
import requests
from flask import Flask, jsonify, redirect, request
from requests_toolbelt.multipart.encoder import MultipartEncoder

from minegauler.shared import highscores as hs


logger = logging.getLogger(__name__)

app = Flask(__name__)


_BOT_ACCESS_TOKEN = None
_BOT_EMAIL = "minegaulerbot@webex.bot"
# fmt: off
_WEBEX_GROUP_ROOM_ID = "Y2lzY29zcGFyazovL3VzL1JPT00vNzYyNjI4NTAtMzg3Ni0xMWVhLTlhM2ItODMyNzMyZDlkZTg3"
# fmt: on


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def _get_person_id(name_or_email: str) -> str:
    if "@" in name_or_email:
        params = {"email": name_or_email}
    else:
        params = {"displayName": name_or_email}
    response = requests.get(
        f"https://api.ciscospark.com/v1/people",
        params=params,
        headers={"Authorization": f"Bearer {_BOT_ACCESS_TOKEN}"},
    )
    response.raise_for_status()
    return response.json()["items"][0]["id"]


def _get_my_id() -> str:
    return _get_person_id("Lewis Gaul")


def _get_bot_id() -> str:
    return _get_person_id("Minegauler Bot")


def _get_message(msg_id: str) -> str:
    response = requests.get(
        f"https://api.ciscospark.com/v1/messages/{msg_id}",
        headers={"Authorization": f"Bearer {_BOT_ACCESS_TOKEN}"},
    )
    return response.json()["text"]


def _send_message(room_id: str, text: str, *, is_person_id=False) -> requests.Response:
    id_field = "toPersonId" if is_person_id else "roomId"
    multipart = MultipartEncoder({"text": text, id_field: room_id})
    response = requests.post(
        "https://api.ciscospark.com/v1/messages",
        data=multipart,
        headers={
            "Authorization": f"Bearer {_BOT_ACCESS_TOKEN}",
            "Content-Type": multipart.content_type,
        },
    )
    response.raise_for_status()
    return response


def _send_myself_message(text: str) -> requests.Response:
    return _send_message(_get_my_id(), text, is_person_id=True)


def _send_group_message(text: str) -> requests.Response:
    return _send_message(_WEBEX_GROUP_ROOM_ID, text)


def _format_highscores(highscores: Iterable[hs.HighscoreStruct]) -> str:
    lines = [f"{h.name:<15s}  {h.elapsed:.2f}" for h in highscores]
    return "\n".join(lines)


def _send_message_if_new_best(h: hs.HighscoreStruct) -> None:
    all_highscores = hs.get_highscores(hs.HighscoresDatabases.REMOTE, settings=h)
    if h.difficulty == "B":
        diff = "beginner"
    elif h.difficulty == "I":
        diff = "intermediate"
    elif h.difficulty == "E":
        diff = "expert"
    elif h.difficulty == "M":
        diff = "master"
    else:
        assert False
    strbool = lambda x: "True" if x else "False"
    if hs.is_highscore_new_best(h, all_highscores) == "time":
        _send_group_message(
            f"New personal record of {h.elapsed:.2f} set by {h.name} on {diff}!\n"
            f"Settings: drag-select={strbool(h.drag_select)}, per-cell={h.per_cell}"
        )


# ------------------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------------------


@app.route("/api/v1/highscore", methods=["POST"])
def api_v1_highscore():
    """Post a highscore to be added to the remote DB."""
    data = request.get_json()
    # verify_highscore(data)  TODO
    highscore = hs.HighscoreStruct.from_dict(data)
    logger.debug("POST highscore: %s", highscore)

    if _BOT_ACCESS_TOKEN and highscore.name != "Siwel G":
        try:
            _send_myself_message(f"New highscore added:\n{highscore}")
        except Exception:
            logger.exception("Error sending webex message")

    try:
        hs.RemoteHighscoresDB().insert_highscore(highscore)
    except hs.DBConnectionError as e:
        logger.exception("Failed to insert highscore into remote DB")
        return str(e), 503

    if _BOT_ACCESS_TOKEN:
        try:
            _send_message_if_new_best(highscore)
        except Exception:
            logger.exception("Error sending webex message for new best")

    return "", 200


@app.route("/api/v1/highscores", methods=["GET"])
def api_v1_highscores():
    """Provide a REST API to get highscores from the DB."""
    logger.debug("GET highscores with args: %s", dict(request.args))
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


@app.route("/bot/message", methods=["POST"])
def bot_message():
    data = request.get_json()["data"]
    logger.debug("POST bot message: %s", data)
    if data["personEmail"] == _BOT_EMAIL:
        return "", 200

    msg_id = data["id"]
    msg_text = _get_message(msg_id)
    logger.debug("Fetched message content: %r", msg_text)
    if "roomId" in data:
        room_id = data["roomId"]
    else:
        room_id = data["personId"]
    msg = re.sub(r"@?Minegauler", "", msg_text, 1).strip().lower()
    logger.debug("Handling message: %r", msg)

    if not msg:
        return "", 200

    words = msg.split()
    if re.match(words[0], "beginner"):
        difficulty = "b"
    elif re.match(words[0], "intermediate"):
        difficulty = "i"
    elif re.match(words[0], "expert"):
        difficulty = "e"
    elif re.match(words[0], "master"):
        difficulty = "m"
    else:
        difficulty = None
    if difficulty:
        if len(words) > 1 and words[1] == "ranks":
            highscores = hs.get_highscores(
                hs.HighscoresDatabases.REMOTE, difficulty=difficulty
            )
            highscores = hs.filter_and_sort(highscores, "time", dict())
            _send_message(room_id, _format_highscores(highscores))

    return "", 200


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


def main():
    global _BOT_ACCESS_TOKEN

    if "SQL_DB_PASSWORD" not in os.environ:
        logger.error("No 'SQL_DB_PASSWORD' env var set")
        sys.exit(1)

    if "BOT_ACCESS_TOKEN" not in os.environ:
        logger.warning("No 'BOT_ACCESS_TOKEN' env var set")
    else:
        _BOT_ACCESS_TOKEN = os.environ["BOT_ACCESS_TOKEN"]

    logging.basicConfig(
        filename="server.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )

    logger.info("Starting up")
    if "--dev" in sys.argv:
        os.environ["FLASK_ENV"] = "development"
        app.run(debug=True)
    else:
        from waitress import serve

        serve(app, listen="*:80")


if __name__ == "__main__":
    main()
