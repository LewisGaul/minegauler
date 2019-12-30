"""
integration_test.py - Integration test, aiming for all mainline code

December 2019, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k integration_test]' from
the root directory.
"""

import logging
import time
import types
from importlib.util import find_spec
from unittest import mock

from PyQt5.QtWidgets import QApplication

from minegauler import core, frontend


logger = logging.getLogger(__name__)


def test_basic_run():
    """
    Run the app using a manual processing of events.
    """

    def run_app(gui: frontend.MinegaulerGUI) -> int:
        logger.info("In run_app()")
        gui.show()
        return 0

    def process_events(wait: int = 0) -> None:
        start_time = time.time()
        while QApplication.hasPendingEvents():
            QApplication.processEvents()
        time.sleep(wait - (time.time() - start_time))

    logger.info("Executing __main__ without starting app event loop")
    main = types.ModuleType("minegauler.__main__")
    spec = find_spec("minegauler.__main__")
    loader = spec.loader
    with mock.patch("minegauler.frontend.run_app", run_app), mock.patch("sys.exit"):
        loader.exec_module(main)

    logger.info("Starting test checks")

    assert type(main.ctrlr) is core.BaseController
    assert type(main.gui) is frontend.MinegaulerGUI
    ctrlr: core.BaseController = main.ctrlr
    gui: frontend.MinegaulerGUI = main.gui
    assert gui._ctrlr is ctrlr

    process_events(1)
    ctrlr.select_cell((1, 2))
    process_events(1)
    ctrlr.select_cell((6, 4))
    process_events(1)
    ctrlr.resize_board(40, 1, 0)
    process_events(1)

    gui.close()
