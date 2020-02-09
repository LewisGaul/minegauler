"""
routes.py - Definition of bot HTTP routes

February 2020, Lewis Gaul
"""

import logging
import re

import flask
import requests
from flask import request

from . import msgparse, utils
from .utils import BOT_NAME


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------------------


def bot_message():
    """Receive a notification of a bot message."""
    data = request.get_json()["data"]
    logger.debug("POST bot message: %s", data)
    user = utils.user_from_email(data["personEmail"])
    if user == BOT_NAME:
        # Ignore messages sent by the bot.
        return "", 200

    msg_id = data["id"]
    try:
        msg_text = utils.get_message(msg_id)
    except requests.HTTPError:
        logger.exception(f"Error getting message from {user}")
        raise

    logger.debug("Fetched message content: %r", msg_text)
    msg = re.sub(r"@?Minegauler", "", msg_text, 1).strip().lower()
    logger.debug("Handling message: %r", msg)

    if not msg:
        return "", 200

    room_id = data["roomId"]
    person_id = data["personId"]
    room_type = msgparse.RoomType(data["roomType"])

    send_to_person_id = False
    send_to_id = room_id
    try:
        resp_msg = msgparse.parse_msg(msg, room_type, allow_markdown=True)
    except msgparse.InvalidArgsError as e:
        resp_msg = str(e)
        if room_type is msgparse.RoomType.GROUP:
            # Send error message to direct chat.
            send_to_person_id = True
            send_to_id = person_id

    try:
        utils.send_message(
            send_to_id, resp_msg, is_person_id=send_to_person_id, markdown=True
        )
    except requests.HTTPError:
        # TODO: I want to know about this!
        logger.exception("Error sending bot response message")

    return "", 200


def handle_bot_messages(app: flask.app.Flask) -> None:
    """Register a route to handle bot messages."""
    app.add_url_rule("bot/message", "bot_message", bot_message, methods=["POST"])
