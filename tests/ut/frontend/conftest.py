# December 2018, Lewis Gaul

"""
Pytest conftest file.

"""

from unittest import mock

import pytest

from minegauler.app import api
from minegauler.app.core import regular
from minegauler.app.shared import utils
from minegauler.app.shared.types import Difficulty, GameMode, GameState, ReachSetting


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
        first_success=True,
        per_cell=1,
        reach=ReachSetting.NORMAL,
        mode=GameMode.REGULAR,
        minefield_known=False,
    )
    ret.board = regular.Board(ret._opts.x_size, ret._opts.y_size)
    return ret
