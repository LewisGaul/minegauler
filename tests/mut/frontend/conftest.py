# December 2018, Lewis Gaul

"""
Pytest conftest file.

"""

from unittest import mock

import pytest

from minegauler import api
from minegauler.core import regular
from minegauler.shared import utils
from minegauler.shared.types import Difficulty, GameMode, GameState


@pytest.fixture
def ctrlr() -> api.AbstractController:
    ret = mock.Mock(spec=api.AbstractController)
    ret._opts = utils.GameOptsStruct()
    ret.get_game_info.return_value = api.GameInfo(
        game_state=GameState.READY,
        x_size=8,
        y_size=8,
        mines=10,
        difficulty=Difficulty.BEGINNER,
        per_cell=1,
        first_success=True,
        mode=GameMode.REGULAR,
        minefield_known=False,
    )
    ret.board = regular.Board(ret._opts.x_size, ret._opts.y_size)
    return ret
