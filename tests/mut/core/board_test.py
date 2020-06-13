"""
Test the board module.

October 2018, Lewis Gaul
"""

import json
from typing import List

import pytest

from minegauler.core.board import Board, Minefield
from minegauler.shared.utils import Grid
from minegauler.types import CellContents
from minegauler.typing import Coord_T


class TestMinefield:
    """Test the Minefield class."""

    x, y = 4, 3
    mines = 5
    per_cell = 2

    # --------------------------------------------------------------------------
    # Test cases
    # --------------------------------------------------------------------------
    def test_create_basic(self):
        """Check basic creation."""
        mf = Minefield(self.x, self.y, mines=self.mines, per_cell=self.per_cell)
        assert (mf.x_size, mf.y_size) == (self.x, self.y)
        assert len(mf.all_coords) == self.x * self.y
        self.check_mf_created(mf)
        # Check passing safe coords.
        safe_coords = [(0, 0), (0, 1), (1, 0), (1, 1)]
        mf = Minefield(
            self.x,
            self.y,
            mines=self.mines,
            per_cell=self.per_cell,
            safe_coords=safe_coords,
        )
        self.check_mf_created(mf)
        for opening in mf.openings:
            if safe_coords[0] in opening:
                assert set(safe_coords) & set(opening) == set(safe_coords)
                break
        else:
            assert False, "Expected opening due to safe coords"

    def test_from_mines_list(self):
        """Check creation from a list of mine coords."""
        mine_coords = [(0, 0), (0, 1), (0, 1), (2, 2)]
        mf = Minefield(self.x, self.y, mines=mine_coords, per_cell=2)
        self.check_mf_created(mf)
        assert mf.per_cell == 2
        exp_completed_board = Board.from_2d_array(
            [
                # fmt: off
                ["F1", 3,  0,   0],
                ["F2", 4,  1,   1],
                [ 2,   3, "F1", 1],
                # fmt: on
            ]
        )
        exp_openings = [[(1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)]]
        exp_3bv = 4
        self.check_mf_correct(mf, exp_3bv, exp_openings, exp_completed_board)

        # Check per cell is respected. Also multiple openings.
        mine_coords = [(0, 0), (2, 2)]
        mf = Minefield(self.x, self.y, mines=mine_coords, per_cell=2)
        self.check_mf_created(mf)
        assert mf.per_cell == 2
        exp_completed_board = Board.from_2d_array(
            [
                # fmt: off
                ["F1", 1,  0,   0],
                [ 1,   2,  1,   1],
                [ 0,   1, "F1", 1],
                # fmt: on
            ]
        )
        exp_openings = [
            [(1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)],
            [(0, 1), (0, 2), (1, 1), (1, 2)],
        ]
        exp_3bv = 3
        self.check_mf_correct(mf, exp_3bv, exp_openings, exp_completed_board)

    def test_to_from_json(self):
        """Check JSON methods."""
        obj = dict(
            x_size=self.x, y_size=self.y, mine_coords=[[0, 0], [2, 2]], per_cell=2
        )
        mf = Minefield.from_json(obj)
        self.check_mf_created(mf)
        assert mf.per_cell == 2
        exp_completed_board = Board.from_2d_array(
            [
                # fmt: off
                ["F1", 1,  0,   0],
                [ 1,   2,  1,   1],
                [ 0,   1, "F1", 1],
                # fmt: on
            ]
        )
        exp_openings = [
            [(1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)],
            [(0, 1), (0, 2), (1, 1), (1, 2)],
        ]
        exp_3bv = 3
        self.check_mf_correct(mf, exp_3bv, exp_openings, exp_completed_board)

        assert json.dumps(mf.to_json()) == json.dumps(obj)

    def test_from_array(self):
        """Check creation from array or grid."""
        array = [[0, 0, 1, 2], [0, 0, 0, 1], [0, 1, 0, 0]]
        grid = Grid.from_2d_array(array)
        exp_mine_coords = [(1, 2), (2, 0), (3, 0), (3, 0), (3, 1)]
        exp_3bv = 5
        exp_openings = [[(0, 0), (0, 1), (1, 0), (1, 1)]]
        exp_completed_board = Board.from_2d_array(
            [
                # fmt: off
                [0,  1,  "F1", "F2"],
                [1,  2,   5,   "F1"],
                [1, "F1", 2,    1  ],
                # fmt: on
            ]
        )

        # Check creation from a grid.
        mf = Minefield.from_grid(grid, per_cell=2)
        assert set(mf.mine_coords) == set(exp_mine_coords)
        self.check_mf_correct(mf, exp_3bv, exp_openings, exp_completed_board)

        # Check creation from a 2D list.
        mf = Minefield.from_2d_array(array, per_cell=2)
        assert set(mf.mine_coords) == set(exp_mine_coords)
        self.check_mf_correct(mf, exp_3bv, exp_openings, exp_completed_board)

    def test_create_extremes(self):
        """Check creation in various extremes."""
        # Check creation with only no mines.
        mf = Minefield(10, 10, mines=0)
        self.check_mf_created(mf)
        assert mf.bbbv == 1
        assert len(mf.openings) == 1

        # Check creation of a tiny minefield.
        mf = Minefield(2, 1, mines=3, per_cell=3, safe_coords=[(0, 0)])
        self.check_mf_created(mf)
        assert mf.mine_coords == [(1, 0), (1, 0), (1, 0)]
        self.check_mf_correct(mf, 1, [], Board.from_2d_array([[3, "F3"]]))

        # Check creation with only one space.
        mf = Minefield(self.x, self.y, mines=self.x * self.y - 1)
        self.check_mf_created(mf)
        assert mf.bbbv == 1
        assert mf.openings == []

        # Check creation with a high mine density per cell.
        mf = Minefield(
            self.x, self.y, mines=5 * self.x * self.y, per_cell=10, safe_coords=[(0, 0)]
        )
        self.check_mf_created(mf)
        assert max(mf.mine_coords.count(c) for c in mf.mine_coords) > 5

        # Check creation leaves a space, high per cell.
        mf = Minefield(self.x, self.y, mines=10 * (self.x * self.y - 1), per_cell=10)
        self.check_mf_created(mf)
        for c in mf.all_coords:
            if not mf.cell_contains_mine(c):
                break
        else:
            assert False, "Expected to find a safe cell"

    def test_create_errors(self):
        """Check various creation errors."""
        # Check error when too many mines.
        with pytest.raises(ValueError):
            Minefield(self.x, self.y, mines=self.x * self.y, per_cell=1)
        with pytest.raises(ValueError):
            Minefield(
                self.x,
                self.y,
                mines=self.x * self.y - 1,
                per_cell=1,
                safe_coords=[(0, 0), (1, 1)],
            )

        # Check passing in too many mines in a cell.
        mine_coords = [(0, 0), (0, 0), (0, 0)]
        with pytest.raises(ValueError):
            Minefield(self.x, self.y, mines=mine_coords, per_cell=1)

    def test_stringify(self):
        """Get coverage of stringify methods."""
        mf = Minefield(self.x, self.y, mines=self.mines, per_cell=self.per_cell)
        repr(mf)
        str(mf)
        repr(mf.completed_board)
        str(mf.completed_board)

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    @staticmethod
    def check_mf_created(mf: Minefield):
        """
        Check minefield was created properly.
        """
        assert mf.mine_coords is not None
        assert len(mf.mine_coords) == mf.nr_mines
        if mf.nr_mines > 0:
            max_mines_in_cell = max(mf.mine_coords.count(c) for c in mf.mine_coords)
            assert max_mines_in_cell <= mf.per_cell
        assert len(set(mf.mine_coords)) < len(mf.all_coords)  # safe cell exists
        assert mf.bbbv is not None and 1 <= mf.bbbv <= len(mf.all_coords)
        assert mf.completed_board is not None
        assert mf.openings is not None
        # Check opening coords and completed board are sane.
        opening_coords = [c for grp in mf.openings for c in grp]
        assert all(
            [
                opening_coords.count(c) == 1
                for c in mf.all_coords
                if mf[c] == CellContents.Num(0)
            ]
        )
        for c in mf.all_coords:
            if c in mf.mine_coords:
                assert mf[c] > 0
                assert type(mf.completed_board[c]) is CellContents.Flag
                assert c not in opening_coords
            else:
                assert mf[c] == 0
                assert type(mf.completed_board[c]) is CellContents.Num
                if mf.completed_board[c] == 0:
                    assert c in opening_coords

    @staticmethod
    def check_mf_correct(
        mf: Minefield,
        exp_3bv: int,
        exp_openings: List[List[Coord_T]],
        exp_completed_board: Board,
    ):
        """
        Check created minefield is correct.

        Arguments:
        mf (Minefield)
            The minefield to check.
        exp_3bv (int)
            The expected 3bv of the minefield.
        exp_openings ([[(int, int), ...], ...])
            The expected openings.
        exp_completed_board (Board)
            The expected contents of the completed board.
        """
        assert len(mf.openings) == len(exp_openings)
        for grp in exp_openings:
            assert grp in mf.openings
        assert mf.bbbv == exp_3bv
        for c in mf.all_coords:
            assert mf[c] == mf.mine_coords.count(c)
            assert mf.completed_board[c] == exp_completed_board[c]
