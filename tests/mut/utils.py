# December 2019, Lewis Gaul

"""
General test utils.

"""

__all__ = ("activate_patches", "make_true_mock", "patch_open")

import contextlib
import os
from typing import Iterable
from unittest import mock


@contextlib.contextmanager
def patch_open(file: os.PathLike, read_data: str):
    @contextlib.contextmanager
    def mock_open(path, *args, **kwargs):
        if path == file:
            open_func = mock.mock_open(read_data=read_data)
        else:
            open_func = open
        with open_func(path, *args, **kwargs) as f:
            yield f

    with mock.patch("builtins.open", mock_open) as m:
        yield m


@contextlib.contextmanager
def activate_patches(patches: Iterable):
    """
    Context manager to activate multiple mock patches.

    :param patches:
        Patches to start and stop.
    """
    mocks = []
    for patch in patches:
        mocks.append(patch.start())
    try:
        yield tuple(mocks)
    finally:
        for patch in patches:
            patch.stop()


def make_true_mock(cls: type) -> type:
    """Mock a class without breaking type checking."""

    class _Tmp(cls):
        __name__ = f"Mock{cls.__name__}"

        def __init__(self, *args, **kwargs):
            self._mock = mock.MagicMock()
            # Qt insists that the superclass's __init__() method is called...
            super().__init__(*args, **kwargs)
            self.__setattr__ = self._mock.__setattr__

        def __repr__(self):
            return self._mock.__repr__()

        def __getattribute__(self, item):
            if item in ["_mock", "__init__"]:
                return super().__getattribute__(item)
            return getattr(self._mock, item)

    return _Tmp
