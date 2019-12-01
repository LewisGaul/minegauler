"""
utils.py - Utilities for the frontend.

December 2018, Lewis Gaul
"""

import json
import logging

import attr

from minegauler import SETTINGS_FILE
from minegauler.core.utils import GameOptsStruct
from minegauler.frontend.utils import GuiOptsStruct
from minegauler.types import *


logger = logging.getLogger(__name__)


@attr.attrs(auto_attribs=True)
class PersistSettingsStruct(GameOptsStruct, GuiOptsStruct):
    """
    Strucure of settings to be persisted when closing the app.
    """

    @classmethod
    def _from_multiple_structs(cls, *args):
        """
        Construct an instance of the class using multiple struct instances.
        Later arguments take precedence over earlier.
        """
        dict_ = {}
        for struct in args:
            dict_.update(attr.asdict(struct))
        return cls._from_dict(dict_)

    def encode_to_json(self):
        ret = attr.asdict(self)
        ret["styles"] = {k.name: v for k, v in self.styles.items()}
        return ret

    @classmethod
    def decode_from_json(cls, dict_):
        dict_["styles"] = {
            getattr(CellImageType, k): v for k, v in dict_["styles"].items()
        }
        return cls(**dict_)


def read_settings_from_file():
    read_settings = None
    try:
        with open(SETTINGS_FILE, "r") as f:
            read_settings = PersistSettingsStruct.decode_from_json(json.load(f))
    except FileNotFoundError:
        logger.info("Settings file not found")
    except json.JSONDecodeError:
        logger.warning("Unable to decode settings from file")
    except Exception as e:
        logger.warning("Unexpected error reading settings from file")
        logger.debug("%s", e)

    return read_settings


def write_settings_to_file(settings: PersistSettingsStruct) -> None:
    logger.info("Saving settings to file: %s", SETTINGS_FILE)
    logger.debug("%s", settings)
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings.encode_to_json(), f, indent=2)
    except Exception as e:
        logger.exception("Unexpected error writing settings to file")


def get_difficulty(x_size: int, y_size: int, mines: int) -> str:
    if x_size == 8 and y_size == 8 and mines == 10:
        return "B"
    if x_size == 16 and y_size == 16 and mines == 40:
        return "I"
    if x_size == 30 and y_size == 16 and mines == 99:
        return "E"
    if x_size == 30 and y_size == 30 and mines == 200:
        return "M"
    return "C"
