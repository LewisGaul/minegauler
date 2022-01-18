# January 2022, Lewis Gaul

import contextlib
import logging
import pathlib
from unittest import mock

import pytest

import minegauler
import minegauler.shared.highscores

from . import PKG_DIR


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
        setattr(config.option, "markexpr", prefix + "not benchmark")


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
    logger.info("Creating testing sandbox, using tmpdir: %s", tmpdir)
    with contextlib.ExitStack() as ctxs:
        # Patch all paths relative to the root dir.
        for name, obj in vars(minegauler.paths).items():
            if not isinstance(obj, pathlib.Path) or name in ["IMG_DIR", "FILES_DIR"]:
                continue
            try:
                subpath = obj.relative_to(PKG_DIR)
            except ValueError:
                pass
            else:
                logger.debug("Patching %s with %s", name, tmpdir / subpath)
                ctxs.enter_context(
                    mock.patch.object(minegauler.paths, name, tmpdir / subpath)
                )

        ctxs.enter_context(
            mock.patch.object(
                minegauler.shared.highscores.HighscoresDatabases.REMOTE, "_value_"
            )
        )

        yield
