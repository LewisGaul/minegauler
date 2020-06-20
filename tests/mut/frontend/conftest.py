# December 2018, Lewis Gaul

"""
Pytest conftest file.

"""

from unittest import mock

import pytest

from minegauler.core import api, board
from minegauler.shared import utils


@pytest.fixture
def ctrlr() -> api.AbstractController:
    ret = mock.Mock(spec=api.AbstractController)
    ret._opts = utils.GameOptsStruct()
    ret.board = board.Board(ret._opts.x_size, ret._opts.y_size)
    return ret
