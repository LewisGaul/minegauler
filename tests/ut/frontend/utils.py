# December 2019, Lewis Gaul

"""
Frontend test utils.

"""

import os

from pytestqt.qtbot import QtBot


def maybe_stop_for_interaction(qtbot: QtBot) -> None:
    """
    Stop the tests to interact with the GUI if 'TEST_INTERACT' environment
    variable is set.
    """
    if os.environ.get("TEST_INTERACT"):
        qtbot.stopForInteraction()
