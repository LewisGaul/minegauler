"""
integration_test.py - Integration test, aiming for all mainline code

December 2019, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k integration_test]' from
the root directory.
"""

import threading
import time
import types
from importlib.util import find_spec


def test_basic_run():
    main = types.ModuleType("minegauler.__main__")

    def _run():
        spec = find_spec("minegauler.__main__")
        loader = spec.loader
        loader.exec_module(main)

    thread = threading.Thread(target=_run)
    thread.start()

    time.sleep(1)

    main.gui.close()

    thread.join()
