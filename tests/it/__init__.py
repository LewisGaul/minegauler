# January 2022, Lewis Gaul

__all__ = ("process_events", "run_main_entrypoint")

import logging
import os
import time
import types

from PyQt6.QtWidgets import QApplication


logger = logging.getLogger(__name__)


def run_main_entrypoint() -> types.ModuleType:
    """
    Run minegauler via the __main__ module.

    :return:
        The __main__ module namespace.
    """
    import minegauler.app.__main__ as main_module

    main_module.main()
    return main_module


try:
    _EVENT_PAUSE = float(os.environ["TEST_IT_EVENT_WAIT"])
except KeyError:
    _EVENT_PAUSE = 0


def process_events(wait: float = _EVENT_PAUSE) -> None:
    """
    Manually process Qt events (normally taken care of by the event loop).

    :param wait:
        The amount of time to spend processing events (in seconds).
    """
    logger.debug("Processing Qt events (pause of %.2fs)", wait)
    start_time = time.time()
    QApplication.processEvents()
    while time.time() - start_time < wait:
        QApplication.processEvents()
