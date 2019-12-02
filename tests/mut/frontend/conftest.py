"""
conftest.py - Pytest conf file

December 2018, Lewis Gaul
"""

from unittest.mock import MagicMock

import pytest

from minegauler.core import api as core_api
from minegauler.core import board
from minegauler.core import utils as core_utils


@pytest.fixture
def ctrlr():
    mock = MagicMock()
    mock.opts = core_utils.GameOptsStruct()
    mock.board = board.Board(mock.opts.x_size, mock.opts.y_size)
    mock.mock_add_spec(core_api.AbstractController, spec_set=True)
    return mock
