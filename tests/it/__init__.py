# January 2022, Lewis Gaul

__all__ = ("EVENT_PAUSE", "process_events", "run_main_entrypoint")

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
    EVENT_PAUSE = float(os.environ["TEST_IT_EVENT_WAIT"])
except KeyError:
    EVENT_PAUSE = 0


def process_events(*, ignore_wait: bool = False) -> None:
    """
    Manually process Qt events (normally taken care of by the event loop).

    :param ignore_wait:
        Whether to ignore the default wait time when processing events.
    """
    wait = 0 if ignore_wait else EVENT_PAUSE
    logger.debug("Processing Qt events (pause of %.2fs)", wait)
    start_time = time.time()
    QApplication.processEvents()
    while time.time() - start_time < wait:
        QApplication.processEvents()
