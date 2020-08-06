# February 2020, Lewis Gaul

"""
Definition of bot HTTP routes.

"""

__all__ = ("activate_bot_msg_handling", "new_highscore_hook")

import logging
import re

import flask
import requests
from flask import request

from minegauler.shared import highscores as hs

from . import msgparse, utils


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# REST API
# ------------------------------------------------------------------------------


def bot_message():
    """Receive a notification of a bot message."""
    data = request.get_json()["data"]
    logger.debug("POST bot message: %s", data)
    user = utils.user_from_email(data["personEmail"])
    send_welcome = False
    if user == utils.BOT_NAME:
        # Ignore messages sent by the bot.
        return "", 200
    elif user not in utils.USER_NAMES:
        # If the user is not yet tracked, add the username as the default name.
        logger.debug("Adding new user %r", user)
        utils.set_user_nickname(user, user)
        send_welcome = True

    msg_id = data["id"]
    try:
        msg_text = utils.get_message(msg_id)
    except requests.HTTPError:
        logger.exception(f"Error getting message from {user}")
        _send_myself_error_msg("getting message")
        raise

    logger.debug("Fetched message content: %r", msg_text)
    msg = re.sub(r"@?Minegauler(?: Bot)?", "", msg_text, 1).strip()
    logger.debug("Handling message: %r", msg)

    if not msg:
        return "", 200

    room_id = data["roomId"]
    person_id = data["personId"]
    room_type = msgparse.RoomType(data["roomType"])

    if send_welcome:
        try:
            utils.send_message(
                person_id, msgparse.GENERAL_INFO, is_person_id=True, markdown=True
            )
        except requests.HTTPError:
            logger.exception("Error sending bot welcome message")
            _send_myself_error_msg("sending bot welcome message")

    send_to_person_id = False
    send_to_id = room_id
    try:
        resp_msg = msgparse.parse_msg(
            msg, room_type, allow_markdown=True, username=user
        )
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
        logger.exception("Error sending bot response message")
        _send_myself_error_msg("sending bot response message")

    return "", 200


def new_highscore_hook(highscore: hs.HighscoreStruct) -> None:
    if highscore.name != "Siwel G":
        try:
            utils.send_myself_message(f"New highscore added:\n{highscore}")
        except Exception:
            logger.exception("Error sending webex message")

    if (
        highscore.name in utils.USER_NAMES.values()
        and utils.is_highscore_new_best(highscore) == "time"
    ):
        try:
            utils.send_new_best_message(highscore)
        except Exception:
            logger.exception("Error sending webex message for new best")
            _send_myself_error_msg("sending webex message for new best")


def activate_bot_msg_handling(app: flask.app.Flask) -> None:
    """Register a route to handle bot messages."""

    def bot_message_with_error_catching():
        try:
            return bot_message()
        except Exception:
            logger.exception("Unexpected error occurred handling a bot message")
            _send_myself_error_msg("<uncaught> occurred")
            raise

    app.add_url_rule(
        "/bot/message", "bot_message", bot_message_with_error_catching, methods=["POST"]
    )


def _send_myself_error_msg(error: str) -> None:
    try:
        utils.send_myself_message(f"Error {error}, see server logs")
    except requests.HTTPError:
        logger.exception("Error sending myself bot message when handling error")
