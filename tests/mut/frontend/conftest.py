"""
conftest.py - Pytest conf file

December 2018, Lewis Gaul
"""

from unittest.mock import MagicMock

import pytest

from minegauler.core import Board, GameOptsStruct
from minegauler.core.api import AbstractController


@pytest.fixture
def ctrlr():
    mock = MagicMock()
    mock.opts = GameOptsStruct()
    mock._game.board = Board(mock.opts.x_size, mock.opts.y_size)
    # mock.mock_add_spec(AbstractController, spec_set=True)
    return mock
