"""
Test the game module.

August 2019, Lewis Gaul
"""

import math
import time
from unittest import mock

import pytest
from pytest import approx

from minegauler.core.board import Board, Minefield
from minegauler.core.game import Game, GameNotStartedError, _ignore_if, _ignore_if_not
from minegauler.types import CellContents, GameState


@pytest.fixture
def new_game() -> Game:
    return Game(x_size=4, y_size=5, mines=6)


@pytest.fixture
def started_game() -> Game:
    game = Game(x_size=4, y_size=5, mines=6, first_success=True)
    game.select_cell((0, 0))
    return game


class TestGame:
    """Test the Game class."""

    def test_basic_create(self):
        """Test basic creation of a 'Game' instance."""
        game = Game(x_size=4, y_size=5, mines=6)
        assert game.x_size == 4
        assert game.y_size == 5
        assert game.mines == 6
        assert game.per_cell == 1
        assert game.lives == 1
        assert game.first_success is False
        assert game.state is GameState.READY
        assert game.start_time is None
        assert game.end_time is None
        assert game.board == Board(x_size=4, y_size=5)
        assert game.difficulty == "C"

    def test_require_started(self, new_game):
        """Test trying to call methods that require a started game."""
        with pytest.raises(GameNotStartedError):
            new_game.get_elapsed()
        with pytest.raises(GameNotStartedError):
            new_game.get_flag_proportion()
        with pytest.raises(GameNotStartedError):
            new_game.get_rem_3bv()
        with pytest.raises(GameNotStartedError):
            new_game.get_prop_complete()
        with pytest.raises(GameNotStartedError):
            new_game.get_3bvps()

    def test_get_elapsed(self, started_game):
        """Test the method to get the elapsed game time."""
        started_game.start_time = time.time() - 10
        assert started_game.get_elapsed() == approx(10)

        started_game.end_time = started_game.start_time + 1.234
        assert started_game.get_elapsed() == approx(1.234)

    def test_get_flag_proportion(self):
        """Test the method to get the proportion of flagging."""
        empty_game = Game(minefield=Minefield(x_size=4, y_size=5, mines=0))
        empty_game.state = GameState.ACTIVE
        empty_game.start_time = time.time()
        normal_game = Game(
            minefield=Minefield(x_size=4, y_size=5, mines=10, per_cell=10)
        )
        normal_game.state = GameState.ACTIVE
        normal_game.start_time = time.time()

        # Zero mines, no flags.
        assert empty_game.get_flag_proportion() == 0

        # Zero mines, one flag.
        empty_game.set_cell_flags((0, 0), 1)
        assert empty_game.get_flag_proportion() == math.inf

        # 10 mines, no flags.
        assert normal_game.get_flag_proportion() == 0

        # 10 mines, 7 flags.
        normal_game.set_cell_flags((0, 0), 7)
        assert normal_game.get_flag_proportion() == approx(0.7)

        # 10 mines, 17 flags.
        normal_game.set_cell_flags((1, 1), 10)
        assert normal_game.get_flag_proportion() == approx(1.7)

    def test_get_rem_3bv(self):
        """Test the method to get the remaining 3bv of a game."""
        # TODO

    def test_get_prop_complete(self):
        """Test the method to get the proportion a game is complete."""
        # TODO


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

        decorated_mock(self.game, (0, 0))  # unclicked
        self.mock_func.assert_called_once()
        self.mock_func.reset_mock()

        self.game.set_cell_flags((0, 0), 1)
        decorated_mock(self.game, (0, 0))  # flagged
        self.mock_func.assert_not_called()

    def test_ignore_if_multiple_cell_states(self):
        """Test 'ignore if' with multiple cell states."""
        decorator = _ignore_if(cell_state=(CellContents.Flag, CellContents.Unclicked))
        decorated_mock = decorator(self.mock_func)

        decorated_mock(self.game, (0, 0))  # flagged
        self.mock_func.assert_not_called()

        decorated_mock(self.game, (0, 1))  # unclicked
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
