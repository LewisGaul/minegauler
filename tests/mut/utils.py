# December 2019, Lewis Gaul

"""
General test utils.

"""

import contextlib
from typing import Iterable
from unittest import mock


@contextlib.contextmanager
def activate_patches(patches: Iterable[mock._patch]):
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

        def __getattribute__(self, item):
            if item in ["_mock", "__init__"]:
                return super().__getattribute__(item)
            return getattr(self._mock, item)

        def __setattribute__(self, key, value):
            if key == "_mock":
                return super().__setattribute__(key, value)
            setattr(self._mock, key, value)

    return _Tmp
