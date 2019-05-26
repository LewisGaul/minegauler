"""
minefield_widget_test.py - Test the minefield widget

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k minefield_widget_test]'
from the root directory.
"""

from unittest.mock import MagicMock

import pytest

from minegauler.shared.utils import GameOptsStruct



@pytest.fixture
def ctrlr():
    mock = MagicMock()
    mock.opts = GameOptsStruct()
    return mock
