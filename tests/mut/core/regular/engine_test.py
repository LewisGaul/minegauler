# January 2022, Lewis Gaul

from unittest import mock

import pytest

from minegauler.core import api
from minegauler.core.regular import (
    Board,
    Coord,
    CreateController,
    Game,
    GameController,
    Minefield,
)
from minegauler.shared import GameOptsStruct
from minegauler.shared.types import CellContents, Difficulty, GameMode, GameState
from minegauler.shared.utils import Grid


class TestGameController:
    """
    Test the game controller class.

    No checks are performed on the notifications that should be sent to
    registered listeners, as this is left to CUT/IT.
    """

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
        mines=mf.mines,
        per_cell=mf.per_cell,
        first_success=True,
    )

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    @classmethod
    def create_ctrlr(cls, opts=None, *, set_mf=True):
        """
        Convenience method for creating a controller instance. Uses the test
        class options and minefield by default.

        :param opts:
            Optionally override the default options.
        :param set_mf:
            Whether to set the minefield or leave it not being created.
        """
        if opts is None:
            opts = cls.opts.copy()
        ctrlr = GameController(opts, notif=mock.Mock())
        if set_mf:
            ctrlr.game.mf = cls.mf
        return ctrlr

    # --------------------------------------------------------------------------
    # Test cases
    # --------------------------------------------------------------------------
    def test_basic_init(self):
        """Test basic creation of a controller."""
        ctrlr = GameController(self.opts, notif=mock.Mock())
        assert ctrlr._opts is self.opts
        assert ctrlr.game.state is GameState.READY
        assert not ctrlr.game.mf.populated
        assert ctrlr.game.board == Board(self.opts.x_size, self.opts.y_size)

    def test_getters(self):
        """Test the getter methods."""
        ctrlr = self.create_ctrlr()

        # Proxies to underlying game.
        assert ctrlr.board is ctrlr.game.board
        assert ctrlr.difficulty is ctrlr.game.difficulty

        # Unstarted game info.
        exp_game_info = api.GameInfo(
            game_state=GameState.READY,
            x_size=self.opts.x_size,
            y_size=self.opts.y_size,
            mines=self.opts.mines,
            difficulty=ctrlr.game.difficulty,
            per_cell=self.opts.per_cell,
            first_success=self.opts.first_success,
            minefield_known=False,
            mode=GameMode.REGULAR,
        )
        assert ctrlr.get_game_info() == exp_game_info

        # Started game info.
        with mock.patch.object(ctrlr.game, "get_elapsed", return_value=5):
            ctrlr.select_cell(Coord(0, 0))
            exp_game_info = api.GameInfo(
                game_state=GameState.ACTIVE,
                x_size=self.opts.x_size,
                y_size=self.opts.y_size,
                mines=self.opts.mines,
                difficulty=ctrlr.game.difficulty,
                per_cell=self.opts.per_cell,
                first_success=self.opts.first_success,
                minefield_known=False,
                mode=GameMode.REGULAR,
                started_info=api.GameInfo.StartedInfo(
                    start_time=ctrlr.game.start_time,
                    elapsed=5,
                    bbbv=self.mf.bbbv,
                    rem_bbbv=ctrlr.game.get_rem_3bv(),
                    bbbvps=ctrlr.game.get_3bvps(),
                    prop_complete=ctrlr.game.get_prop_complete(),
                    prop_flagging=0,
                ),
            )
            assert ctrlr.get_game_info() == exp_game_info

    def test_cell_interaction(self):
        """Test various basic cell interaction."""
        coord = Coord(2, 2)

        # Setup.
        opts = GameOptsStruct(per_cell=2, first_success=False)
        ctrlr = self.create_ctrlr(opts=opts, set_mf=False)

        # Flag a cell.
        ctrlr.flag_cell(coord)
        assert ctrlr.game.board[coord] is CellContents.Flag(1)
        assert not ctrlr.game.mf.populated
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines - 1

        # Select a flagged cell.
        ctrlr.select_cell(coord)
        assert ctrlr.game.board[coord] is CellContents.Flag(1)
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines - 1

        # Flag a cell that is already flagged (multiple mines per cell).
        ctrlr.flag_cell(coord)
        assert ctrlr.game.board[coord] is CellContents.Flag(2)
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines - 2

        # Flag a cell that is at max flags to reset it.
        ctrlr.flag_cell(coord)
        assert ctrlr.game.board[coord] is CellContents.Unclicked
        assert not ctrlr.game.mf.populated
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines

        # Remove cell flags.
        ctrlr.flag_cell(coord)
        ctrlr.remove_cell_flags(coord)
        assert ctrlr.game.board[coord] is CellContents.Unclicked
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines

        # Select a cell to start the game.
        ctrlr.select_cell(coord)
        assert isinstance(
            ctrlr.game.board[coord], (CellContents.HitMine, CellContents.Num)
        )
        assert ctrlr.game.mf.populated
        assert ctrlr.game.state in {GameState.ACTIVE, GameState.LOST}
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines

        # Select an already-selected cell.
        revealed = ctrlr.game.board[coord]
        ctrlr.select_cell(coord)
        assert ctrlr.game.board[coord] == revealed

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
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(0, 0))
        assert ctrlr.game.board == exp_board

        # Select the edge of an opening.
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(1, 3))
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
        ctrlr.select_cell(Coord(1, 2))
        assert ctrlr.game.board == exp_board

        # Select another cell to trigger the other opening.
        ctrlr.select_cell(Coord(3, 4))
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
        ctrlr = self.create_ctrlr()
        ctrlr.flag_cell(Coord(0, 1))
        ctrlr.select_cell(Coord(0, 0))
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
        ctrlr.remove_cell_flags(Coord(0, 1))
        ctrlr.select_cell(Coord(0, 0))
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
        ctrlr.flag_cell(Coord(0, 3))
        ctrlr.flag_cell(Coord(0, 2))
        ctrlr.chord_on_cell(Coord(0, 0))
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

    def test_chording(self):
        """Test chording in various situations."""
        # Use the same controller throughout the test.
        ctrlr = self.create_ctrlr()

        # No-op chording - game not started.
        ctrlr.chord_on_cell(Coord(0, 0))
        assert ctrlr.game.state is GameState.READY

        # No-op chording - no flags.
        ctrlr.select_cell(Coord(0, 4))
        ctrlr.chord_on_cell(Coord(0, 4))
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

        # Basic successful chording.
        ctrlr.flag_cell(Coord(1, 4))
        ctrlr.chord_on_cell(Coord(0, 4))
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

        # Successful chording triggering opening.
        ctrlr.chord_on_cell(Coord(1, 3))
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

        # No-op - repeated chording.
        prev_board = ctrlr.game.board
        ctrlr.chord_on_cell(Coord(1, 3))
        assert ctrlr.game.board == prev_board

        # No-op - chording on flagged cell.
        ctrlr.chord_on_cell(Coord(1, 4))
        assert ctrlr.game.board == prev_board

        # No-op - wrong number of flags.
        ctrlr.flag_cell(Coord(3, 0))
        ctrlr.flag_cell(Coord(3, 0))
        ctrlr.chord_on_cell(Coord(2, 1))

        # Incorrect flags cause hitting a mine.
        ctrlr.flag_cell(Coord(3, 2))
        ctrlr.chord_on_cell(Coord(2, 2))
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

    def test_first_success(self):
        """Test success on first click toggle option."""
        # First click should hit an opening with first_success set.
        opts = GameOptsStruct(first_success=True)
        ctrlr = GameController(opts, notif=mock.Mock())
        coord = Coord(1, 5)
        ctrlr.select_cell(coord)
        assert ctrlr.game.state is GameState.ACTIVE
        assert ctrlr.game.board[coord] is CellContents.Num(0)
        for c in ctrlr.game.board.get_nbrs(coord):
            assert type(ctrlr.game.board[c]) is CellContents.Num

        # Check first success is ignored when using created minefield.
        ctrlr = self.create_ctrlr()
        coord = Coord(3, 0)
        ctrlr.select_cell(coord)
        assert ctrlr.game.state is GameState.LOST
        assert ctrlr.game.board[coord] is CellContents.HitMine(2)

        # Test first success on a high density board - no room for opening.
        opts = GameOptsStruct(
            x_size=4, y_size=4, mines=15, per_cell=1, first_success=True
        )
        ctrlr = GameController(opts, notif=mock.Mock())
        coord = Coord(1, 2)
        ctrlr.select_cell(coord)
        assert ctrlr.game.board[coord] is CellContents.Num(8)

        # Test first success turned off - should hit a mine with high density.
        opts.first_success = False
        passed = False
        attempts = 0
        while not passed:
            ctrlr = GameController(opts, notif=mock.Mock())
            ctrlr.select_cell(coord)
            attempts += 1
            try:
                assert ctrlr.game.board[coord] is CellContents.HitMine(1)
                passed = True
            except AssertionError:
                if attempts >= 10:
                    raise

    def test_losing(self):
        # Lose straight away.
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(3, 0))
        assert ctrlr.game.state is GameState.LOST
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

        # Lose after game has been started with incorrect flag.
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(1, 0))
        ctrlr.flag_cell(Coord(1, 1))
        ctrlr.select_cell(Coord(2, 0))
        assert ctrlr.game.state is GameState.LOST
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

        # Check cells can't be selected when the game is lost.
        for c in ctrlr.game.board.all_coords:
            ctrlr.select_cell(c)
            ctrlr.flag_cell(c)
            ctrlr.chord_on_cell(c)
            ctrlr.remove_cell_flags(c)
        assert ctrlr.game.state is GameState.LOST

        # Check losing via chording works.
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(1, 0))
        ctrlr.flag_cell(Coord(1, 1))
        ctrlr.chord_on_cell(Coord(1, 0))
        assert ctrlr.game.state is GameState.LOST
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

    def test_winning(self):
        # Test winning in one click.
        opts = GameOptsStruct(x_size=2, y_size=1, mines=1, first_success=True)
        ctrlr = self.create_ctrlr(opts=opts, set_mf=False)
        ctrlr.select_cell(Coord(0, 0))
        assert ctrlr.game.state is GameState.WON
        assert ctrlr.game.end_time is not None
        assert ctrlr.game.mines_remaining == 0
        assert ctrlr.game.board == ctrlr.game.mf.completed_board

        # Check winning via chording and hitting an opening works.
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.select_cell(Coord(0, 4))
        ctrlr.flag_cell(Coord(3, 1))
        ctrlr.chord_on_cell(Coord(2, 2))
        assert ctrlr.game.state is GameState.WON
        assert (
            ctrlr.game.board
            == ctrlr.game.mf.completed_board
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
        for c in ctrlr.game.board.all_coords:
            ctrlr.select_cell(c)
            ctrlr.flag_cell(c)
            ctrlr.chord_on_cell(c)
            ctrlr.remove_cell_flags(c)
        assert ctrlr.game.state is GameState.WON

    def test_new_game(self):
        """Test starting new games."""
        # Start a new game before doing anything else with minefield.
        ctrlr = self.create_ctrlr()
        ctrlr.new_game()
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert not ctrlr.game.mf.populated

        # Start a new game that isn't started but has flags.
        ctrlr = self.create_ctrlr()
        ctrlr.flag_cell(Coord(0, 0))
        ctrlr.flag_cell(Coord(1, 0))
        ctrlr.flag_cell(Coord(1, 0))
        assert ctrlr.game.board != Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        ctrlr.new_game()
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)

        # Start a new game mid-game.
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.select_cell(Coord(0, 1))
        assert ctrlr.game.state is GameState.ACTIVE
        assert ctrlr.game.mf.populated
        assert ctrlr.game.board != Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        ctrlr.new_game()
        assert ctrlr.game.state is GameState.READY
        assert not ctrlr.game.mf.populated
        assert ctrlr.game.start_time is None
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)

        # Start a new game on lost game.
        ctrlr = self.create_ctrlr()
        ctrlr.game.mf = self.mf
        ctrlr.select_cell(Coord(3, 0))
        assert ctrlr.game.state is GameState.LOST
        assert ctrlr.game.mf.populated
        assert ctrlr.game.board != Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        ctrlr.new_game()
        assert ctrlr.game.state is GameState.READY
        assert not ctrlr.game.mf.populated
        assert ctrlr.game.start_time is ctrlr.game.end_time is None
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)

        # Start a new game when the number of mines is too high.
        ctrlr = self.create_ctrlr()
        ctrlr.game = Game.from_minefield(
            Minefield.from_grid(
                Grid(self.opts.x_size, self.opts.y_size, fill=2), per_cell=3
            )
        )
        assert ctrlr.game.mines == self.opts.x_size * self.opts.y_size * 2
        ctrlr._opts.mines = ctrlr.game.mines
        ctrlr.new_game()
        assert ctrlr.game.state is GameState.READY
        assert (
            ctrlr._opts.mines
            == ctrlr.game.mines
            == self.opts.x_size * self.opts.y_size - 1
        )

    def test_restart_game(self):
        """Test restarting games."""
        # Only require a single controller.
        ctrlr = self.create_ctrlr(set_mf=False)

        # Replay before doing anything else, without minefield.
        ctrlr.restart_game()
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert not ctrlr.game.mf.populated

        # Replay before doing anything else, with minefield.
        ctrlr.game.mf = self.mf
        ctrlr.restart_game()
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr.game.mf == self.mf

        # Restart a game that isn't started but has flags.
        ctrlr.flag_cell(Coord(0, 0))
        ctrlr.flag_cell(Coord(1, 0))
        ctrlr.flag_cell(Coord(1, 0))
        ctrlr.restart_game()
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr.game.mf == self.mf

        # Restart game mid-game.
        ctrlr.select_cell(Coord(0, 0))
        assert ctrlr.game.state is GameState.ACTIVE
        ctrlr.restart_game()
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.start_time is None
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr.game.mf == self.mf

        # Restart finished game (lost game).
        ctrlr.select_cell(Coord(3, 0))
        assert ctrlr.game.state is GameState.LOST
        ctrlr.restart_game()
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.start_time is ctrlr.game.end_time is None
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines
        assert ctrlr.game.board == Board(ctrlr._opts.x_size, ctrlr._opts.y_size)
        assert ctrlr.game.mf == self.mf

    def test_resize_board(self):
        """Test resizing the board in various situations."""
        # Setup, including start a game.
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.flag_cell(Coord(2, 0))
        assert ctrlr.game.state is not GameState.READY
        assert ctrlr.game.mines_remaining == self.opts.mines - 1

        # Normal resize.
        opts = ctrlr._opts.copy()
        opts.x_size, opts.y_size, opts.mines = 10, 2, 3
        ctrlr.resize_board(x_size=opts.x_size, y_size=opts.y_size, mines=opts.mines)
        assert ctrlr._opts == opts
        assert ctrlr.game.state is GameState.READY
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines
        assert not ctrlr.game.mf.populated
        assert ctrlr.game.board == Board(opts.x_size, opts.y_size)

        # Resize without changing values starts new game.
        ctrlr.select_cell(Coord(0, 0))
        assert ctrlr.game.state is not GameState.READY
        ctrlr.resize_board(x_size=opts.x_size, y_size=opts.y_size, mines=opts.mines)
        assert ctrlr.game.state is GameState.READY
        assert not ctrlr.game.mf.populated
        assert ctrlr.game.board == Board(opts.x_size, opts.y_size)

    def test_lives(self):
        opts = self.opts.copy()
        opts.lives = 3
        ctrlr = self.create_ctrlr(opts=opts)

        # Lose first life on single mine.
        ctrlr.select_cell(Coord(2, 0))
        assert ctrlr.game.state is GameState.ACTIVE
        assert ctrlr.game.lives_remaining == 2
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines - 1
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

        # Lose second life on double mine.
        ctrlr.select_cell(Coord(3, 0))
        assert ctrlr.game.state is GameState.ACTIVE
        assert ctrlr.game.lives_remaining == 1
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines - 3
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

        # Lose final life.
        ctrlr.select_cell(Coord(3, 1))
        assert ctrlr.game.state is GameState.LOST
        assert ctrlr.game.lives_remaining == 0
        assert ctrlr.game.mines_remaining == ctrlr._opts.mines - 3  # unchanged
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

    def test_set_first_success(self):
        """Test the method to set the 'first success' option."""
        opts = self.opts.copy()
        opts.first_success = False
        ctrlr = self.create_ctrlr(opts)
        assert ctrlr._opts is opts
        assert ctrlr.game.first_success is False

        # Normal toggle.
        ctrlr.set_first_success(True)
        assert ctrlr._opts.first_success is True
        assert ctrlr.game.first_success is True

        # No op.
        ctrlr.set_first_success(True)
        assert ctrlr._opts.first_success is True
        assert ctrlr.game.first_success is True

        # During game.
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.set_first_success(False)
        assert ctrlr._opts.first_success is False
        assert ctrlr.game.first_success is True

        # New games pick up the change.
        ctrlr.new_game()
        assert ctrlr._opts.first_success is False
        assert ctrlr.game.first_success is False

    def test_set_per_cell(self):
        """Test the method to set the 'per cell' option."""
        opts = self.opts.copy()
        opts.per_cell = 1
        ctrlr = self.create_ctrlr(opts, set_mf=False)
        assert ctrlr._opts is opts
        assert ctrlr.game.per_cell == 1

        # Normal toggle.
        ctrlr.set_per_cell(2)
        assert ctrlr._opts.per_cell == 2
        assert ctrlr.game.per_cell == 2

        # No op.
        ctrlr.set_per_cell(2)
        assert ctrlr._opts.per_cell == 2
        assert ctrlr.game.per_cell == 2

        # During game.
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.set_per_cell(3)
        assert ctrlr._opts.per_cell == 3
        assert ctrlr.game.per_cell == 2

        # New games pick up the change.
        ctrlr.new_game()
        assert ctrlr._opts.per_cell == 3
        assert ctrlr.game.per_cell == 3

        # Known minefield.
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.restart_game()
        ctrlr.set_per_cell(4)
        assert ctrlr._opts.per_cell == 4
        assert ctrlr.game.per_cell == 3

        # Invalid value.
        with pytest.raises(ValueError):
            ctrlr.set_per_cell(0)

    @mock.patch("builtins.open")
    def test_save_minefield(self, mock_open):
        """Test the method to save the current minefield."""
        ctrlr = self.create_ctrlr()

        # Game must be completed.
        with pytest.raises(RuntimeError):
            ctrlr.save_current_minefield("file")

        # Success case.
        ctrlr.game.state = GameState.WON
        with mock.patch("json.dump") as mock_json_dump:
            ctrlr.save_current_minefield("file")
        mock_open.assert_called_once_with("file", "w")
        mock_json_dump.assert_called_once_with(ctrlr.game.mf.to_json(), mock.ANY)

    @mock.patch("builtins.open")
    def test_load_minefield(self, mock_open):
        """Test the method to load a minefield from file."""
        ctrlr = self.create_ctrlr()
        mf = Minefield.from_dimensions(11, 12, mines=10)
        mf.populate()

        with mock.patch("json.load", return_value=mf.to_json()):
            ctrlr.load_minefield("file")
        mock_open.assert_called_once_with("file")
        assert ctrlr._opts.x_size == 11
        assert ctrlr._opts.y_size == 12
        assert ctrlr._opts.mines == 10
        assert ctrlr.game.mf == mf
        assert ctrlr.game.minefield_known


class TestCreateController:
    """
    Test the create controller class.

    No checks are performed on the notifications that should be sent to
    registered listeners, as this is left to CUT/IT.
    """

    opts = GameOptsStruct()

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    @classmethod
    def create_ctrlr(cls, opts=None) -> CreateController:
        """
        Convenience method for creating a controller instance. Uses the test
        class optionsby default.

        :param opts:
            Optionally override the default options.
        """
        if opts is None:
            opts = cls.opts.copy()
        return CreateController(opts, notif=mock.Mock())

    # --------------------------------------------------------------------------
    # Test cases
    # --------------------------------------------------------------------------
    def test_basic_init(self):
        """Test basic creation of a controller."""
        ctrlr = CreateController(self.opts, notif=mock.Mock())
        assert ctrlr._opts is self.opts
        assert ctrlr._board == Board(self.opts.x_size, self.opts.y_size)
        assert ctrlr._flags == 0

    def test_get_game_info(self):
        """Test get_game_info() method."""
        opts = self.opts.copy()
        ctrlr = self.create_ctrlr(opts)

        # Initial creation.
        exp_game_info = api.GameInfo(
            game_state=GameState.ACTIVE,
            x_size=opts.x_size,
            y_size=opts.y_size,
            mines=0,
            difficulty=Difficulty.CUSTOM,
            per_cell=opts.per_cell,
            first_success=opts.first_success,
            minefield_known=True,
            mode=GameMode.REGULAR,
        )
        assert ctrlr.get_game_info() == exp_game_info

        # Changed values.
        opts.per_cell = 3
        ctrlr._flags = 10
        exp_game_info = api.GameInfo(
            game_state=GameState.ACTIVE,
            x_size=opts.x_size,
            y_size=opts.y_size,
            mines=10,
            difficulty=Difficulty.BEGINNER,
            per_cell=opts.per_cell,
            first_success=opts.first_success,
            minefield_known=True,
            mode=GameMode.REGULAR,
        )
        assert ctrlr.get_game_info() == exp_game_info

    def test_cell_interaction(self):
        """Test various basic cell interaction."""
        # Setup.
        coord = Coord(2, 2)
        opts = GameOptsStruct(per_cell=2)
        ctrlr = self.create_ctrlr(opts)

        # Flag a cell.
        ctrlr.flag_cell(coord)
        assert ctrlr.board[coord] is CellContents.Mine(1)
        assert ctrlr.get_game_info().mines == 1

        # Select a flagged cell.
        ctrlr.select_cell(coord)
        assert ctrlr.board[coord] is CellContents.Mine(1)
        assert ctrlr.get_game_info().mines == 1

        # Flag a cell that is already flagged (multiple mines per cell).
        ctrlr.flag_cell(coord)
        assert ctrlr.board[coord] is CellContents.Mine(2)
        assert ctrlr.get_game_info().mines == 2

        # Flag a cell that is at max flags to reset it.
        ctrlr.flag_cell(coord)
        assert ctrlr.board[coord] is CellContents.Unclicked
        assert ctrlr.get_game_info().mines == 0

        # Remove cell flags.
        ctrlr.flag_cell(coord)
        ctrlr.remove_cell_flags(coord)
        assert ctrlr.board[coord] is CellContents.Unclicked
        assert ctrlr.get_game_info().mines == 0

        # Select a cell.
        ctrlr.select_cell(coord)
        assert ctrlr.board[coord] is CellContents.Num(0)
        assert ctrlr.get_game_info().mines == 0

        # Select an already-selected cell.
        ctrlr.select_cell(coord)
        assert ctrlr.board[coord] is CellContents.Num(1)
        assert ctrlr.get_game_info().mines == 0

        # 'Flag' a clicked cell.
        ctrlr.flag_cell(coord)
        assert ctrlr.board[coord] is CellContents.Unclicked
        assert ctrlr.get_game_info().mines == 0

        # 'Remove flags' on a clicked cell.
        ctrlr.select_cell(coord)
        ctrlr.remove_cell_flags(coord)
        assert ctrlr.board[coord] is CellContents.Num(0)

    def test_chording(self):
        """Test chording."""
        ctrlr = self.create_ctrlr()
        # Chording does nothing in the backend.
        ctrlr.chord_on_cell(Coord(0, 0))
        assert ctrlr.board[(0, 0)] is CellContents.Unclicked
        assert ctrlr.get_game_info().mines == 0

    def test_new_game(self):
        """Test starting new games."""
        opts = GameOptsStruct(per_cell=3)
        ctrlr = self.create_ctrlr(opts)
        base_game_info = ctrlr.get_game_info()

        # Start a new game before doing anything else.
        ctrlr.new_game()
        assert ctrlr.get_game_info() == base_game_info

        # Start a new game with various cells selected/flagged.
        ctrlr.flag_cell(Coord(0, 0))
        ctrlr.flag_cell(Coord(1, 0))
        ctrlr.flag_cell(Coord(1, 0))
        ctrlr.select_cell(Coord(1, 1))
        ctrlr.select_cell(Coord(1, 1))
        ctrlr.select_cell(Coord(2, 1))
        assert ctrlr.get_game_info().mines == 3
        assert ctrlr.board[(0, 0)] is CellContents.Mine(1)
        assert ctrlr.board[(1, 0)] is CellContents.Mine(2)
        assert ctrlr.board[(1, 1)] is CellContents.Num(1)
        assert ctrlr.board[(2, 1)] is CellContents.Num(0)
        ctrlr.new_game()
        assert ctrlr.get_game_info() == base_game_info
        assert ctrlr.board == Board(opts.x_size, opts.y_size)

    def test_restart_game(self):
        """Test restart game just calls new game."""
        ctrlr = self.create_ctrlr()
        with mock.patch.object(ctrlr, "new_game") as mock_new_game:
            ctrlr.restart_game()
            mock_new_game.assert_called_once()

    def test_resize_board(self):
        """Test resizing the board."""
        ctrlr = self.create_ctrlr()
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.flag_cell(Coord(1, 1))
        assert ctrlr.get_game_info().x_size == 8
        assert ctrlr.get_game_info().y_size == 8
        assert ctrlr.get_game_info().mines == 1
        assert ctrlr.board.x_size == 8
        assert ctrlr.board.y_size == 8

        # Normal resize.
        ctrlr.resize_board(2, 3, 4)
        assert ctrlr.get_game_info().x_size == 2
        assert ctrlr.get_game_info().y_size == 3
        assert ctrlr.get_game_info().mines == 0
        assert ctrlr.board == Board(2, 3)

        # Resize without changing values starts new game.
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.flag_cell(Coord(1, 1))
        ctrlr.resize_board(2, 3, 4)
        assert ctrlr.get_game_info().x_size == 2
        assert ctrlr.get_game_info().y_size == 3
        assert ctrlr.get_game_info().mines == 0
        assert ctrlr.board == Board(2, 3)

    def test_set_first_success(self):
        """Test the method to set the 'first success' option."""
        opts = GameOptsStruct(first_success=False)
        ctrlr = self.create_ctrlr(opts)
        assert ctrlr.get_game_info().first_success is False

        # Normal toggle.
        ctrlr.set_first_success(True)
        assert ctrlr.get_game_info().first_success is True

        # No op.
        ctrlr.set_first_success(True)
        assert ctrlr.get_game_info().first_success is True

        # Toggle back.
        ctrlr.set_first_success(False)
        assert ctrlr.get_game_info().first_success is False

    def test_set_per_cell(self):
        """Test the method to set the 'per cell' option."""
        opts = GameOptsStruct(per_cell=1)
        ctrlr = self.create_ctrlr(opts)
        assert ctrlr.get_game_info().per_cell == 1

        # Normal change.
        ctrlr.set_per_cell(2)
        assert ctrlr.get_game_info().per_cell == 2

        # No op.
        ctrlr.set_per_cell(2)
        assert ctrlr.get_game_info().per_cell == 2

    @mock.patch("builtins.open")
    def test_save_minefield(self, mock_open):
        """Test the method to save the current minefield."""
        ctrlr = self.create_ctrlr(GameOptsStruct(x_size=3, y_size=3, per_cell=3))
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.select_cell(Coord(0, 0))
        ctrlr.select_cell(Coord(0, 1))
        ctrlr.flag_cell(Coord(1, 2))
        ctrlr.flag_cell(Coord(1, 2))
        ctrlr.flag_cell(Coord(2, 2))
        mf = Minefield.from_2d_array(
            [
                # fmt: off
                [0, 0, 0],
                [0, 0, 0],
                [0, 2, 1],
                # fmt: on
            ],
            per_cell=3,
        )

        with mock.patch("json.dump") as mock_json_dump:
            ctrlr.save_current_minefield("file")
        mock_open.assert_called_once_with("file", "w")
        mock_json_dump.assert_called_once_with(mf.to_json(), mock.ANY)
