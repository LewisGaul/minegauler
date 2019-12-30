"""
utils.py - General utilities

December 2018, Lewis Gaul
"""

import json
import logging
from typing import Any, Dict

import attr

from . import SETTINGS_FILE
from .types import *


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


@attr.attrs(auto_attribs=True)
class GameOptsStruct(StructConstructorMixin):
    """
    Structure of game options.
    """

    x_size: int = 8
    y_size: int = 8
    mines: int = 10
    first_success: bool = True
    per_cell: int = 1
    lives: int = 1


@attr.attrs(auto_attribs=True)
class GuiOptsStruct(StructConstructorMixin):
    """
    Structure of GUI options.
    """

    btn_size: int = 16
    drag_select: bool = False
    name: str = ""
    styles: Dict[CellImageType, str] = {
        CellImageType.BUTTONS: "Standard",
        CellImageType.NUMBERS: "Standard",
        CellImageType.MARKERS: "Standard",
    }


@attr.attrs(auto_attribs=True)
class AllOptsStruct(GameOptsStruct, GuiOptsStruct):
    """
    Structure containing all application options.
    """

    def encode_to_json(self) -> Dict[str, Any]:
        ret = attr.asdict(self)
        ret["styles"] = {k.name: v for k, v in self.styles.items()}
        return ret

    @classmethod
    def decode_from_json(cls, dict_: Dict[str, Any]) -> "AllOptsStruct":
        dict_["styles"] = {
            getattr(CellImageType, k): v for k, v in dict_["styles"].items()
        }
        return cls(**dict_)


def read_settings_from_file():
    read_settings = None
    try:
        with open(SETTINGS_FILE, "r") as f:
            read_settings = AllOptsStruct.decode_from_json(json.load(f))
    except FileNotFoundError:
        logger.info("Settings file not found")
    except json.JSONDecodeError:
        logger.warning("Unable to decode settings from file")
    except Exception as e:
        logger.warning("Unexpected error reading settings from file")
        logger.debug("%s", e)

    return read_settings


def write_settings_to_file(settings: AllOptsStruct) -> None:
    logger.info("Saving settings to file: %s", SETTINGS_FILE)
    logger.debug("%s", settings)
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings.encode_to_json(), f, indent=2)
    except Exception as e:
        logger.exception("Unexpected error writing settings to file")


def get_difficulty(x_size: int, y_size: int, mines: int) -> str:
    """Get the difficulty code based on the board dimensions and mines."""
    if x_size == 8 and y_size == 8 and mines == 10:
        return "B"
    elif x_size == 16 and y_size == 16 and mines == 40:
        return "I"
    elif x_size == 30 and y_size == 16 and mines == 99:
        return "E"
    elif x_size == 30 and y_size == 30 and mines == 200:
        return "M"
    else:
        return "C"


def is_flagging_threshold(proportion: float) -> bool:
    """Does the given proportion correspond to a board solved with 'flagging'?"""
    return proportion > 0.1
