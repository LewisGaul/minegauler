__all__ = ("init_route_handling",)

import logging
import os
import sys

import flask

from minegauler.shared import highscores as hs
from server import add_new_highscore_hook
from server.utils import is_highscore_new_best

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

    app.add_url_rule("/bot", "bot_message", routes.bot_message, methods=["POST"])

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
