# April 2018, Lewis Gaul

__all__ = ("GAME_MODE_IMPL",)

from typing import Any, Mapping

from ..shared.types import GameMode
from . import board, game, minefield, regular, split_cells


# TODO: Re-add imports when fixed
# from . import api, board, engine, game, minefield, regular, split_cells


GAME_MODE_IMPL: Mapping[GameMode, Any] = {
    GameMode.REGULAR: regular,
    GameMode.SPLIT_CELL: split_cells,
}
