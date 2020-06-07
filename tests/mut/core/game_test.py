"""
Test the game module.

August 2019, Lewis Gaul
"""

from unittest.mock import Mock

from minegauler.core.game import Game, _ignore_if, _ignore_if_not
from minegauler.types import CellContents, GameState


def test_ignore_if_decorators():
    """
    Test the 'ignore if' and 'ignore if not' decorators, since they aren't
    fully used in the code.
    """
    game = Game(x_size=4, y_size=5, mines=5)
    mock_func = Mock()

    # First test 'ignore if'.
    # Test with one ignored cell state (flagged).
    decorated_mock = _ignore_if(cell_state=CellContents.Flag)(mock_func)
    decorated_mock(game, (0, 0))  # unclicked
    mock_func.assert_called_once()
    mock_func.reset_mock()

    game.set_cell_flags((0, 0), 1)
    decorated_mock(game, (0, 0))  # flagged
    mock_func.assert_not_called()

    # Test with multiple ignored cell states.
    decorated_mock = _ignore_if(cell_state=(CellContents.Flag, CellContents.Unclicked))(
        mock_func
    )
    decorated_mock(game, (0, 0))  # flagged
    mock_func.assert_not_called()

    decorated_mock(game, (0, 1))  # unclicked
    mock_func.assert_not_called()

    # Next test 'ignore if not'.
    mock_func.reset_mock()
    # Test with one game state (READY).
    decorated_mock = _ignore_if_not(game_state=GameState.READY)(mock_func)
    game.state = GameState.READY
    decorated_mock(game)
    mock_func.assert_called_once()
    mock_func.reset_mock()

    game.state = GameState.ACTIVE
    decorated_mock(game)
    mock_func.assert_not_called()

    # Test with multiple ignored cell states.
    decorated_mock = _ignore_if_not(game_state=(GameState.READY, GameState.ACTIVE))(
        mock_func
    )
    game.state = GameState.READY
    decorated_mock(game)
    mock_func.assert_called_once()
    mock_func.reset_mock()

    game.state = GameState.ACTIVE
    decorated_mock(game)
    mock_func.assert_called_once()
    mock_func.reset_mock()

    game.state = GameState.LOST
    decorated_mock(game)
    mock_func.assert_not_called()
