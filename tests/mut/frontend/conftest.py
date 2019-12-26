"""
conftest.py - Pytest conf file

December 2018, Lewis Gaul
"""

from unittest.mock import MagicMock

import pytest

from minegauler import utils
from minegauler.core import api as core_api
from minegauler.core import board


@pytest.fixture
def ctrlr():
    mock = MagicMock()
    mock._opts = utils.GameOptsStruct()
    mock.board = board.Board(mock._opts.x_size, mock._opts.y_size)
    mock.mock_add_spec(core_api.AbstractSwitchingController, spec_set=True)
    return mock
