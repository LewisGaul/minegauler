# December 2018, Lewis Gaul

"""
Utilities for the frontend.

Exports
-------
.. class:: ClickEvent
    An enum of click events.

.. class:: MouseEvent
    A mouse event tuple.

.. class:: MouseMove
    A mouse move tuple.

.. data:: FILES_DIR
    The directory containing files.

.. data:: HIGHSCORES_DIR
    The directory containing highscore files.

.. data:: IMG_DIR
    The directory containing images.

"""

__all__ = (
    "FILES_DIR",
    "HIGHSCORES_DIR",
    "IMG_DIR",
    "ClickEvent",
    "MouseEvent",
    "MouseMove",
    "save_highscore",
)

import enum
import json
import pathlib
from collections import namedtuple
from typing import List

import attr

from .. import ROOT_DIR
from ..shared.types import Coord_T
from . import state


IMG_DIR: pathlib.Path = ROOT_DIR / "images"
FILES_DIR: pathlib.Path = ROOT_DIR / "files"
HIGHSCORES_DIR: pathlib.Path = ROOT_DIR / "highscores"


class ClickEvent(enum.IntEnum):
    """An enum of events triggered by some form of mouse click."""

    LEFT_DOWN = 1
    LEFT_MOVE = 2
    LEFT_UP = 3
    RIGHT_DOWN = 4
    RIGHT_MOVE = 5
    BOTH_DOWN = 6
    BOTH_MOVE = 7
    FIRST_OF_BOTH_UP = 8
    DOUBLE_LEFT_DOWN = 9
    DOUBLE_LEFT_MOVE = 10


class MouseEvent(namedtuple("_MouseEvent", ["elapsed", "event", "coord"])):
    """A mouse event tuple."""

    def __new__(cls, elapsed: float, event: ClickEvent, coord: Coord_T):
        return super().__new__(cls, elapsed, event, coord)


class MouseMove(namedtuple("_MouseMove", ["elapsed", "position"])):
    """A mouse move tuple."""

    def __new__(cls, elapsed: float, position: Coord_T):
        return super().__new__(cls, elapsed, position)


def save_highscore(game_state: state.PerGameState, mouse_events: List[MouseEvent]):
    """
    @@@
    :param game_state:
    :param mouse_events:
    """
    fname = "{0.difficulty.value}_{0.per_cell}_{0.drag_select}.mgh".format(game_state)
    data = {"game_opts": attr.asdict(game_state), "mouse_events": mouse_events}
    HIGHSCORES_DIR.mkdir(exist_ok=True)
    with open(HIGHSCORES_DIR / fname, "w") as f:
        json.dump(data, f)
