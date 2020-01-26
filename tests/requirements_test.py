"""
requirements_test.py - Test the requirements

October 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k requirements_test]' from
the root directory.
"""

import pathlib

import pkg_resources
from pip import __version__ as pip_version
from pip._internal.req import parse_requirements


if int(pip_version[:2]) < 20:
    from pip._internal.download import PipSession
else:
    from pip._internal.network.session import PipSession


class TestRequirements:
    def test_requirements(self):
        """
        Recursively confirm that requirements are available.
        """
        reqs_path = pathlib.Path(__file__).parents[1] / "requirements.txt"
        reqs = parse_requirements(str(reqs_path), session=PipSession())
        reqs = [str(r.req) for r in reqs]
        pkg_resources.require(reqs)
