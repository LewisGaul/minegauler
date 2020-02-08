import logging
import re

import flask
from flask import request

from minegauler.shared import highscores as hs
from server.bot import msgparse

from . import format, utils
from .utils import BOT_NAME


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------------------


def bot_message():
    """Receive a notification of a bot message."""
    data = request.get_json()["data"]
    logger.debug("POST bot message: %s", data)
    if utils.user_from_email(data["personEmail"]) == BOT_NAME:
        # Ignore messages sent by the bot.
        return "", 200

    msg_id = data["id"]
    msg_text = utils.get_message(msg_id)
    logger.debug("Fetched message content: %r", msg_text)
    if "roomId" in data:
        room_id = data["roomId"]
    else:
        room_id = data["personId"]
    msg = re.sub(r"@?Minegauler", "", msg_text, 1).strip().lower()
    logger.debug("Handling message: %r", msg)

    if not msg:
        return "", 200

    utils.send_group_message(msgparse.parse_msg(msg))

    return "", 200


def handle_bot_messages(app: flask.app.Flask) -> None:
    """Register a route to handle bot messages."""
    app.add_url_rule(bot_message, methods=["POST"])
