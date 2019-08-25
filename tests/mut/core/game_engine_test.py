"""
game_engine_test.py - Test the game engine module

October 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k game_engine_test]' from
the root directory.
"""

import logging
from unittest import mock
from unittest.mock import Mock

import pytest

from minegauler.core import game
from minegauler.core.board import Board
from minegauler.core.game import ignore_if, ignore_if_not
from minegauler.core.game_engine import Controller, GameOptsStruct
from minegauler.core.internal_types import *
from minegauler.core.minefield import Minefield


logger = logging.getLogger(__name__)


@pytest.fixture()
def frontend1():
    return Mock()


@pytest.fixture()
def frontend2():
    return Mock()


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
    # -------------------------------------------------------------------------
    def test_create(self):
        # Normal create of a controller.
        ctrlr = Controller(self.opts)
        assert ctrlr.opts == self.opts
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mf is None
        assert ctrlr.game.board == Board(self.opts.x_size, self.opts.y_size)

        # Try creating a controller with invalid options.
        with pytest.raises(ValueError):
            Controller("INVALID")

    def test_register_callbacks(self, frontend1, frontend2):
        # Register two valid callback functions.
        ctrlr = self.create_controller()
        ctrlr.register_callback(lambda x: None)
        ctrlr.register_callback(lambda x, y=None: None)
        assert len(ctrlr._registered_callbacks) == 2

        # Register an invalid callback - not callable.
        ctrlr = self.create_controller()
        ctrlr.register_callback("NOT CALLABLE")
        # @@@LG Check an error is logged.
        assert len(ctrlr._registered_callbacks) == 0

        # Register an invalid callback - doesn't take a positional argument.
        ctrlr = self.create_controller()
        ctrlr.register_callback(lambda: None)
        # @@@LG Check an error is logged.
        assert len(ctrlr._registered_callbacks) == 0

        # Register an invalid callback - expects too many positional arguments.
        ctrlr = self.create_controller()
        ctrlr.register_callback(lambda x, y: None)
        # @@@LG Check an error is logged.
        assert len(ctrlr._registered_callbacks) == 0

        # Register a callback that can't be inspected.
        ctrlr = self.create_controller()
        ctrlr.register_callback(min)
        # @@@LG Check a warning is logged.
        assert len(ctrlr._registered_callbacks) == 1

        # Check callbacks are called.
        ctrlr = self.create_controller()
        ctrlr._next_update = "dummy"
        ctrlr._registered_callbacks = [frontend1, frontend2]
        ctrlr._send_callback_updates()
        for cb in ctrlr._registered_callbacks:
            cb.assert_called_once()
            cb.reset_mock()

        # Check an error is logged when a callback raises an error.
        frontend1.side_effect = Exception
        ctrlr._next_update = "dummy"
        ctrlr._send_callback_updates()
        # @@@LG Check error is logged.
        for cb in ctrlr._registered_callbacks:
            cb.assert_called_once()
            cb.reset_mock()

    def test_cell_interaction(self, frontend1):
        coord = (2, 2)

        # Setup.
        opts = GameOptsStruct(per_cell=2, first_success=False)
        ctrlr = self.create_controller(opts=opts, set_mf=False, cb=frontend1)
        frontend1.assert_not_called()

        # Flag a cell.
        ctrlr.flag_cell(coord)
        assert ctrlr.game.board[coord] == CellFlag(1)
        assert not ctrlr.game.mf
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines - 1
        self.check_and_reset_callback(
            frontend1,
            cell_updates=self.get_cell_states([coord], ctrlr),
            mines_remaining=ctrlr.game.mines_remaining,
        )

        # Select a flagged cell.
        ctrlr.select_cell(coord)
        assert ctrlr.game.board[coord] == CellFlag(1)
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines - 1
        # frontend1.assert_not_called()  # TODO
        frontend1.reset_mock()  # TODO

        # Flag a cell that is already flagged (multiple mines per cell).
        ctrlr.flag_cell(coord)
        assert ctrlr.game.board[coord] == CellFlag(2)
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines - 2
        self.check_and_reset_callback(
            frontend1,
            cell_updates=self.get_cell_states([coord], ctrlr),
            mines_remaining=ctrlr.game.mines_remaining,
        )

        # Flag a cell that is at max flags to reset it.
        ctrlr.flag_cell(coord)
        assert ctrlr.game.board[coord] == CellUnclicked()
        assert not ctrlr.game.mf
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        self.check_and_reset_callback(
            frontend1,
            cell_updates=self.get_cell_states([coord], ctrlr),
            mines_remaining=ctrlr.game.mines_remaining,
        )

        # Remove cell flags.
        ctrlr.flag_cell(coord)
        frontend1.reset_mock()
        ctrlr.remove_cell_flags(coord)
        assert ctrlr.game.board[coord] == CellUnclicked()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        self.check_and_reset_callback(
            frontend1,
            cell_updates=self.get_cell_states([coord], ctrlr),
            mines_remaining=ctrlr.game.mines_remaining,
        )

        # Select a cell to start the game.
        ctrlr.select_cell(coord)
        assert isinstance(ctrlr.game.board[coord], (CellHitMine, CellNum))
        assert ctrlr.game.mf
        assert ctrlr.game.state in {GameState.ACTIVE, GameState.LOST}
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        self.check_and_reset_callback(frontend1, game_state=ctrlr.game.state)

        # Select an already-selected cell.
        revealed = ctrlr.game.board[coord]
        ctrlr.select_cell(coord)
        assert ctrlr.game.board[coord] == revealed
        # frontend1.assert_not_called()  # TODO

    def test_select_opening(self, frontend1):
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
        ctrlr = self.create_controller(cb=frontend1)
        ctrlr.select_cell((0, 0))
        assert ctrlr.game.board == exp_board
        self.check_and_reset_callback(frontend1, game_state=GameState.ACTIVE)

        # Select the edge of an opening.
        ctrlr = self.create_controller()
        ctrlr.select_cell((1, 3))
        assert ctrlr.game.board == Board.from_2d_array(
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
        assert ctrlr.game.board == exp_board

        # Select another cell to trigger the other opening.
        ctrlr.select_cell((3, 4))
        assert ctrlr.game.board == Board.from_2d_array(
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
        assert ctrlr.game.board == Board.from_2d_array(
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
        assert ctrlr.game.board == Board.from_2d_array(
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
        assert ctrlr.game.board == Board.from_2d_array(
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

    def test_chording(self, frontend1):
        # Use the same controller throughout the test.

        # No-op chording - game not started.
        ctrlr = self.create_controller(cb=frontend1)
        ctrlr.chord_on_cell((0, 0))
        assert ctrlr.game.state == GameState.READY
        # frontend1.assert_not_called()  # TODO

        # No-op chording - no flags.
        ctrlr.select_cell((0, 4))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((0, 4))
        assert ctrlr.game.board == Board.from_2d_array(
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
        # frontend1.assert_not_called()  # TODO

        # Basic successful chording.
        ctrlr.flag_cell((1, 4))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((0, 4))
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(
            frontend1, cell_updates={c: CellNum(1) for c in [(0, 3), (1, 3)]}
        )

        # Successful chording triggering opening.
        ctrlr.chord_on_cell((1, 3))
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(frontend1)

        # No-op - repeated chording.
        prev_board = ctrlr.game.board
        ctrlr.chord_on_cell((1, 3))
        assert ctrlr.game.board == prev_board
        # frontend1.assert_not_called()  # TODO

        # No-op - chording on flagged cell.
        ctrlr.chord_on_cell((1, 4))
        assert ctrlr.game.board == prev_board
        # frontend1.assert_not_called()  # TODO

        # No-op - wrong number of flags.
        ctrlr.flag_cell((3, 0))
        ctrlr.flag_cell((3, 0))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((2, 1))
        # frontend1.assert_not_called()  # TODO

        # Incorrect flags cause hitting a mine.
        ctrlr.flag_cell((3, 2))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((2, 2))
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(frontend1, game_state=GameState.LOST)

    def test_first_success(self):
        # First click should hit an opening with first_success set.
        opts = GameOptsStruct(first_success=True)
        ctrlr = Controller(opts)
        coord = (1, 5)
        ctrlr.select_cell(coord)
        assert ctrlr.game.state == GameState.ACTIVE
        assert ctrlr.game.board[coord] == CellNum(0)
        for c in ctrlr.game.board.get_nbrs(coord):
            assert type(ctrlr.game.board[c]) == CellNum

        # Check first success is ignored when using created minefield.
        ctrlr = self.create_controller()
        coord = (3, 0)
        ctrlr.select_cell(coord)
        assert ctrlr.game.state == GameState.LOST
        assert ctrlr.game.board[coord] == CellHitMine(2)

        # Test first success on a high density board - no room for opening.
        opts = GameOptsStruct(
            x_size=4, y_size=4, mines=15, per_cell=1, first_success=True
        )
        ctrlr = Controller(opts)
        coord = (1, 2)
        ctrlr.select_cell(coord)
        assert ctrlr.game.board[coord] == CellNum(8)

        # Test first success turned off - should hit a mine with high density.
        opts.first_success = False
        passed = False
        attempts = 0
        while not passed:
            ctrlr = Controller(opts)
            ctrlr.select_cell(coord)
            attempts += 1
            if attempts >= 10:
                assert ctrlr.game.board[coord] == CellHitMine(1)
            elif ctrlr.game.board[coord] == CellHitMine(1):
                passed = True

    def test_losing(self, frontend1):
        # Lose straight away.
        ctrlr = self.create_controller(cb=frontend1)
        ctrlr.select_cell((3, 0))
        assert ctrlr.game.state == GameState.LOST
        assert ctrlr.game.end_time is not None
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(
            frontend1,
            cell_updates={
                (2, 0): CellMine(1),
                (3, 0): CellHitMine(2),
                (3, 1): CellMine(1),
                (1, 4): CellMine(1),
            },
            game_state=GameState.LOST,
            lives_remaining=0,
            elapsed_time=ctrlr.game.end_time - ctrlr.game.start_time,
        )

        # Lose after game has been started with incorrect flag.
        ctrlr = self.create_controller(cb=frontend1)
        ctrlr.select_cell((1, 0))
        ctrlr.flag_cell((1, 1))
        frontend1.reset_mock()
        ctrlr.select_cell((2, 0))
        assert ctrlr.game.state == GameState.LOST
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(frontend1)

        # Check cells can't be selected when the game is lost.
        for c in ctrlr.game.board.all_coords:
            ctrlr.select_cell(c)
            ctrlr.flag_cell(c)
            ctrlr.chord_on_cell(c)
            ctrlr.remove_cell_flags(c)
        assert ctrlr.game.state == GameState.LOST
        # frontend1.assert_not_called()  # TODO

        # Check losing via chording works.
        ctrlr = self.create_controller()
        ctrlr.select_cell((1, 0))
        ctrlr.flag_cell((1, 1))
        ctrlr.chord_on_cell((1, 0))
        assert ctrlr.game.state == GameState.LOST
        assert ctrlr.game.board == Board.from_2d_array(
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

    def test_winning(self, frontend1):
        # Test winning in one click.
        opts = GameOptsStruct(x_size=2, y_size=1, mines=1, first_success=True)
        ctrlr = self.create_controller(opts=opts, set_mf=False, cb=frontend1)
        ctrlr.select_cell((0, 0))
        assert ctrlr.game.state == GameState.WON
        assert ctrlr.game.end_time is not None
        assert ctrlr.game.mines_remaining == 0
        assert ctrlr.game.board == ctrlr.game.mf.completed_board
        self.check_and_reset_callback(
            frontend1,
            cell_updates={(0, 0): CellNum(1), (1, 0): CellFlag(1)},
            game_state=GameState.WON,
            mines_remaining=0,
            lives_remaining=ctrlr.game.lives_remaining,
            elapsed_time=ctrlr.game.end_time - ctrlr.game.start_time,
        )

        # Check winning via chording and hitting an opening works.
        ctrlr = self.create_controller()
        ctrlr.select_cell((0, 0))
        ctrlr.select_cell((0, 4))
        ctrlr.flag_cell((3, 1))
        ctrlr.chord_on_cell((2, 2))
        assert ctrlr.game.state == GameState.WON
        assert (
            ctrlr.game.board
            == ctrlr.game.mf.completed_board
            == Board.from_2d_array(
                [
                    # fmt: off
                    [0, 1, "F1", "F2"],
                    [0, 1, 4, "F1"],
                    [0, 0, 1, 1],
                    [1, 1, 1, 0],
                    [1, "F1", 1, 0],
                    # fmt: on
                ]
            )
        )

        # Check cells can't be selected when the game is won.
        for c in ctrlr.game.board.all_coords:
            ctrlr.select_cell(c)
            ctrlr.flag_cell(c)
            ctrlr.chord_on_cell(c)
            ctrlr.remove_cell_flags(c)
        assert ctrlr.game.state == GameState.WON
        # frontend1.assert_not_called()  # TODO

    def test_new_game(self, frontend1):
        # Only require a single controller when able to create new games.
        ctrlr = self.create_controller(cb=frontend1)

        # Start a new game before doing anything else with minefield.
        ctrlr.new_game()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert not ctrlr.game.mf

        # Start a new game that isn't started but has flags.
        ctrlr.flag_cell((0, 0))
        ctrlr.flag_cell((1, 0))
        ctrlr.flag_cell((1, 0))
        assert ctrlr.game.board != Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        frontend1.reset_mock()
        ctrlr.new_game()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        self.check_and_reset_callback(
            frontend1,
            cell_updates={c: CellUnclicked() for c in {(0, 0), (1, 0)}},
            mines_remaining=ctrlr.opts.mines,
        )

        # Start a new game mid-game.
        ctrlr.select_cell((0, 0))
        ctrlr.select_cell((0, 1))
        assert ctrlr.game.state == GameState.ACTIVE
        assert ctrlr.game.mf
        assert ctrlr.game.board != Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        frontend1.reset_mock()
        ctrlr.new_game()
        assert ctrlr.game.state == GameState.READY
        assert not ctrlr.game.mf
        assert ctrlr.game.start_time is None
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        self.check_and_reset_callback(frontend1)

        # Start a new game on lost game.
        ctrlr.game.mf = self.mf
        ctrlr.select_cell((3, 0))
        assert ctrlr.game.state == GameState.LOST
        assert ctrlr.game.mf
        assert ctrlr.game.board != Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        frontend1.reset_mock()
        ctrlr.new_game()
        assert ctrlr.game.state == GameState.READY
        assert not ctrlr.game.mf
        assert ctrlr.game.start_time is ctrlr.game.end_time is None
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        self.check_and_reset_callback(
            frontend1,
            cell_updates={
                c: CellUnclicked()
                for c in ctrlr.game.board.all_coords
                if self.mf.cell_contains_mine(c)
            },
        )

    def test_restart_game(self, frontend1):
        # Only require a single controller.
        ctrlr = self.create_controller(set_mf=False, cb=frontend1)

        # Replay before doing anything else, without minefield.
        ctrlr.restart_game()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert not ctrlr.game.mf

        # Replay before doing anything else, with minefield.
        ctrlr.game.mf = self.mf
        ctrlr.restart_game()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert ctrlr.game.mf == self.mf

        # Restart a game that isn't started but has flags.
        ctrlr.flag_cell((0, 0))
        ctrlr.flag_cell((1, 0))
        ctrlr.flag_cell((1, 0))
        frontend1.reset_mock()
        ctrlr.restart_game()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert ctrlr.game.mf == self.mf
        self.check_and_reset_callback(
            frontend1,
            cell_updates={c: CellUnclicked() for c in {(0, 0), (1, 0)}},
            mines_remaining=ctrlr.opts.mines,
        )

        # Restart game mid-game.
        ctrlr.select_cell((0, 0))
        assert ctrlr.game.state == GameState.ACTIVE
        frontend1.reset_mock()
        opened_cells = {
            c
            for c in ctrlr.game.mf.all_coords
            if ctrlr.game.board[c] != CellUnclicked()
        }
        ctrlr.restart_game()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.start_time is None
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert ctrlr.game.mf == self.mf
        self.check_and_reset_callback(
            frontend1,
            cell_updates={c: CellUnclicked() for c in opened_cells},
            game_state=GameState.READY,
        )

        # Restart finished game (lost game).
        ctrlr.select_cell((3, 0))
        assert ctrlr.game.state == GameState.LOST
        frontend1.reset_mock()
        ctrlr.restart_game()
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.start_time is ctrlr.game.end_time is None
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        assert ctrlr.game.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert ctrlr.game.mf == self.mf
        self.check_and_reset_callback(frontend1)

    def test_resize_board(self):
        # Setup, including start a game.
        opts = self.opts.copy()
        ctrlr = self.create_controller(opts=opts)
        ctrlr.select_cell((0, 0))
        ctrlr.flag_cell((2, 0))
        assert ctrlr.game.state == GameState.ACTIVE
        assert ctrlr.game.mines_remaining == opts.mines - 1

        # Normal resize.
        opts.x_size, opts.y_size, opts.mines = 10, 2, 3
        ctrlr.resize_board(x_size=opts.x_size, y_size=opts.y_size, mines=opts.mines)
        assert ctrlr.opts == opts
        assert ctrlr.game.state == GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines
        assert not ctrlr.game.mf
        assert ctrlr.game.board == Board(opts.x_size, opts.y_size)

        # Resize without changing values starts new game.
        ctrlr.select_cell((0, 0))
        assert ctrlr.game.state == GameState.ACTIVE
        ctrlr.resize_board(x_size=opts.x_size, y_size=opts.y_size, mines=opts.mines)
        assert ctrlr.game.state == GameState.READY
        assert not ctrlr.game.mf
        assert ctrlr.game.board == Board(opts.x_size, opts.y_size)

    def test_lives(self, frontend1):
        opts = self.opts.copy()
        opts.lives = 3
        ctrlr = self.create_controller(opts=opts, cb=frontend1)

        # Lose first life on single mine.
        ctrlr.select_cell((2, 0))
        assert ctrlr.game.state == GameState.ACTIVE
        assert ctrlr.game.lives_remaining == 2
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines - 1
        assert ctrlr.game.end_time is None
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(
            frontend1,
            cell_updates={(2, 0): CellHitMine(1)},
            game_state=GameState.ACTIVE,
            lives_remaining=ctrlr.game.lives_remaining,
            mines_remaining=ctrlr.game.mines_remaining,
        )

        # Lose second life on double mine.
        ctrlr.select_cell((3, 0))
        assert ctrlr.game.state == GameState.ACTIVE
        assert ctrlr.game.lives_remaining == 1
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines - 3
        assert ctrlr.game.end_time is None
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(
            frontend1,
            cell_updates={(3, 0): CellHitMine(2)},
            game_state=ctrlr.game.state,
            lives_remaining=ctrlr.game.lives_remaining,
            mines_remaining=ctrlr.game.mines_remaining,
        )

        # Lose final life.
        ctrlr.select_cell((3, 1))
        assert ctrlr.game.state == GameState.LOST
        assert ctrlr.game.lives_remaining == 0
        assert ctrlr.game.mines_remaining == ctrlr.opts.mines - 3  # unchanged
        assert ctrlr.game.end_time is not None
        assert ctrlr.game.board == Board.from_2d_array(
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
        self.check_and_reset_callback(
            frontend1,
            cell_updates={(3, 1): CellHitMine(1), (1, 4): CellMine(1)},
            game_state=GameState.LOST,
            lives_remaining=0,
            mines_remaining=ctrlr.game.mines_remaining,
        )

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    @classmethod
    def create_controller(cls, *, opts=None, set_mf=True, cb=None):
        """
        Convenience method for creating a controller instance. Uses the test
        class options and minefield by default, and registers a callback if one
        is given.

        Arguments:
        opts=None
            Optionally override the default options.
        set_mf=True
            Whether to set the minefield or leave it not being created.
        cb=None
            Optionally specify a callback to register.
        """
        if opts is None:
            opts = cls.opts
        ctrlr = Controller(opts)
        if set_mf:
            ctrlr.game.mf = cls.mf
        if cb:
            ctrlr._registered_callbacks = [cb]

        return ctrlr

    @staticmethod
    def get_cell_states(coords, ctrlr):
        return {c: ctrlr.game.board[c] for c in coords}

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
