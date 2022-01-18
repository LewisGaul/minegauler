"""
Benchmark tests.

February 2020, Lewis Gaul
"""

import json
import tempfile
from types import ModuleType

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from minegauler import core, frontend
from minegauler.shared.types import CellContents

from . import process_events as _utils_process_events
from . import run_main_entrypoint


def process_events():
    _utils_process_events(0)


class ITBase:
    """Base class for IT, setting up the app."""

    main_module: ModuleType
    ctrlr: core.UberController
    gui: frontend.MinegaulerGUI

    @classmethod
    def setup_class(cls):
        """Set up the app to be run using manual processing of events."""
        cls.main_module = run_main_entrypoint()

        cls.ctrlr = cls.main_module.ctrlr
        cls.gui = cls.main_module.gui

    @classmethod
    def teardown_class(cls):
        """Undo class setup."""
        cls.gui.close()

    def load_minefield(self, mf: core.MinefieldBase) -> None:
        with tempfile.TemporaryFile() as tmp_file:
            with open(tmp_file, "w") as f:
                json.dump(mf.to_json(), f)
            self.ctrlr.load_minefield(tmp_file)


@pytest.mark.benchmark
class TestBenchmarks(ITBase):
    """Benchmark testcases."""

    def setup_method(self):
        self.ctrlr.resize_board(x_size=50, y_size=50, mines=1000)
        process_events()

    def test_new_game(self, benchmark: BenchmarkFixture):
        benchmark(self.ctrlr.new_game)

    def test_restart_game(self, benchmark: BenchmarkFixture):
        benchmark(self.ctrlr.restart_game)

    def test_flag_one_cell(self, benchmark: BenchmarkFixture):
        benchmark(self.ctrlr.flag_cell, (0, 0))

    def test_change_lots_of_cells(self, benchmark: BenchmarkFixture):
        # Create a board with a huge opening, but not resulting in the game
        # being completed in one click.
        checked = False

        def setup():
            nonlocal checked
            mf = core.board.Minefield(x_size=50, y_size=50, mines=[(1, 0)])
            if not checked:
                assert mf.completed_board[(0, 0)] == CellContents.Num(1)
                assert mf.completed_board[(1, 0)] == CellContents.Flag(1)
                assert mf.completed_board[(3, 3)] == CellContents.Num(0)
                checked = True
            self.load_minefield(mf)

        benchmark.pedantic(self.ctrlr.select_cell, ((3, 3),), setup=setup, rounds=10)

    def test_win_game(self, benchmark: BenchmarkFixture):
        # Create a basic one-click win situation.
        checked = False

        def setup():
            nonlocal checked
            mf = core.board.Minefield(x_size=2, y_size=1, mines=[(1, 0)])
            if not checked:
                assert mf.completed_board[(0, 0)] == CellContents.Num(1)
                assert mf.completed_board[(1, 0)] == CellContents.Flag(1)
                checked = True
            self.load_minefield(mf)

        benchmark.pedantic(self.ctrlr.select_cell, ((0, 0),), setup=setup)

    def test_lose_game(self, benchmark: BenchmarkFixture):
        # Create a basic one-click lose situation.
        checked = False

        def setup():
            nonlocal checked
            mf = core.board.Minefield(x_size=2, y_size=1, mines=[(1, 0)])
            if not checked:
                assert mf.completed_board[(0, 0)] == CellContents.Num(1)
                assert mf.completed_board[(1, 0)] == CellContents.Flag(1)
                checked = True
            self.load_minefield(mf)

        benchmark.pedantic(self.ctrlr.select_cell, ((1, 0),), setup=setup)
