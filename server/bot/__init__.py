"""
__init__.py - Bot package

February 2020, Lewis Gaul
"""

__all__ = ("init_route_handling",)

import json
import logging
import os
import sys

import flask

from minegauler.shared import highscores as hs

from .. import add_new_highscore_hook
from ..utils import is_highscore_new_best
from . import routes, utils


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# External
# ------------------------------------------------------------------------------


def init_route_handling(app: flask.app.Flask):
    if "BOT_ACCESS_TOKEN" not in os.environ:
        logger.error("No 'BOT_ACCESS_TOKEN' env var set")
        sys.exit(1)
    utils.set_bot_access_token(os.environ["BOT_ACCESS_TOKEN"])

    try:
        with open(utils.USER_NAMES_FILE) as f:
            utils.USER_NAMES = json.load(f)
    except FileNotFoundError:
        logger.warning("%s file not found", utils.USER_NAMES_FILE)

    routes.activate_bot_msg_handling(app)

    add_new_highscore_hook(_new_highscore_hook)


# ------------------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------------------


def _new_highscore_hook(highscore: hs.HighscoreStruct) -> None:
    if highscore.name != "Siwel G":
        try:
            utils.send_myself_message(f"New highscore added:\n{highscore}")
        except Exception:
            logger.exception("Error sending webex message")

    if is_highscore_new_best(highscore) == "time":
        try:
            utils.send_new_best_message(highscore)
        except Exception:
            logger.exception("Error sending webex message for new best")
