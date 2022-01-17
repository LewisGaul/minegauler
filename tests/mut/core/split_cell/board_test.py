# January 2022, Lewis Gaul

"""
Test the split cell board module.

"""

import pytest

from minegauler.core.split_cell import Board, Coord
from minegauler.shared.types import CellContents


class TestSplitCellBoard:
    """Test the split cell Board class."""

    x, y = 6, 4

    @pytest.fixture
    def board(self) -> Board:
        return Board(self.x, self.y)

    def test_init(self):
        board = Board(self.x, self.y)
        assert board.x_size == self.x
        assert board.y_size == self.y
        assert sorted(board.all_coords) == [
            Coord(0, 0, False),
            Coord(0, 2, False),
            Coord(2, 0, False),
            Coord(2, 2, False),
            Coord(4, 0, False),
            Coord(4, 2, False),
        ]
        assert all(board[c] is CellContents.Unclicked for c in board.all_coords)

    def test_split_coord(self, board):
        # +-----+-----+-----+
        # |     |     |     |
        # |     |     |     |
        # |     |     |     |
        # +-----+-----+-----+
        # |     |  |  |     |
        # |     |--+--|     |
        # |     |  |  |     |
        # +-----+-----+-----+
        board.split_coord(Coord(2, 2, False))
        assert set(board.all_coords) == {
            Coord(0, 0, False),
            Coord(0, 2, False),
            Coord(2, 0, False),
            Coord(2, 2, True),
            Coord(2, 3, True),
            Coord(3, 2, True),
            Coord(3, 3, True),
            Coord(4, 0, False),
            Coord(4, 2, False),
        }
        assert all(board[c] is CellContents.Unclicked for c in board.all_coords)

    def test_get_nbrs(self, board):
        # Top-left corner
        nbrs = board.get_nbrs(Coord(0, 0, False))
        assert set(nbrs) == {Coord(0, 2, False), Coord(2, 0, False), Coord(2, 2, False)}

        # Bottom-right corner
        nbrs = board.get_nbrs(Coord(4, 2, False))
        assert set(nbrs) == {Coord(2, 0, False), Coord(2, 2, False), Coord(4, 0, False)}

        # Edge
        nbrs = board.get_nbrs(Coord(2, 0, False))
        assert set(nbrs) == {
            Coord(0, 0, False),
            Coord(0, 2, False),
            Coord(2, 2, False),
            Coord(4, 0, False),
            Coord(4, 2, False),
        }

        # Split a cell:
        # +-----+-----+-----+
        # |     |     |     |
        # |     |     |     |
        # |     |     |     |
        # +-----+-----+-----+
        # |     |  |  |     |
        # |     |--+--|     |
        # |     |  |  |     |
        # +-----+-----+-----+
        board.split_coord(Coord(2, 2, False))

        # Top-left corner
        nbrs = board.get_nbrs(Coord(0, 0, False))
        assert set(nbrs) == {Coord(0, 2, False), Coord(2, 0, False), Coord(2, 2, True)}

        # Top middle
        nbrs = board.get_nbrs(Coord(2, 0, False))
        assert set(nbrs) == {
            Coord(0, 0, False),
            Coord(0, 2, False),
            Coord(2, 2, True),
            Coord(3, 2, True),
            Coord(4, 0, False),
            Coord(4, 2, False),
        }

        # Top-left small cell
        nbrs = board.get_nbrs(Coord(2, 2, True))
        assert set(nbrs) == {
            Coord(0, 0, False),
            Coord(0, 2, False),
            Coord(2, 0, False),
            Coord(2, 3, True),
            Coord(3, 2, True),
            Coord(3, 3, True),
        }

        # Bottom-right small cell
        nbrs = board.get_nbrs(Coord(3, 3, True))
        assert set(nbrs) == {
            Coord(2, 2, True),
            Coord(2, 3, True),
            Coord(3, 2, True),
            Coord(4, 2, False),
        }

        # Split another cell:
        # +-----+-----+-----+
        # |     |     |  |  |
        # |     |     |--+--|
        # |     |     |  |  |
        # +-----+-----+-----+
        # |     |  |  |     |
        # |     |--+--|     |
        # |     |  |  |     |
        # +-----+-----+-----+
        board.split_coord(Coord(4, 0, False))
        nbrs = board.get_nbrs(Coord(4, 1, True))
        assert set(nbrs) == {
            Coord(2, 0, False),
            Coord(3, 2, True),
            Coord(4, 0, True),
            Coord(5, 0, True),
            Coord(5, 1, True),
            Coord(4, 2, False),
        }

        for c in [Coord(0, 0, True), Coord(2, 2, False)]:
            assert c not in board.all_coords
            with pytest.raises(ValueError):
                board.get_nbrs(c)
