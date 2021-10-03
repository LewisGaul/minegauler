# October 2021, Lewis Gaul

from ...shared.types import GameMode
from ..board import BoardBase


class Board(BoardBase):
    """A split-cell minesweeper board."""

    mode = GameMode.SPLIT_CELL

    # TODO
