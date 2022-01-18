# October 2021, Lewis Gaul

"""
Test the regular board module.

"""

import textwrap

import pytest

from minegauler.core.regular import Board, Coord
from minegauler.shared import utils
from minegauler.shared.types import CellContents


class TestRegularBoard:
    """Test the regular Board class."""

    x, y = 5, 3

    @pytest.fixture
    def board(self) -> Board:
        return Board(self.x, self.y)

    def test_init(self):
        board = Board(self.x, self.y)
        assert board.x_size == self.x
        assert board.y_size == self.y
        assert sorted(board.all_coords) == [
            Coord(i, j) for i in range(self.x) for j in range(self.y)
        ]
        assert all(board[c] is CellContents.Unclicked for c in board.all_coords)

    def test_get_nbrs(self, board):
        # Corner
        nbrs = board.get_nbrs((0, 0))
        assert set(nbrs) == {(0, 1), (1, 0), (1, 1)}

        # Edge
        nbrs = board.get_nbrs((0, 1))
        assert set(nbrs) == {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)}

        # Middle
        nbrs = board.get_nbrs((1, 1), include_origin=True)
        assert set(nbrs) == {
            # fmt: off
            (0, 0), (0, 1), (0, 2),
            (1, 0), (1, 1), (1, 2),
            (2, 0), (2, 1), (2, 2),
            # fmt: on
        }

    def test_fill(self, board):
        board.fill(CellContents.Num(0))
        assert len(board.all_coords) == self.x * self.y
        assert all(board[c] == CellContents.Num(0) for c in board.all_coords)

    def test_reset(self, board):
        board.fill(CellContents.Num(0))
        board.reset()
        assert len(board.all_coords) == self.x * self.y
        assert all(board[c] is CellContents.Unclicked for c in board.all_coords)

    def test_contains(self, board):
        assert Coord(0, 0) in board
        assert Coord(10, 10) not in board

    def test_setitem_error(self, board):
        with pytest.raises(TypeError):
            board[(0, 0)] = 1

    def test_equal(self):
        board1 = Board(self.x, self.y)
        board2 = Board(self.x, self.y)
        board3 = Board(self.x, self.y + 1)
        assert board1 == board2
        assert board1 != board3
        assert board1 != utils.Grid(self.x, self.y, fill=CellContents.Unclicked)

        board2[Coord(0, 0)] = CellContents.Flag(1)
        assert board1 != board2

    def test_stringify(self, board):
        board[(0, 0)] = CellContents.Flag(2)
        board[(1, 0)] = CellContents.Mine(2)
        board[(1, 1)] = CellContents.Num(5)
        board[(2, 1)] = CellContents.Num(0)
        assert repr(board) == f"<{self.x}x{self.y} board>"
        assert str(board) == textwrap.dedent(
            """\
            F2 M2  #  #  #
             #  5  .  #  #
             #  #  #  #  #"""
        )

    def test_from_2d_array(self):
        board = Board.from_2d_array(
            [
                # fmt: off
                ["F1", "F2", "#"],
                ["M1", 1, "X3"],
                [0, 1, "!1"],
                # fmt: on
            ]
        )
        assert board.x_size == 3
        assert board.y_size == 3
        assert board[(0, 0)] == CellContents.Flag(1)
        assert board[(1, 0)] == CellContents.Flag(2)
        assert board[(2, 0)] is CellContents.Unclicked
        assert board[(0, 1)] == CellContents.Mine(1)
        assert board[(1, 1)] == CellContents.Num(1)
        assert board[(2, 1)] == CellContents.WrongFlag(3)
        assert board[(0, 2)] == CellContents.Num(0)
        assert board[(1, 2)] == CellContents.Num(1)
        assert board[(2, 2)] == CellContents.HitMine(1)

    def test_from_2d_array_error(self):
        with pytest.raises(ValueError):
            Board.from_2d_array([["1"]])
