"""
utils.py - General utilities

December 2018, Lewis Gaul
"""

__all__ = ("StructConstructorMixin",)

import logging
from typing import Any, Dict

import attr


logger = logging.getLogger(__name__)


class StructConstructorMixin:
    """
    A mixin class adding methods for ways to create instances.
    """

    @classmethod
    def from_structs(cls, *structs):
        """
        Create an instance using namespace(s) containing the required fields.

        Later arguments take precedence.
        """
        dict_ = {}
        for struct in structs:
            dict_.update(attr.asdict(struct))
        return cls.from_dict(dict_)

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]):
        """
        Create an instance from a dictionary.

        Ignores extra attributes.
        """
        args = {a: v for a, v in dict_.items() if a in attr.fields_dict(cls)}
        return cls(**args)

    def copy(self):
        """
        Create and return a copy of the instance.

        This is a shallow copy.
        """
        return self.from_structs(self)
