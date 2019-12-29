"""
conftest.py - Pytest conf file

December 2018, Lewis Gaul
"""

from unittest import mock

import pytest

from minegauler.core import api, board
from minegauler.shared import utils


@pytest.fixture
def ctrlr() -> api.AbstractSwitchingController:
    ret = mock.Mock(spec=api.AbstractSwitchingController)
    ret._opts = utils.GameOptsStruct()
    ret.board = board.Board(ret._opts.x_size, ret._opts.y_size)
    return ret
