"""
requirements_test.py - Test the requirements

October 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k requirements_test]' from
the root directory.
"""

import functools
import pathlib
from typing import Callable

import pkg_resources
import pytest


@pytest.fixture()
def get_pip_reqs():
    from pip import __version__ as pip_version
    assert float(pip_version[:2]) >= 19
    from pip._internal.req import parse_requirements

    if int(pip_version[:2]) < 20:
        from pip._internal.download import PipSession
    else:
        from pip._internal.network.session import PipSession

    return functools.partial(parse_requirements, session=PipSession)


class TestRequirements:
    def test_requirements(self, get_pip_reqs: Callable):
        """
        Recursively confirm that requirements are available.
        """
        reqs_path = pathlib.Path(__file__).parents[1] / "requirements.txt"
        reqs = [str(r.req) for r in get_pip_reqs(str(reqs_path))]
        pkg_resources.require(reqs)
