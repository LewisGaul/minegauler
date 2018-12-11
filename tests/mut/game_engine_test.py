"""
game_engine_test.py - Test the game engine module

October 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k game_engine_test]' from
the root directory.
"""


import pytest
from unittest.mock import Mock

from minegauler.backend.game_engine import Controller, GameOptsStruct
from minegauler.backend.minefield import Minefield
from minegauler.backend.utils import Board
from minegauler.shared.internal_types import *


@pytest.fixture()
def frontend1():
    return Mock()

@pytest.fixture()
def frontend2():
    return Mock()


def assert_reset_call_count(mock, count):
    """
    Assert the value of a call count on a mock and reset the mock.
    """
    assert mock.call_count == count
    mock.reset_mock()



class TestController:

    mf = Minefield.from_2d_array([
        [0, 0, 1, 2],
        [0, 0, 0, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 1, 0, 0],
    ])
    opts = GameOptsStruct(x_size=mf.x_size, y_size=mf.y_size, mines=mf.mines,
                          per_cell=mf.per_cell, first_success=True)

    # --------------------------------------------------------------------------
    # Test cases
    # -------------------------------------------------------------------------
    def test_create(self):
        # Create a controller.
        ctrlr = Controller(self.opts)
        assert ctrlr.game_state == GameState.READY
        assert ctrlr.opts == self.opts
        for opt in ['x_size', 'y_size', 'mines', 'per_cell']:
            assert getattr(ctrlr.mf, opt) == getattr(self.opts, opt)
        assert not ctrlr.mf.is_created
        assert ctrlr.board == Board(self.opts.x_size, self.opts.y_size)

    def test_register_callbacks(self, frontend1, frontend2):
        ctrlr = Controller(self.opts)
        for cb in [frontend1, frontend2]:
            ctrlr.register_callback(cb)
        assert len(ctrlr._registered_callbacks) == 2
        ctrlr._cell_updates = 'dummy'
        ctrlr._send_callback_updates()
        for cb in [frontend1, frontend2]:
            assert cb.call_count == 1

    def test_cell_interaction(self, frontend1):
        # Setup.
        opts = GameOptsStruct(per_cell=2, first_success=False)
        ctrlr = Controller(opts)
        ctrlr.register_callback(frontend1)
        assert_reset_call_count(frontend1, 0)

        coord = (2, 2)
        # Flag a cell.
        ctrlr.flag_cell(coord)
        assert ctrlr.board[coord] == CellFlag(1)
        assert not ctrlr.mf.is_created
        assert ctrlr.game_state == GameState.READY
        assert_reset_call_count(frontend1, 1)

        # Select a flagged cell.
        ctrlr.select_cell(coord)
        assert ctrlr.board[coord] == CellFlag(1)
        assert_reset_call_count(frontend1, 0)

        # Flag a cell that is already flagged (multiple mines per cell).
        ctrlr.flag_cell(coord)
        assert ctrlr.board[coord] == CellFlag(2)
        assert_reset_call_count(frontend1, 1)

        # Flag a cell that is at max flags to reset it.
        ctrlr.flag_cell(coord)
        assert ctrlr.board[coord] == CellUnclicked()
        assert not ctrlr.mf.is_created
        assert ctrlr.game_state == GameState.READY
        assert_reset_call_count(frontend1, 1)

        # Remove cell flags.
        ctrlr.flag_cell(coord)
        ctrlr.remove_cell_flags(coord)
        assert ctrlr.board[coord] == CellUnclicked()
        assert_reset_call_count(frontend1, 2)

        # Select a cell to start the game.
        ctrlr.select_cell(coord)
        assert isinstance(ctrlr.board[coord], (CellHit, CellNum))
        assert ctrlr.mf.is_created
        assert ctrlr.game_state in {GameState.ACTIVE, GameState.LOST}
        assert_reset_call_count(frontend1, 1)

        # Select an already-selected cell.
        revealed = ctrlr.board[coord]
        ctrlr.select_cell(coord)
        assert ctrlr.board[coord] == revealed
        assert_reset_call_count(frontend1, 0)

    def test_select_opening(self, frontend1):
        exp_board = Board.from_2d_array([
            [ 0 ,  1 , '#', '#'],
            [ 0 ,  1 ,  4 , '#'],
            [ 0 ,  0 ,  1 , '#'],
            [ 1 ,  1 ,  1 , '#'],
            ['#', '#', '#', '#'],
        ])
        # Select a cell to trigger the opening.
        ctrlr = Controller(self.opts)
        ctrlr.register_callback(frontend1)
        ctrlr.mf = self.mf
        ctrlr.select_cell((0, 0))
        assert ctrlr.board == exp_board
        assert_reset_call_count(frontend1, 1)

        # Select the edge of an opening.
        ctrlr = Controller(self.opts)
        ctrlr.mf = self.mf
        ctrlr.select_cell((1, 3))
        assert ctrlr.board ==  Board.from_2d_array([
            ['#', '#', '#', '#'],
            ['#', '#', '#', '#'],
            ['#', '#', '#', '#'],
            ['#',  1 , '#', '#'],
            ['#', '#', '#', '#'],
        ])

        # Select a different cell to trigger the same opening as above.
        ctrlr.select_cell((1, 2))
        assert ctrlr.board == exp_board

        # Select another cell to trigger the other opening.
        ctrlr.select_cell((3, 4))
        assert ctrlr.board ==  Board.from_2d_array([
            [ 0,   1 , '#', '#'],
            [ 0,   1 ,  4 , '#'],
            [ 0,   0 ,  1 ,  1 ],
            [ 1,   1 ,  1 ,  0 ],
            ['#', '#',  1 ,  0 ],
        ])

        # Trigger opening with incorrect flag blocking the way.
        ctrlr = Controller(self.opts)
        ctrlr.mf = self.mf
        ctrlr.flag_cell((0, 1))
        ctrlr.select_cell((0, 0))
        assert ctrlr.board == Board.from_2d_array([
            [  0 ,  1 , '#', '#'],
            ['F1',  1 , '#', '#'],
            [ '#', '#', '#', '#'],
            [ '#', '#', '#', '#'],
            [ '#', '#', '#', '#'],
        ])

        # Select doesn't trigger remainder of opening on revealed opening.
        ctrlr.remove_cell_flags((0, 1))
        ctrlr.select_cell((0, 0))
        assert ctrlr.board == Board.from_2d_array([
            [ 0 ,  1 , '#', '#'],
            ['#',  1 , '#', '#'],
            ['#', '#', '#', '#'],
            ['#', '#', '#', '#'],
            ['#', '#', '#', '#'],
        ])

        # Chording does trigger remainder of opening on revealed opening.
        # Also test other invalid flags blocking the opening.
        ctrlr.flag_cell((0, 3))
        ctrlr.flag_cell((0, 2))
        ctrlr.chord_on_cell((0, 0))
        assert ctrlr.board == Board.from_2d_array([
            [  0 ,  1 , '#', '#'],
            [  0 ,  1 ,  4 , '#'],
            ['F1',  0 ,  1 , '#'],
            ['F1',  1 ,  1 , '#'],
            [ '#', '#', '#', '#'],
        ])

    def test_chording(self, frontend1):
        """Use the same controller throughout the test."""

        # No-op chording - game not started.
        ctrlr = Controller(self.opts)
        ctrlr.register_callback(frontend1)
        ctrlr.mf = self.mf
        ctrlr.chord_on_cell((0, 0))
        assert ctrlr.game_state == GameState.READY
        assert_reset_call_count(frontend1, 0)

        # No-op chording - no flags.
        ctrlr.select_cell((0, 4))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((0, 4))
        assert_reset_call_count(frontend1, 0)
        assert ctrlr.board ==  Board.from_2d_array([
            ['#', '#', '#', '#'],
            ['#', '#', '#', '#'],
            ['#', '#', '#', '#'],
            ['#', '#', '#', '#'],
            [ 1,  '#', '#', '#'],
        ])

        # Basic successful chording.
        ctrlr.flag_cell((1, 4))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((0, 4))
        assert_reset_call_count(frontend1, 1)
        assert ctrlr.board ==  Board.from_2d_array([
            ['#',  '#', '#', '#'],
            ['#',  '#', '#', '#'],
            ['#',  '#', '#', '#'],
            [ 1 ,   1 , '#', '#'],
            [ 1 , 'F1', '#', '#'],
        ])

        # Successful chording triggering opening.
        ctrlr.chord_on_cell((1, 3))
        assert_reset_call_count(frontend1, 1)
        assert ctrlr.board ==  Board.from_2d_array([
            [ 0,   1 , '#', '#'],
            [ 0,   1 ,  4 , '#'],
            [ 0,   0 ,  1 , '#'],
            [ 1,   1 ,  1 , '#'],
            [ 1, 'F1',  1 , '#'],
        ])

        # No-op - repeated chording.
        prev_board = ctrlr.board
        ctrlr.chord_on_cell((1, 3))
        assert_reset_call_count(frontend1, 0)
        assert ctrlr.board == prev_board

        # No-op - chording on flagged cell.
        ctrlr.chord_on_cell((1, 4))
        assert_reset_call_count(frontend1, 0)
        assert ctrlr.board == prev_board

        # No-op - wrong number of flags.
        ctrlr.flag_cell((3, 0))
        ctrlr.flag_cell((3, 0))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((2, 1))
        assert_reset_call_count(frontend1, 0)

        # Incorrect flags cause hitting a mine.
        ctrlr.flag_cell((3, 2))
        frontend1.reset_mock()
        ctrlr.chord_on_cell((2, 2))
        assert_reset_call_count(frontend1, 1)
        assert ctrlr.board ==  Board.from_2d_array([
            [ 0,   1 , 'M1', 'F2'],
            [ 0,   1 ,   4 , '!1'],
            [ 0,   0 ,   1 , 'X1'],
            [ 1,   1 ,   1 ,   0 ],
            [ 1, 'F1',   1 ,   0 ],
        ])

    def test_first_success(self):
        # First click should hit an opening with first_success set.
        opts = GameOptsStruct(first_success=True)
        ctrlr = Controller(opts)
        coord = (1, 5)
        ctrlr.select_cell(coord)
        assert ctrlr.game_state == GameState.ACTIVE
        assert ctrlr.board[coord] == CellNum(0)
        for c in ctrlr.board.get_nbrs(coord):
            assert type(ctrlr.board[c]) == CellNum

        # Check first success is ignored when using created minefield.
        ctrlr = Controller(self.opts)
        ctrlr.mf = self.mf
        coord = (3, 0)
        ctrlr.select_cell(coord)
        assert ctrlr.game_state == GameState.LOST
        assert ctrlr.board[coord] == CellHit(2)

        # Test first success on a high density board.
        opts = GameOptsStruct(x_size=4, y_size=4, mines=15, per_cell=1,
                              first_success=True)
        ctrlr = Controller(opts)
        coord = (1, 2)
        ctrlr.select_cell(coord)
        assert ctrlr.board[coord] == CellNum(8)

        # Test no first success on a high density board - should hit a mine.
        opts.first_success = False
        passed = False
        attempts = 0
        while not passed:
            ctrlr = Controller(opts)
            ctrlr.select_cell(coord)
            attempts += 1
            if attempts >= 10:
                assert ctrlr.board[coord] == CellHit(1)
            elif ctrlr.board[coord] == CellHit(1):
                passed = True

    def test_losing(self, frontend1):
        # Lose straight away.
        ctrlr = Controller(self.opts)
        ctrlr.mf = self.mf
        ctrlr.select_cell((3, 0))
        assert ctrlr.game_state == GameState.LOST
        assert ctrlr.board == Board.from_2d_array([
            ['#',  '#', 'M1', '!2'],
            ['#',  '#',  '#', 'M1'],
            ['#',  '#',  '#',  '#'],
            ['#',  '#',  '#',  '#'],
            ['#', 'M1',  '#',  '#'],
        ])

        # Lose after game has been started with incorrect flag.
        ctrlr = Controller(self.opts)
        ctrlr.mf = self.mf
        ctrlr.register_callback(frontend1)
        ctrlr.select_cell((1, 0))
        ctrlr.flag_cell((1, 1))
        ctrlr.select_cell((2, 0))
        assert ctrlr.game_state == GameState.LOST
        assert_reset_call_count(frontend1, 3)
        assert ctrlr.board == Board.from_2d_array([
            ['#',   1 , '!1', 'M2'],
            ['#', 'X1',  '#', 'M1'],
            ['#',  '#',  '#',  '#'],
            ['#',  '#',  '#',  '#'],
            ['#', 'M1',  '#',  '#'],
        ])

        # Check cells can't be selected when the game is lost.
        for c in ctrlr.board.all_coords:
            ctrlr.select_cell(c)
            ctrlr.flag_cell(c)
            ctrlr.chord_on_cell(c)
            ctrlr.remove_cell_flags(c)
        assert_reset_call_count(frontend1, 0)

        # Check losing via chording works.
        ctrlr = Controller(self.opts)
        ctrlr.mf = self.mf
        ctrlr.select_cell((1, 0))
        ctrlr.flag_cell((1, 1))
        ctrlr.chord_on_cell((1, 0))
        assert ctrlr.game_state == GameState.LOST
        assert ctrlr.board == Board.from_2d_array([
            [ 0 ,   1 , '!1', 'M2'],
            [ 0 , 'X1',   4 , 'M1'],
            [ 0 ,   0 ,   1 ,  '#'],
            [ 1 ,   1 ,   1 ,  '#'],
            ['#', 'M1',  '#',  '#'],
        ])

    @pytest.mark.skip
    def test_winning(self):
        pass

    def test_new_game(self, frontend1):
        ctrlr = Controller(self.opts)
        ctrlr.register_callback(frontend1)

        # Start a new game before doing anything else.
        ctrlr.new_game()
        assert ctrlr.game_state == GameState.READY
        assert ctrlr.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert_reset_call_count(frontend1, 0)

        # Start a new game that isn't started but has flags.
        ctrlr.flag_cell((0, 0))
        ctrlr.flag_cell((1, 0))
        ctrlr.flag_cell((1, 0))
        assert ctrlr.board != Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        frontend1.reset_mock()
        ctrlr.new_game()
        assert ctrlr.game_state == GameState.READY
        assert ctrlr.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert_reset_call_count(frontend1, 1)

        # Start a new game mid-game.
        ctrlr.select_cell((0, 0))
        assert ctrlr.game_state == GameState.ACTIVE
        assert ctrlr.mf.is_created
        assert ctrlr.board != Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        frontend1.reset_mock()
        ctrlr.new_game()
        assert ctrlr.game_state == GameState.READY
        assert not ctrlr.mf.is_created
        assert ctrlr.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert_reset_call_count(frontend1, 1)

        # Start a new game on finished game.
        ctrlr.mf = self.mf
        ctrlr.select_cell((3, 0))
        assert ctrlr.game_state == GameState.LOST
        assert ctrlr.mf.is_created
        assert ctrlr.board != Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        frontend1.reset_mock()
        ctrlr.new_game()
        assert ctrlr.game_state == GameState.READY
        assert not ctrlr.mf.is_created
        assert ctrlr.board == Board(ctrlr.opts.x_size, ctrlr.opts.y_size)
        assert_reset_call_count(frontend1, 1)



    @pytest.mark.skip
    def test_replay_game(self):
        pass

    @pytest.mark.skip
    def test_callback_updates(self):
        pass