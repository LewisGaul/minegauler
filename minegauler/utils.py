"""
utils.py - Utilities for the frontend.

December 2018, Lewis Gaul
"""

import json
import logging

import attr

from minegauler import SETTINGS_FILE
from minegauler.core import GameOptsStruct
from minegauler.frontend import GuiOptsStruct
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


def write_settings_to_file(settings: PersistSettingsStruct):
    logger.info("Saving settings to file: %s", SETTINGS_FILE)
    logger.debug("%s", settings)
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings.encode_to_json(), f)
    except Exception as e:
        logger.error("Unexpected error writing settings to file: %s", e)
