"""
utils.py - General utilities

March 2018, Lewis Gaul

Exports:
AbstractStruct (class)
    Abstract structure class for storing data together. Intended to behave
    similarly to C structs by disallowing monkey-patching.
"""


import inspect
import json
import logging
import os
from inspect import Parameter
from os.path import abspath, dirname, join

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


class AbstractStruct(dict):
    """
    Abstract structure class, used to store related data. Elements can be
    accessed via attributes or dictionary-style keys. Only elements given in
    'elements' can be used, otherwise KeyError/AttributeError will be raised.
    
    Attributes:
    _elements (dict)
        Mapping of element names to their default values.

    Methods:
    _from_struct (classmethod)
        Create an instance from another structure-like object.
    """

    _elements = {}

    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            self[k] = v
        for k, v in self._elements.items():
            if k not in self:
                self[k] = v
                
    def __new__(cls, **kwargs):
        if cls == AbstractStruct:
            raise TypeError("Cannot instantiate base structure class directly")
        return super().__new__(cls)
                
    def __getitem__(self, name):
        if name in self._elements:
            if name in self:
                return super().__getitem__(name)
            else:
                return None
        else:
            raise KeyError("Unexpected element")
            
    def __setitem__(self, name, value):
        if name in self._elements:
            super().__setitem__(name, value)
        else:
            raise KeyError("Unexpected element")
            
    def __getattr__(self, name):
        if name in self._elements:
            return self[name]
        else:
            raise AttributeError("Unexpected element")
            
    def __setattr__(self, name, value):
        if name in self._elements:
            self[name] = value
        else:
            raise AttributeError("Unexpected element")

    def copy(self):
        return self.__class__(**self)

    @classmethod
    def _from_struct(cls, struct):
        """
        Create an instance of the structure by extracting element values from
        an object with any of the elements as attributes. Ignores extra
        attributes.
        """
        ret = cls()
        for elem in cls._elements:
            if hasattr(struct, elem):
                ret[elem] = getattr(struct, elem)

        return ret

    @classmethod
    def _from_dict(cls, dict_):
        """
        Create an instance of the structure by extracting element values from
        an object with any of the elements retrievable with __getitem__.
        Ignores extra attributes.
        """
        ret = cls()
        for elem in cls._elements:
            try:
                ret[elem] = dict_[elem]
            except KeyError:
                pass

        return ret


class GameOptsStruct(AbstractStruct):
    """
    Structure of game options.
    """
    _elements = {
        'x_size':        8,
        'y_size':        8,
        'mines':         10,
        'first_success': True,
        'per_cell':      1,
        'lives':         1,
        # 'game_mode':     None,
    }


class GUIOptsStruct(AbstractStruct):
    _elements = {'btn_size'   : 32,
                 'styles'     : {CellImageType.BUTTONS: 'Standard',
                                 CellImageType.NUMBERS: 'Standard',
                                 CellImageType.MARKERS: 'Standard'},
                 'drag_select': False}


class PersistSettingsStruct(AbstractStruct):

    _elements = {**GameOptsStruct._elements, **GUIOptsStruct._elements}

    def encode_to_json(self):
        ret = dict(self)
        ret['styles'] = {k.name: v for k, v in self['styles'].items()}

        return ret

    @classmethod
    def decode_from_json(cls, dict_):
        dict_['styles'] = {getattr(CellImageType, k): v for k, v in
                           dict_['styles'].items()}

        return cls._from_dict(dict_)


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


def write_settings_to_file(settings):
    logger.info("Saving settings to file: %s", SETTINGS_FILE)
    logger.debug("%s", settings)
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(PersistSettingsStruct.encode_to_json(settings), f)
    except Exception as e:
        logger.warning("Unexpected error writing settings to file: %s", e)


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