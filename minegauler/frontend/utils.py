# December 2018, Lewis Gaul

"""
Utilities for the frontend.

Exports
-------
.. class:: CellUpdate_T
    A cell update type alias.

.. class:: MouseMove
    A mouse move tuple.

.. function:: save_highscore
    Save a highscore to file.

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
    "CellUpdate_T",
    "MouseMove",
    "save_highscore",
)

import json
import pathlib
import time
from collections import namedtuple
from typing import Iterable, Mapping, Tuple

import attr

from .. import ROOT_DIR
from ..shared.types import CellContents, Coord_T
from . import state


IMG_DIR: pathlib.Path = ROOT_DIR / "images"
FILES_DIR: pathlib.Path = ROOT_DIR / "files"
HIGHSCORES_DIR: pathlib.Path = ROOT_DIR / "highscores"


CellUpdate_T = Tuple[float, Mapping[Coord_T, CellContents]]


class MouseMove(namedtuple("_MouseMove", ["elapsed", "position"])):
    """A mouse move tuple."""

    def __new__(cls, elapsed: float, position: Coord_T):
        return super().__new__(cls, elapsed, position)


def save_highscore(
    game_state: state.PerGameState, cell_updates: Iterable[CellUpdate_T]
):
    """
    @@@
    :param game_state:
    :param cell_updates:
    """
    fname = ("{0.difficulty.value}_{0.per_cell}_{0.drag_select}_{1}.mgh").format(
        game_state, int(time.time())
    )
    data = {
        "game_opts": attr.asdict(game_state),
        "cell_updates": [
            (t, [(c, str(x)) for c, x in updates.items()])
            for t, updates in cell_updates
        ],
    }
    HIGHSCORES_DIR.mkdir(exist_ok=True)
    with open(HIGHSCORES_DIR / fname, "w") as f:
        json.dump(data, f)
