import os

import pytest

from . import EVENT_PAUSE


@pytest.fixture(scope="session", autouse=True)
def _env_vars() -> None:
    if not EVENT_PAUSE:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
