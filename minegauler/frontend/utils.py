# December 2018, Lewis Gaul

"""
Utilities for the frontend.

Exports
-------
.. class:: CellUpdate_T
    A cell update type alias.

.. class:: MouseMove
    A mouse move tuple.

.. function:: save_highscore_file
    Save a highscore to file.

.. function:: read_highscore_file
    Read data from a highscore file.

"""

__all__ = (
    "CellUpdate_T",
    "MouseMove",
    "read_highscore_file",
    "save_highscore_file",
)

import gzip
import json
import logging
import pathlib
from collections import namedtuple
from typing import Iterable, List, Mapping, Tuple

import attr

from .. import paths
from ..shared import HighscoreStruct
from ..shared.types import CellContents, Coord, PathLike
from ..shared.utils import format_timestamp


logger = logging.getLogger(__name__)

CellUpdate_T = Tuple[float, Mapping[Coord, CellContents]]


# TODO
class MouseMove(namedtuple("_MouseMove", ["elapsed", "position"])):
    """A mouse move tuple."""

    def __new__(cls, elapsed: float, position: Coord):
        return super().__new__(cls, elapsed, position)


def save_highscore_file(
    highscore: HighscoreStruct, cell_updates: Iterable[CellUpdate_T]
) -> pathlib.Path:
    """
    Save a highscore to file.

    :param highscore:
        The highscore to save.
    :param cell_updates:
        The cell updates that were made during the game.
    :return:
        The path the file is saved at.
    """
    fname = (
        "{0.name}_{0.difficulty.value}_{0.elapsed:.2f}_{0.bbbv}_"
        "max={0.per_cell}_drag={0.drag_select}_{1}.mgh"
    ).format(
        highscore,
        format_timestamp(highscore.timestamp).replace(" ", "_").replace(":", "-"),
    )
    data = {
        "highscore": attr.asdict(highscore),
        "cell_updates": [
            (t, [(c, str(x)) for c, x in updates.items()])
            for t, updates in cell_updates
        ],
    }
    paths.DATA_DIR.mkdir(exist_ok=True)
    with gzip.open(paths.DATA_DIR / fname, "wt") as f:
        json.dump(data, f)
    return paths.DATA_DIR / fname


def read_highscore_file(
    path: PathLike,
) -> Tuple[HighscoreStruct, List[CellUpdate_T]]:
    """
    Read data from a highscore file.

    :param path:
        Path to the file.
    :return:
        The highscore struct and a list of cell updates.
    """
    with gzip.open(path, "rt") as f:
        data = json.load(f)
    return HighscoreStruct(**data["highscore"]), data["cell_updates"]
