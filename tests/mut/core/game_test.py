# August 2019, Lewis Gaul

"""
Test the core game module.

"""

import logging
from unittest import mock

from minegauler.core.game import _ignore_if, _ignore_if_not
from minegauler.core.regular.game import Game
from minegauler.core.regular.types import Coord
from minegauler.shared.types import CellContents, GameState


logger = logging.getLogger(__name__)


class TestIgnoreIfDecorators:
    """
    Test the 'ignore if' and 'ignore if not' decorators, since they aren't
    fully used in the code.
    """

    game = Game(x_size=4, y_size=5, mines=5)
    mock_func = mock.Mock()

    def setup_method(self):
        self.mock_func.reset_mock()

    def test_ignore_if_cell_state(self):
        """Test 'ignore if' with one cell state."""
        decorated_mock = _ignore_if(cell_state=CellContents.Flag)(self.mock_func)

        decorated_mock(self.game, Coord(0, 0))  # unclicked
        self.mock_func.assert_called_once()
        self.mock_func.reset_mock()

        self.game.set_cell_flags(Coord(0, 0), 1)
        decorated_mock(self.game, Coord(0, 0))  # flagged
        self.mock_func.assert_not_called()

    def test_ignore_if_multiple_cell_states(self):
        """Test 'ignore if' with multiple cell states."""
        decorator = _ignore_if(cell_state=(CellContents.Flag, CellContents.Unclicked))
        decorated_mock = decorator(self.mock_func)

        decorated_mock(self.game, Coord(0, 0))  # flagged
        self.mock_func.assert_not_called()

        decorated_mock(self.game, Coord(0, 1))  # unclicked
        self.mock_func.assert_not_called()

    def test_ignore_if_not_game_state(self):
        """Test 'ignore if not' with one game state."""
        decorated_mock = _ignore_if_not(game_state=GameState.READY)(self.mock_func)

        self.game.state = GameState.READY
        decorated_mock(self.game)
        self.mock_func.assert_called_once()
        self.mock_func.reset_mock()

        self.game.state = GameState.ACTIVE
        decorated_mock(self.game)
        self.mock_func.assert_not_called()

    def test_ignore_if_not_multiple_game_states(self):
        """Test 'ignore if not' with multiple game states."""
        decorator = _ignore_if_not(game_state=(GameState.READY, GameState.ACTIVE))
        decorated_mock = decorator(self.mock_func)

        self.game.state = GameState.READY
        decorated_mock(self.game)
        self.mock_func.assert_called_once()
        self.mock_func.reset_mock()

        self.game.state = GameState.ACTIVE
        decorated_mock(self.game)
        self.mock_func.assert_called_once()
        self.mock_func.reset_mock()

        self.game.state = GameState.LOST
        decorated_mock(self.game)
        self.mock_func.assert_not_called()
