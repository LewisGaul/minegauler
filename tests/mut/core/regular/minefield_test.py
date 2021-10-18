# October 2021, Lewis Gaul

import textwrap

import pytest

from minegauler.core.regular.board import Board
from minegauler.core.regular.minefield import Minefield
from minegauler.core.regular.types import Coord


class TestRegularMinefield:
    """Test the regular minefield."""

    x, y = 4, 3
    mines = 5
    per_cell = 2

    @property
    def coords(self):
        return {Coord(i, j) for i in range(self.x) for j in range(self.y)}

    @pytest.fixture
    def mf(self) -> Minefield:
        return Minefield(self.coords, mines=self.mines, per_cell=self.per_cell)

    # --------------------------------------------------------------------------
    # Test cases
    # --------------------------------------------------------------------------
    def test_init_basic(self):
        """Check basic init."""
        mf = Minefield(self.coords, mines=self.mines, per_cell=self.per_cell)
        assert (mf.x_size, mf.y_size) == (self.x, self.y)
        assert mf.mines == self.mines
        assert mf.per_cell == self.per_cell
        assert set(mf.all_coords) == self.coords
        assert len(mf.mine_coords) == 0
        assert not mf.populated

    def test_from_dimensions(self):
        """Check init from dimensions."""
        mf = Minefield.from_dimensions(self.x, self.y, mines=self.mines)
        assert (mf.x_size, mf.y_size) == (self.x, self.y)
        assert mf.mines == self.mines
        assert mf.per_cell == 1
        assert set(mf.all_coords) == self.coords
        assert len(mf.mine_coords) == 0

    def test_init_too_many_mines_error(self):
        """Check init error passing too many mines."""
        with pytest.raises(ValueError):
            Minefield(self.coords, mines=len(self.coords), per_cell=1)

    def test_init_negative_mines_error(self):
        """Check init error with mines < 1."""
        with pytest.raises(ValueError):
            Minefield(self.coords, mines=-1)

    def test_init_non_pos_per_cell_error(self):
        """Check init error with per_cell < 1."""
        with pytest.raises(ValueError):
            Minefield(self.coords, mines=self.mines, per_cell=0)

    def test_unpopulated_error(self, mf):
        """Check error is raised if trying to access info on unpopulated mf."""
        with pytest.raises(AttributeError):
            mf.bbbv
        with pytest.raises(AttributeError):
            mf.completed_board
        with pytest.raises(AttributeError):
            mf.openings

    def test_populate_basic(self, mf):
        """Check basic populate."""
        mf.populate()
        assert mf.populated
        assert len(mf.mine_coords) == mf.mines

    def test_populate_with_safe_coords(self):
        """Check populating a minefield with coords kept safe."""
        mf = Minefield({Coord(0, 0), Coord(0, 1), Coord(0, 2)}, mines=1)
        safe_coords = {Coord(0, 0), Coord(0, 1)}
        mf.populate(safe_coords)
        assert mf.populated
        assert mf.mine_coords == [Coord(0, 2)]

    def test_populate_too_many_mines_error(self):
        """Check populate error - too many mines for safe coords."""
        safe_coords = {Coord(0, 0), Coord(0, 1)}
        mf = Minefield(self.coords, mines=len(self.coords) - 1, per_cell=1)
        with pytest.raises(ValueError):
            mf.populate(safe_coords)
        assert not mf.populated

    def test_no_mines(self):
        """Check creating a minefield with no mines."""
        mf = Minefield(self.coords, mines=0)
        mf.populate()
        assert mf.bbbv == 1
        assert mf.mine_coords == []
        assert mf.populated

    def test_one_space_single_mine(self):
        """Check populating a minefield with only one space, 1 per cell."""
        mf = Minefield(self.coords, mines=self.x * self.y - 1)
        mf.populate()
        assert mf.bbbv == 1
        assert mf.openings == []

    def test_one_space_multiple_mine(self):
        """Check populating a minefield with only one space, high per cell."""
        mf = Minefield(self.coords, mines=5 * (self.x * self.y - 1), per_cell=5)
        mf.populate()
        assert mf.bbbv == 1
        assert mf.openings == []
        assert len(set(mf.all_coords) - set(mf.mine_coords)) == 1  # One safe cell
        assert all(mf.mine_coords.count(c) == 5 for c in mf.mine_coords)

    def test_from_coords(self):
        """Test basic create from mine coords."""
        mine_coords = [Coord(*c) for c in ((0, 0), (0, 1), (0, 1), (2, 2))]
        mf = Minefield.from_coords(self.coords, mine_coords=mine_coords, per_cell=2)
        assert mf.mine_coords == mine_coords
        assert mf.mines == len(mine_coords)
        assert mf.per_cell == 2
        exp_board = Board.from_2d_array(
            [
                # fmt: off
                ["F1", 3,  0,   0],
                ["F2", 4,  1,   1],
                [ 2,   3, "F1", 1],
                # fmt: on
            ]
        )
        assert mf.completed_board == exp_board
        assert mf.bbbv == 4
        assert mf.openings == [[(1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)]]
        assert mf[Coord(0, 0)] == 1
        assert mf[Coord(0, 1)] == 2
        assert mf[Coord(1, 1)] == 0

    def test_from_coords_too_many_per_cell_error(self):
        """Check passing in too many mines in a cell."""
        mine_coords = [Coord(0, 0), Coord(0, 0)]
        with pytest.raises(ValueError):
            Minefield.from_coords(self.coords, mine_coords=mine_coords, per_cell=1)

    def test_stringify(self, mf):
        """Get coverage of stringify methods."""
        mine_coords = [Coord(*c) for c in ((0, 0), (0, 0), (0, 1))]
        mf = Minefield.from_coords(
            self.coords, mine_coords=mine_coords, per_cell=self.per_cell
        )
        assert repr(mf) == "<4x3 minefield with 3 mines>"
        assert str(mf) == textwrap.dedent(
            """\
            2 0 0 0
            1 0 0 0
            0 0 0 0"""
        )

    def test_getitem(self):
        """Check getitem behaviour."""
        mf = Minefield(self.coords, mines=self.mines)
        assert mf[Coord(0, 0)] == mf.mine_coords.count(Coord(0, 0))
        with pytest.raises(IndexError):
            mf[Coord(10, 10)]
