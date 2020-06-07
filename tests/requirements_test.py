"""
Test the package requirements are installed.

October 2018, Lewis Gaul
"""

import pathlib
from typing import List

import pkg_resources
from pip import __version__ as pip_version_str


pip_version = float(".".join(pip_version_str.split(".")[:2]))


def parse_requirements(path) -> List[str]:
    assert pip_version >= 19
    from pip._internal.req import parse_requirements

    try:
        from pip._internal.download import PipSession
    except ImportError:
        from pip._internal.network.session import PipSession

    reqs = parse_requirements(str(path), session=PipSession())
    try:
        return [r.requirement for r in reqs]
    except AttributeError:
        return [str(r.req) for r in reqs]


def test_requirements():
    """Check requirements are available."""
    reqs_path = pathlib.Path(__file__).parents[1] / "requirements.txt"
    pkg_resources.require(parse_requirements(reqs_path))
