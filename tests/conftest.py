# January 2022, Lewis Gaul

import contextlib
import logging
import os
import pathlib
import threading
from unittest import mock

import pytest

import minegauler.app
import minegauler.app.highscores

from . import APP_DIR


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Pytest run options
# ------------------------------------------------------------------------------


def pytest_addoption(parser):
    parser.addoption("--benchmark", action="store_true", help="run benchmark tests")


def pytest_configure(config):
    # Handle (lack of) --benchmark CLI arg.
    if not config.option.benchmark:
        if getattr(config.option, "markexpr", None):
            prefix = config.option.markexpr + " and "
        else:
            prefix = ""
        config.option.markexpr = prefix + "not benchmark"


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def sandbox(tmpdir_factory: pytest.TempdirFactory):
    """
    Create a sandbox for testing the app.

    Must run before importing any minegauler submodules.
    """
    tmpdir = tmpdir_factory.mktemp("sandbox")
    os.chdir(tmpdir)
    logger.info("Creating testing sandbox, using tmpdir: %s", tmpdir)
    with contextlib.ExitStack() as ctxs:
        # Patch all paths relative to the root dir.
        for name, obj in vars(minegauler.app.paths).items():
            if not isinstance(obj, pathlib.Path) or name in ["IMG_DIR", "FILES_DIR"]:
                continue
            try:
                subpath = obj.relative_to(APP_DIR)
            except ValueError:
                pass
            else:
                logger.debug("Patching %s with %s", name, tmpdir / subpath)
                ctxs.enter_context(
                    mock.patch.object(minegauler.app.paths, name, tmpdir / subpath)
                )

        # Ensure no posting of highscores!
        logger.debug("Patching requests.post()")
        ctxs.enter_context(mock.patch("requests.post"))

        yield


@pytest.fixture
def sync_threads() -> None:
    """Make threaded code run synchronously."""

    class MockThread(threading.Thread):
        def start(self) -> None:
            self._target()

    with mock.patch("threading.Thread", MockThread):
        yield
