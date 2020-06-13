"""
Test the game engine module.

October 2018, Lewis Gaul
"""

import logging
from unittest import mock

import pytest

from minegauler.core.board import Board, Minefield
from minegauler.core.engine import GameController
from minegauler.shared.types import CellContents, GameState
from minegauler.shared.utils import GameOptsStruct


logger = logging.getLogger(__name__)


@pytest.fixture()
def frontend1():
    return mock.Mock()


@pytest.fixture()
def frontend2():
    return mock.Mock()


class TestController:

    mf = Minefield.from_2d_array(
        [
            # fmt: off
            [0, 0, 1, 2],
            [0, 0, 0, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 1, 0, 0],
            # fmt: on
        ],
        per_cell=2,
    )
    opts = GameOptsStruct(
        x_size=mf.x_size,
        y_size=mf.y_size,
        mines=mf.nr_mines,
        per_cell=mf.per_cell,
        first_success=True,
    )

    # --------------------------------------------------------------------------
    # Test cases
    # --------------------------------------------------------------------------
    def test_create(self):
        """Test basic creation of a controller."""
        ctrlr = GameController(self.opts)
        assert ctrlr._opts == self.opts
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mf is None
        assert ctrlr._game.board == Board(self.opts.x_size, self.opts.y_size)

    def test_register_listeners(self, frontend1, frontend2):
        """Test registering listeners."""
        # Register two listeners.
        ctrlr = self.create_controller()
        ctrlr.register_listener(frontend1)
        ctrlr.register_listener(frontend2)

        # Check callbacks are called.
        ctrlr._game.state = GameState.ACTIVE
        ctrlr._send_updates(dict())
        for listener in [frontend1, frontend2]:
            listener.update_game_state.assert_called_once()

    def test_cell_interaction(self):
        """Test various basic cell interaction."""
        coord = (2, 2)

        # Setup.
        opts = GameOptsStruct(per_cell=2, first_success=False)
        ctrlr = self.create_controller(opts=opts, set_mf=False)

        # Flag a cell.
        ctrlr.flag_cell(coord)
        assert ctrlr._game.board[coord] is CellContents.Flag(1)
        assert not ctrlr._game.mf
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines - 1

        # Select a flagged cell.
        ctrlr.select_cell(coord)
        assert ctrlr._game.board[coord] is CellContents.Flag(1)
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines - 1

        # Flag a cell that is already flagged (multiple mines per cell).
        ctrlr.flag_cell(coord)
        assert ctrlr._game.board[coord] is CellContents.Flag(2)
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines - 2

        # Flag a cell that is at max flags to reset it.
        ctrlr.flag_cell(coord)
        assert ctrlr._game.board[coord] is CellContents.Unclicked
        assert not ctrlr._game.mf
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines

        # Remove cell flags.
        ctrlr.flag_cell(coord)
        ctrlr.remove_cell_flags(coord)
        assert ctrlr._game.board[coord] is CellContents.Unclicked
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines

        # Select a cell to start the game.
        ctrlr.select_cell(coord)
        assert isinstance(
            ctrlr._game.board[coord], (CellContents.HitMine, CellContents.Num)
        )
        assert ctrlr._game.mf
        assert ctrlr._game.state in {GameState.ACTIVE, GameState.LOST}
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines

        # Select an already-selected cell.
        revealed = ctrlr._game.board[coord]
        ctrlr.select_cell(coord)
        assert ctrlr._game.board[coord] == revealed

    def test_select_opening(self):
        """Test clicking and revealing an opening."""
        exp_board = Board.from_2d_array(
            [
                # fmt: off
                [ 0,   1,  "#", "#"],
                [ 0,   1,   4,  "#"],
                [ 0,   0,   1,  "#"],
                [ 1,   1,   1,  "#"],
                ["#", "#", "#", "#"],
                # fmt: on
            ]
        )
        # Select a cell to trigger the opening.
        ctrlr = self.create_controller()
        ctrlr.select_cell((0, 0))
        assert ctrlr._game.board == exp_board

        # Select the edge of an opening.
        ctrlr = self.create_controller()
        ctrlr.select_cell((1, 3))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                ["#",  1,  "#", "#"],
                ["#", "#", "#", "#"],
                # fmt: on
            ]
        )

        # Select a different cell to trigger the same opening as above.
        ctrlr.select_cell((1, 2))
        assert ctrlr._game.board == exp_board

        # Select another cell to trigger the other opening.
        ctrlr.select_cell((3, 4))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                [ 0,   1, "#", "#"],
                [ 0,   1,   4, "#"],
                [ 0,   0,   1,  1 ],
                [ 1,   1,   1,  0 ],
                ["#", "#",  1,  0 ],
                # fmt: on
            ]
        )

        # Trigger opening with incorrect flag blocking the way.
        ctrlr = self.create_controller()
        ctrlr.flag_cell((0, 1))
        ctrlr.select_cell((0, 0))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                [ 0,   1,  "#", "#"],
                ["F1", 1,  "#", "#"],
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                # fmt: on
            ]
        )

        # Select doesn't trigger remainder of opening on revealed opening.
        ctrlr.remove_cell_flags((0, 1))
        ctrlr.select_cell((0, 0))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                [ 0,   1,  "#", "#"],
                ["#",  1,  "#", "#"],
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                # fmt: on
            ]
        )

        # Chording does trigger remainder of opening on revealed opening. Also
        # test other invalid flags blocking the opening.
        ctrlr.flag_cell((0, 3))
        ctrlr.flag_cell((0, 2))
        ctrlr.chord_on_cell((0, 0))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                [ 0,   1,  "#", "#"],
                [ 0,   1,   4,  "#"],
                ["F1", 0,   1,  "#"],
                ["F1", 1,   1,  "#"],
                ["#", "#", "#", "#"],
                # fmt: on
            ]
        )

    def test_chording(self):
        """Test chording in various situations."""
        # Use the same controller throughout the test.
        ctrlr = self.create_controller()

        # No-op chording - game not started.
        ctrlr.chord_on_cell((0, 0))
        assert ctrlr._game.state is GameState.READY

        # No-op chording - no flags.
        ctrlr.select_cell((0, 4))
        ctrlr.chord_on_cell((0, 4))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                ["#", "#", "#", "#"],
                [ 1,  "#", "#", "#"],
                # fmt: on
            ]
        )

        # Basic successful chording.
        ctrlr.flag_cell((1, 4))
        ctrlr.chord_on_cell((0, 4))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#", "#",  "#", "#"],
                ["#", "#",  "#", "#"],
                ["#", "#",  "#", "#"],
                [ 1,   1,   "#", "#"],
                [ 1,  "F1", "#", "#"],
                # fmt: on
            ]
        )

        # Successful chording triggering opening.
        ctrlr.chord_on_cell((1, 3))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                [0,  1,  "#", "#"],
                [0,  1,   4,  "#"],
                [0,  0,   1,  "#"],
                [1,  1,   1,  "#"],
                [1, "F1", 1,  "#"],
                # fmt: on
            ]
        )

        # No-op - repeated chording.
        prev_board = ctrlr._game.board
        ctrlr.chord_on_cell((1, 3))
        assert ctrlr._game.board == prev_board

        # No-op - chording on flagged cell.
        ctrlr.chord_on_cell((1, 4))
        assert ctrlr._game.board == prev_board

        # No-op - wrong number of flags.
        ctrlr.flag_cell((3, 0))
        ctrlr.flag_cell((3, 0))
        ctrlr.chord_on_cell((2, 1))

        # Incorrect flags cause hitting a mine.
        ctrlr.flag_cell((3, 2))
        ctrlr.chord_on_cell((2, 2))
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                [0,  1,  "M1", "F2"],
                [0,  1,   4,   "!1"],
                [0,  0,   1,   "X1"],
                [1,  1,   1,    0  ],
                [1, "F1", 1,    0  ],
                # fmt: on
            ]
        )

    def test_first_success(self):
        """Test success on first click toggle option."""
        # First click should hit an opening with first_success set.
        opts = GameOptsStruct(first_success=True)
        ctrlr = GameController(opts)
        coord = (1, 5)
        ctrlr.select_cell(coord)
        assert ctrlr._game.state is GameState.ACTIVE
        assert ctrlr._game.board[coord] is CellContents.Num(0)
        for c in ctrlr._game.board.get_nbrs(coord):
            assert type(ctrlr._game.board[c]) is CellContents.Num

        # Check first success is ignored when using created minefield.
        ctrlr = self.create_controller()
        coord = (3, 0)
        ctrlr.select_cell(coord)
        assert ctrlr._game.state is GameState.LOST
        assert ctrlr._game.board[coord] is CellContents.HitMine(2)

        # Test first success on a high density board - no room for opening.
        opts = GameOptsStruct(
            x_size=4, y_size=4, mines=15, per_cell=1, first_success=True
        )
        ctrlr = GameController(opts)
        coord = (1, 2)
        ctrlr.select_cell(coord)
        assert ctrlr._game.board[coord] is CellContents.Num(8)

        # Test first success turned off - should hit a mine with high density.
        opts.first_success = False
        passed = False
        attempts = 0
        while not passed:
            ctrlr = GameController(opts)
            ctrlr.select_cell(coord)
            attempts += 1
            try:
                assert ctrlr._game.board[coord] is CellContents.HitMine(1)
                passed = True
            except AssertionError:
                if attempts >= 10:
                    raise

    def test_losing(self):
        # Lose straight away.
        ctrlr = self.create_controller()
        ctrlr.select_cell((3, 0))
        assert ctrlr._game.state is GameState.LOST
        assert ctrlr._game.end_time is not None
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#", "#",  "M1", "!2"],
                ["#", "#",  "#",  "M1"],
                ["#", "#",  "#",  "#" ],
                ["#", "#",  "#",  "#" ],
                ["#", "M1", "#",  "#" ],
                # fmt: on
            ]
        )

        # Lose after game has been started with incorrect flag.
        ctrlr = self.create_controller()
        ctrlr.select_cell((1, 0))
        ctrlr.flag_cell((1, 1))
        ctrlr.select_cell((2, 0))
        assert ctrlr._game.state is GameState.LOST
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#",  1,   "!1", "M2"],
                ["#", "X1", "#",  "M1"],
                ["#", "#",  "#",  "#" ],
                ["#", "#",  "#",  "#" ],
                ["#", "M1", "#",  "#" ],
                # fmt: on
            ]
        )

        # Check cells can't be selected when the game is lost.
        for c in ctrlr._game.board.all_coords:
            ctrlr.select_cell(c)
            ctrlr.flag_cell(c)
            ctrlr.chord_on_cell(c)
            ctrlr.remove_cell_flags(c)
        assert ctrlr._game.state is GameState.LOST

        # Check losing via chording works.
        ctrlr = self.create_controller()
        ctrlr.select_cell((1, 0))
        ctrlr.flag_cell((1, 1))
        ctrlr.chord_on_cell((1, 0))
        assert ctrlr._game.state is GameState.LOST
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                [ 0,   1,   "!1", "M2"],
                [ 0,  "X1",  4,   "M1"],
                [ 0,   0,    1,   "#" ],
                [ 1,   1,    1,   "#" ],
                ["#", "M1", "#",  "#" ],
                # fmt: on
            ]
        )

    def test_winning(self):
        # Test winning in one click.
        opts = GameOptsStruct(x_size=2, y_size=1, mines=1, first_success=True)
        ctrlr = self.create_controller(opts=opts, set_mf=False)
        ctrlr.select_cell((0, 0))
        assert ctrlr._game.state is GameState.WON
        assert ctrlr._game.end_time is not None
        assert ctrlr._game.mines_remaining == 0
        assert ctrlr._game.board == ctrlr._game.mf.completed_board

        # Check winning via chording and hitting an opening works.
        ctrlr = self.create_controller()
        ctrlr.select_cell((0, 0))
        ctrlr.select_cell((0, 4))
        ctrlr.flag_cell((3, 1))
        ctrlr.chord_on_cell((2, 2))
        assert ctrlr._game.state is GameState.WON
        assert (
            ctrlr._game.board
            == ctrlr._game.mf.completed_board
            == Board.from_2d_array(
                [
                    # fmt: off
                    [0,  1,  "F1", "F2"],
                    [0,  1,   4,   "F1"],
                    [0,  0,   1,    1  ],
                    [1,  1,   1,    0  ],
                    [1, "F1", 1,    0  ],
                    # fmt: on
                ]
            )
        )

        # Check cells can't be selected when the game is won.
        for c in ctrlr._game.board.all_coords:
            ctrlr.select_cell(c)
            ctrlr.flag_cell(c)
            ctrlr.chord_on_cell(c)
            ctrlr.remove_cell_flags(c)
        assert ctrlr._game.state is GameState.WON

    def test_new_game(self):
        """Test starting new games."""
        # Start a new game before doing anything else with minefield.
        ctrlr = self.create_controller()
        ctrlr.new_game()
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert not ctrlr._game.mf

        # Start a new game that isn't started but has flags.
        ctrlr = self.create_controller()
        ctrlr.flag_cell((0, 0))
        ctrlr.flag_cell((1, 0))
        ctrlr.flag_cell((1, 0))
        assert ctrlr._game.board != Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        ctrlr.new_game()
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)

        # Start a new game mid-game.
        ctrlr = self.create_controller()
        ctrlr.select_cell((0, 0))
        ctrlr.select_cell((0, 1))
        assert ctrlr._game.state is GameState.ACTIVE
        assert ctrlr._game.mf
        assert ctrlr._game.board != Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        ctrlr.new_game()
        assert ctrlr._game.state is GameState.READY
        assert not ctrlr._game.mf
        assert ctrlr._game.start_time is None
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)

        # Start a new game on lost game.
        ctrlr = self.create_controller()
        ctrlr._game.mf = self.mf
        ctrlr.select_cell((3, 0))
        assert ctrlr._game.state is GameState.LOST
        assert ctrlr._game.mf
        assert ctrlr._game.board != Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        ctrlr.new_game()
        assert ctrlr._game.state is GameState.READY
        assert not ctrlr._game.mf
        assert ctrlr._game.start_time is ctrlr._game.end_time is None
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)

    def test_restart_game(self):
        # Only require a single controller.
        ctrlr = self.create_controller(set_mf=False)

        # Replay before doing anything else, without minefield.
        ctrlr.restart_game()
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert not ctrlr._game.mf

        # Replay before doing anything else, with minefield.
        ctrlr._game.mf = self.mf
        ctrlr.restart_game()
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr._game.mf == self.mf

        # Restart a game that isn't started but has flags.
        ctrlr.flag_cell((0, 0))
        ctrlr.flag_cell((1, 0))
        ctrlr.flag_cell((1, 0))
        ctrlr.restart_game()
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr._game.mf == self.mf

        # Restart game mid-game.
        ctrlr.select_cell((0, 0))
        assert ctrlr._game.state is GameState.ACTIVE
        ctrlr.restart_game()
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.start_time is None
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr._game.mf == self.mf

        # Restart finished game (lost game).
        ctrlr.select_cell((3, 0))
        assert ctrlr._game.state is GameState.LOST
        ctrlr.restart_game()
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.start_time is ctrlr._game.end_time is None
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines
        assert ctrlr._game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr._game.mf == self.mf

    def test_resize_board(self):
        # Setup, including start a game.
        opts = self.opts.copy()
        ctrlr = self.create_controller(opts=opts)
        ctrlr.select_cell((0, 0))
        ctrlr.flag_cell((2, 0))
        assert ctrlr._game.state is not GameState.READY
        assert ctrlr._game.mines_remaining == opts.mines - 1

        # Normal resize.
        opts.x_size, opts.y_size, opts.mines = 10, 2, 3
        ctrlr.resize_board(x_size=opts.x_size, y_size=opts.y_size, mines=opts.mines)
        assert ctrlr._opts == opts
        assert ctrlr._game.state is GameState.READY
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines
        assert not ctrlr._game.mf
        assert ctrlr._game.board == Board(opts.x_size, opts.y_size)

        # Resize without changing values starts new game.
        ctrlr.select_cell((0, 0))
        assert ctrlr._game.state is not GameState.READY
        ctrlr.resize_board(x_size=opts.x_size, y_size=opts.y_size, mines=opts.mines)
        assert ctrlr._game.state is GameState.READY
        assert not ctrlr._game.mf
        assert ctrlr._game.board == Board(opts.x_size, opts.y_size)

    def test_lives(self):
        opts = self.opts.copy()
        opts.lives = 3
        ctrlr = self.create_controller(opts=opts)

        # Lose first life on single mine.
        ctrlr.select_cell((2, 0))
        assert ctrlr._game.state is GameState.ACTIVE
        assert ctrlr._game.lives_remaining == 2
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines - 1
        assert ctrlr._game.end_time is None
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#", "#", "!1", "#"],
                ["#", "#",  "#", "#"],
                ["#", "#",  "#", "#"],
                ["#", "#",  "#", "#"],
                ["#", "#",  "#", "#"],
                # fmt: on
            ]
        )

        # Lose second life on double mine.
        ctrlr.select_cell((3, 0))
        assert ctrlr._game.state is GameState.ACTIVE
        assert ctrlr._game.lives_remaining == 1
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines - 3
        assert ctrlr._game.end_time is None
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#", "#", "!1", "!2"],
                ["#", "#", "#",  "#" ],
                ["#", "#", "#",  "#" ],
                ["#", "#", "#",  "#" ],
                ["#", "#", "#",  "#" ],
                # fmt: on
            ]
        )

        # Lose final life.
        ctrlr.select_cell((3, 1))
        assert ctrlr._game.state is GameState.LOST
        assert ctrlr._game.lives_remaining == 0
        assert ctrlr._game.mines_remaining == ctrlr._opts.mines - 3  # unchanged
        assert ctrlr._game.end_time is not None
        assert ctrlr._game.board == Board.from_2d_array(
            [
                # fmt: off
                ["#", "#",  "!1", "!2"],
                ["#", "#",  "#",  "!1"],
                ["#", "#",  "#",  "#" ],
                ["#", "#",  "#",  "#" ],
                ["#", "M1", "#",  "#" ],
                # fmt: on
            ]
        )

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    @classmethod
    def create_controller(cls, *, opts=None, set_mf=True, listener=None):
        """
        Convenience method for creating a controller instance. Uses the test
        class options and minefield by default, and registers a listener if one
        is given.

        Arguments:
        opts=None
            Optionally override the default options.
        set_mf=True
            Whether to set the minefield or leave it not being created.
        listener=None
            Optionally specify a listener to register.
        """
        if opts is None:
            opts = cls.opts
        ctrlr = GameController(opts)
        if set_mf:
            ctrlr._game.mf = cls.mf
        if listener:
            ctrlr.register_listener(listener)
        return ctrlr

    @staticmethod
    def check_and_reset_callback(cb, **kwargs):
        """
        Assert that a callback was called exactly once, and with information
        matching whatever is passed in to this method.
        """
        cb.assert_called_once()
        passed_info = cb.call_args[0][0]
        for key, value in kwargs.items():
            if key == "cell_updates":
                logger.warning("Skipping check on cell updates")
                continue
            assert getattr(passed_info, key) == value

        cb.reset_mock()
