"""
game.py - General utilities

March 2018, Lewis Gaul

Exports:
TODO
"""


import inspect
import json
import logging
import os
from inspect import Parameter
from os.path import abspath, dirname, join
from typing import Dict

import attr

from minegauler.shared.internal_types import CellImageType


logger = logging.getLogger(__name__)

root_dir = os.getcwd()

SETTINGS_FILE = join(root_dir, 'settings.cfg')


def get_dir_path(f):
    """
    Get the full path to the directory containing a file.

    Arguments:
    f (str)
        Filename or file path.

    Returns: str
        Full path to the directory containing the file.
    """
    return dirname(abspath(f))


def get_num_pos_args_accepted(func):
    """
    Determine how many positional args a function can take.

    Arguments:
    func (callable)
        The function to check.

    Returns:
    tuple (int, int)
        A tuple containing the minimum and maximum number of positional args the
        function can take.

    Raises:
        See inspect.signature().
    """
    params = inspect.signature(func).parameters.values()
    pos_params = [p for p in params if p.kind in
                  {Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD}]
    min_args = len([p for p in pos_params if p.default == Parameter.empty])
    max_args = len(pos_params)

    return min_args, max_args


class StructConstructorMixin:
    """
    A mixin class for creating a struct class from a dictionary or struct.

    Methods:
    _from_struct (classmethod)
        Create an instance from another structure-like object.
    _from_dict (classmethod)
        Create an instance from a dictionary.
    """
    @classmethod
    def _from_struct(cls, struct):
        """
        Create an instance of the structure by extracting element values from
        an object with any of the elements as attributes. Ignores extra
        attributes.
        """
        return cls._from_dict(attr.asdict(struct))

    @classmethod
    def _from_dict(cls, dict_):
        """
        Create an instance of the structure by extracting element values from
        a dictionary. Ignores extra attributes.
        """
        args = {a: v for a, v in dict_.items() if a in attr.fields_dict(cls)}
        return cls(**args)

    def copy(self):
        """
        Create and return a copy of the struct instance.
        """
        return self._from_struct(self)


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
    # game_mode: None = None,


@attr.attrs(auto_attribs=True)
class GuiOptsStruct(StructConstructorMixin):
    """
    Structure of GUI options.
    """
    btn_size: int = 16
    drag_select: bool = False
    styles: Dict[CellImageType, str] = {
        CellImageType.BUTTONS: 'Standard',
        CellImageType.NUMBERS: 'Standard',
        CellImageType.MARKERS: 'Standard',
    }


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
        ret['styles'] = {k.name: v for k, v in self.styles.items()}
        return ret

    @classmethod
    def decode_from_json(cls, dict_):
        dict_['styles'] = {getattr(CellImageType, k): v for k, v in
                           dict_['styles'].items()}
        return cls(**dict_)


def read_settings_from_file():
    read_settings = None
    try:
        with open(SETTINGS_FILE, 'r') as f:
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
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings.encode_to_json(), f)
    except Exception as e:
        logger.error("Unexpected error writing settings to file: %s", e)


def get_difficulty(x_size, y_size, mines):
    if x_size == 8 and y_size == 8 and mines == 10:
        return 'B'
    if x_size == 16 and y_size == 16 and mines == 40:
        return 'I'
    if x_size == 30 and y_size == 16 and mines == 99:
        return 'E'
    if x_size == 30 and y_size == 30 and mines == 200:
        return 'M'
    return 'C'