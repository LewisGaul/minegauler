# October 2021, Lewis Gaul

"""
Test the regular game module.

"""

import logging
import math
import time

import pytest
from pytest import approx

from minegauler.core.game import GameNotStartedError
from minegauler.core.regular.board import Board
from minegauler.core.regular.game import Game
from minegauler.core.regular.minefield import Minefield
from minegauler.core.regular.types import Coord
from minegauler.shared.types import Difficulty, GameState


logger = logging.getLogger(__name__)


@pytest.fixture
def started_game() -> Game:
    game = Game(x_size=4, y_size=5, mines=6, first_success=True)
    game.select_cell(Coord(0, 0))
    return game


class TestGame:
    """Test the regular Game class."""

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
        assert game.difficulty is Difficulty.CUSTOM

    def test_require_started(self):
        """Test trying to call methods that require a started game."""
        game = Game(x_size=4, y_size=5, mines=6)
        with pytest.raises(GameNotStartedError):
            game.get_elapsed()
        with pytest.raises(GameNotStartedError):
            game.get_3bvps()
        with pytest.raises(GameNotStartedError):
            game.get_rem_3bv()
        with pytest.raises(GameNotStartedError):
            game.get_prop_complete()

        game.mf.populate()
        with pytest.raises(GameNotStartedError):
            game.get_elapsed()
        with pytest.raises(GameNotStartedError):
            game.get_3bvps()

    def test_get_elapsed(self, started_game):
        """Test the method to get the elapsed game time."""
        started_game.start_time = time.time() - 10
        assert started_game.get_elapsed() == approx(10, abs=1e-3)

        started_game.end_time = started_game.start_time + 1.234
        assert started_game.get_elapsed() == approx(1.234)

    def test_get_3bvps(self, started_game):
        """Test the method to get the 3bv/s."""
        started_game.state = GameState.WON
        started_game.start_time = time.time() - 10
        started_game.end_time = started_game.start_time + 1.234
        assert started_game.get_3bvps() == approx(started_game.mf.bbbv / 1.234)

    def test_get_flag_proportion(self):
        """Test the method to get the proportion of flagging."""
        game = Game(x_size=4, y_size=5, mines=10, per_cell=10)

        # 10 mines, no flags.
        assert game.get_flag_proportion() == 0

        # 10 mines, 7 flags.
        game.set_cell_flags(Coord(0, 0), 7)
        assert game.get_flag_proportion() == approx(0.7)

        # 10 mines, 17 flags.
        game.set_cell_flags(Coord(1, 1), 10)
        assert game.get_flag_proportion() == approx(1.7)

    def test_get_prop_complete(self):
        """Test the method to get the proportion a game is complete."""
        mf = Minefield.from_2d_array(
            [
                # fmt: off
                [0, 0, 1, 1],
                [0, 0, 1, 1],
                [1, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                # fmt: on
            ],
        )
        game = Game.from_minefield(mf)
        assert game.mf.bbbv == 3

        # Not started game.
        assert game.get_rem_3bv() == 3
        assert game.get_prop_complete() == 0

        # Clicks that don't reduce remaining clicks.
        #   # 2 @ @
        #   # 5 @ @
        #   @ @ @ #
        #   2 # # #
        #   # # # #
        game.select_cell(Coord(1, 0))
        game.select_cell(Coord(1, 1))
        game.select_cell(Coord(0, 3))
        logger.debug("Board state:\n%s", game.board)
        assert game.get_rem_3bv() == 3
        assert game.get_prop_complete() == 0

        # Click an opening.
        #   . 2 @ @
        #   2 5 @ @
        #   @ @ @ #
        #   2 # # #
        #   # # # #
        game.select_cell(Coord(0, 0))
        logger.debug("Board state:\n%s", game.board)
        assert game.get_rem_3bv() == 2
        assert game.get_prop_complete() == approx(1 / 3)

        # Click an opening that has a wrong flag in it, stopping propagation.
        #   . 2 @ @
        #   2 5 @ @
        #   @ @ @ #
        #   2 3 # #
        #   . F # #
        game.set_cell_flags(Coord(1, 4), 1)
        game.select_cell(Coord(0, 4))
        logger.debug("Board state:\n%s", game.board)
        assert game.get_rem_3bv() == 2
        assert game.get_prop_complete() == approx(1 / 3)

        # Click an opening with a wrong flag at the edge.
        #   . 2 @ @
        #   2 5 @ @
        #   @ @ @ #
        #   2 3 F 1
        #   . . . .
        game.set_cell_flags(Coord(1, 4), 0)
        game.set_cell_flags(Coord(2, 3), 1)
        game.select_cell(Coord(1, 4))
        logger.debug("Board state:\n%s", game.board)
        assert game.get_rem_3bv() == 2
        assert game.get_prop_complete() == approx(1 / 3)

        # Finish previously blocked opening.
        #   . 2 @ @
        #   2 5 @ @
        #   @ @ @ #
        #   2 3 2 1
        #   . . . .
        game.set_cell_flags(Coord(2, 3), 0)
        game.chord_on_cell(Coord(1, 4))
        logger.debug("Board state:\n%s", game.board)
        assert game.get_rem_3bv() == 1
        assert game.get_prop_complete() == approx(2 / 3)

        # Finish the game.
        #   . 2 @ @
        #   2 5 @ @
        #   @ @ @ 3
        #   2 3 2 1
        #   . . . .
        game.select_cell(Coord(3, 2))
        logger.debug("Board state:\n%s", game.board)
        assert game.get_rem_3bv() == 0
        assert game.get_prop_complete() == 1

    def test_empty_minefield(self):
        """Test game methods with an empty minefield."""
        game = Game(
            x_size=4,
            y_size=5,
            mines=0,
            first_success=False,
        )
        game.mf.populate()
        assert game.mf.bbbv == 1

        # Zero mines, no flags.
        assert game.get_flag_proportion() == 0
        assert game.get_prop_complete() == 0
        # Zero mines, one flag.
        game.set_cell_flags(Coord(0, 0), 1)
        assert game.get_flag_proportion() == math.inf

        game.set_cell_flags(Coord(0, 0), 0)
        game.select_cell(Coord(0, 0))
        assert game.state is GameState.WON
        assert game.get_elapsed() == 0
        assert game.get_3bvps() == math.inf
        assert game.get_flag_proportion() == 0
        assert game.get_prop_complete() == 1

    def test_almost_full_minefield(self):
        """Test game methods with an almost full minefield."""
        game = Game(x_size=4, y_size=5, mines=19, first_success=True)
        game.select_cell(Coord(0, 0))
        assert game.mf.bbbv == 1
        assert game.state is GameState.WON
        assert game.get_elapsed() == 0
        assert game.get_3bvps() == math.inf
        assert game.get_flag_proportion() == 0
