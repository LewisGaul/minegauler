# December 2019, Lewis Gaul

"""
Integration tests.

Aims to cover all mainline code.  # TODO - incomplete

"""

import logging
import os
import time
import types
from importlib.util import find_spec
from unittest import mock

from PyQt5.QtWidgets import QApplication

from minegauler import core, frontend


logger = logging.getLogger(__name__)


def _run_minegauler__main__() -> types.ModuleType:
    """
    Run minegauler via the __main__ module.

    :return:
        The __main__ module namespace.
    """
    module = types.ModuleType("minegauler.__main__")
    spec = find_spec("minegauler.__main__")
    spec.loader.exec_module(module)
    return module


class TestMain:
    """Test running minegauler in an IT way."""

    main_module: types.ModuleType
    ctrlr: core.BaseController
    gui: frontend.MinegaulerGUI

    @classmethod
    def setup_class(cls):
        """Set up the app to be run using manual processing of events."""

        def run_app(gui: frontend.MinegaulerGUI) -> int:
            logger.info("In run_app()")
            gui.show()
            return 0

        logger.info("Executing __main__ without starting app event loop")
        with mock.patch("minegauler.frontend.run_app", run_app), mock.patch("sys.exit"):
            cls.main_module = _run_minegauler__main__()

        cls.ctrlr = cls.main_module.ctrlr
        cls.gui = cls.main_module.gui

    @classmethod
    def teardown_class(cls):
        """Undo class setup."""

    def test_setup(self):
        """Test the setup is sane."""
        assert type(self.ctrlr) is core.BaseController
        assert type(self.gui) is frontend.MinegaulerGUI
        assert self.gui._ctrlr is self.ctrlr

    def test_play_game(self):
        """Test basic playing of a game."""
        self._process_events()
        self.ctrlr.select_cell((1, 2))
        self._process_events()
        self.ctrlr.select_cell((6, 4))
        self._process_events()

    def test_change_board(self):
        """Test changing the board."""
        self.ctrlr.resize_board(40, 1, 1)
        self._process_events()

    # -------------------------------------------
    # Helper methods
    # -------------------------------------------
    @staticmethod
    def _process_events() -> None:
        """
        Manually process Qt events (normally taken care of by the event loop).

        The environment variable TEST_IT_EVENT_WAIT can be used to set the
        amount of time to spend processing events (in seconds).
        """
        start_time = time.time()
        if os.environ.get("TEST_IT_EVENT_WAIT"):
            wait = float(os.environ["TEST_IT_EVENT_WAIT"])
        else:
            wait = 0
        QApplication.processEvents()
        while time.time() < start_time + wait:
            QApplication.processEvents()
