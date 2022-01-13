# March 2018, Lewis Gaul

"""
General utilities.

Exports
-------
.. class:: AllOptsStruct
    A structure class containing all persisted options.

.. class:: GUIOptsStruct
    A structure class containing persisted GUI options.

.. class:: GameOptsStruct
    A structure class containing persisted game options.

.. class:: Grid
    Representation of a 2D array.

.. class:: StructConstructorMixin
    A mixin for structure classes.

.. function:: format_timestamp
    Format a timestamp.

.. function:: is_flagging_threshold
    Check whether flagging threshold is met.

.. function:: read_settings_from_file
    Read persisted settings.

.. function:: write_settings_to_file
    Persist settings to file.

"""

__all__ = (
    "AllOptsStruct",
    "GUIOptsStruct",
    "GameOptsStruct",
    "Grid",
    "StructConstructorMixin",
    "format_timestamp",
    "is_flagging_threshold",
    "read_settings_from_file",
    "write_settings_to_file",
)

import json
import logging
import os
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import attr

from .. import paths
from .types import CellImageType, GameMode, PathLike


logger = logging.getLogger(__name__)


class Grid(list):
    """
    Grid representation using a list of lists (2D array).

    Attributes:
    x_size (int > 0)
        The number of columns.
    y_size (int > 0)
        The number of rows.
    all_coords ([(int, int), ...])
        List of all coordinates in the grid.
    """

    def __init__(self, x_size: int, y_size: int, *, fill: Any = 0):
        """
        Arguments:
        x_size (int > 0)
            The number of columns.
        y_size (int > 0)
            The number of rows.
        fill=0 (object)
            What to fill the grid with.
        """
        super().__init__()
        for j in range(y_size):
            row = x_size * [fill]
            self.append(row)
        self.x_size: int = x_size
        self.y_size: int = y_size
        self.all_coords: List[Tuple[int, int]] = [
            (x, y) for x in range(x_size) for y in range(y_size)
        ]

    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} grid>"

    def __str__(self, mapping=None, cell_size=None):
        """
        Convert the grid to a string in an aligned format. The __repr__ method
        is used to display the objects inside the grid unless the mapping
        argument is given.

        Arguments:
        mapping=None (dict | callable | None)
            A mapping to apply to all objects contained within the grid. The
            result of the mapping will be converted to a string and displayed.
            If a mapping is specified, a cell size should also be given.
        cell_size=None (int | None)
            The size to display a grid cell as. Defaults to the maximum size of
            the representation of all the objects contained in the grid.
        """
        # @@@LG Some attention please :)

        # Use max length of object representation if no cell size given.
        if cell_size is None:
            cell_size = max([len(repr(obj)) for row in self for obj in row])

        cell = "{:>%d}" % cell_size
        ret = ""
        for row in self:
            for obj in row:
                if isinstance(mapping, dict):
                    rep = str(mapping[obj]) if obj in mapping else repr(obj)
                elif mapping is not None:
                    rep = str(mapping(obj))
                else:
                    rep = repr(obj)
                ret += cell.format(rep[:cell_size]) + " "
            ret = ret[:-1]  # Remove trailing space
            ret += "\n"
        ret = ret[:-1]  # Remove trailing newline

        return ret

    def __getitem__(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            x, y = key
            return super().__getitem__(y)[x]
        else:
            raise TypeError("Grid keys should be tuple coordinates of the form (0, 1)")

    def __setitem__(self, key, value):
        if isinstance(key, tuple) and len(key) == 2:
            x, y = key
            super().__getitem__(y)[x] = value
        else:
            raise TypeError("Grid keys should be tuple coordinates of the form (0, 1)")

    @classmethod
    def from_2d_array(cls, array):
        """
        Create an instance using a 2-dimensional array.

        Arguments:
        array ([[object, ...], ...])
            The array to use in creating the grid instance.

        Return: Grid
            The resulting grid.
        """
        x_size = len(array[0])
        y_size = len(array)
        grid = cls(x_size, y_size)
        for coord in grid.all_coords:
            x, y = coord
            grid[coord] = array[y][x]
        return grid

    def fill(self, item):
        """
        Fill the grid with a given object.

        Arguments:
        item (object)
            The item to fill the grid with.
        """
        for row in self:
            for i in range(len(row)):
                row[i] = item

    def get_nbrs(
        self, coord: Tuple[int, int], *, include_origin=False
    ) -> Iterable[Tuple[int, int]]:
        """
        Get a list of the coordinates of neighbouring cells.

        Arguments:
        coord ((int, int), within grid boundaries)
            The coordinate to check.
        include_origin=False (bool)
            Whether to include the original coordinate, coord, in the list.

        Return: [(int, int), ...]
            List of coordinates within the boundaries of the grid.
        """
        x, y = coord
        nbrs = []
        for i in range(max(0, x - 1), min(self.x_size, x + 2)):
            for j in range(max(0, y - 1), min(self.y_size, y + 2)):
                nbrs.append((i, j))
        if not include_origin:
            nbrs.remove(coord)
        return nbrs

    def copy(self):
        ret = Grid(self.x_size, self.y_size)
        for coord in self.all_coords:
            ret[coord] = self[coord]
        return ret

    def is_coord_in_grid(self, coord: Tuple[int, int]) -> bool:
        x, y = coord
        return 0 <= x < self.x_size and 0 <= y < self.y_size


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
    mode: GameMode = GameMode.REGULAR


@attr.attrs(auto_attribs=True)
class GUIOptsStruct(StructConstructorMixin):
    """
    Structure of GUI options.
    """

    btn_size: int = 16
    drag_select: bool = False
    name: str = ""
    styles: Mapping[CellImageType, str] = {
        CellImageType.BUTTONS: "Standard",
        CellImageType.NUMBERS: "Standard",
        CellImageType.MARKERS: "Standard",
    }


@attr.attrs(auto_attribs=True)
class AllOptsStruct(GameOptsStruct, GUIOptsStruct):
    """
    Structure containing all application options.
    """

    def encode_to_json(self) -> Dict[str, Any]:
        ret = attr.asdict(self)
        ret["styles"] = {k.name: v for k, v in self.styles.items()}
        ret["mode"] = ret["mode"].name
        return ret

    @classmethod
    def decode_from_json(cls, dict_: Dict[str, Any]) -> "AllOptsStruct":
        dict_["styles"] = {
            getattr(CellImageType, k): v for k, v in dict_["styles"].items()
        }
        dict_["mode"] = getattr(GameMode, dict_.get("mode", "REGULAR"))
        return cls(**dict_)


def is_flagging_threshold(proportion: float) -> bool:
    """Does the given proportion correspond to a board solved with 'flagging'?"""
    return proportion > 0.1


def read_settings_from_file(file: os.PathLike) -> Optional[AllOptsStruct]:
    logger.info("Reading settings from file: %s", file)

    read_settings = None
    try:
        with open(file, "r") as f:
            read_settings = AllOptsStruct.decode_from_json(json.load(f))
    except FileNotFoundError:
        logger.info("Settings file not found")
    except json.JSONDecodeError:
        logger.warning("Unable to decode settings from file")
    except Exception:
        logger.warning("Unexpected error reading settings from file", exc_info=True)

    return read_settings


def write_settings_to_file(settings: AllOptsStruct, file: PathLike) -> None:
    logger.info("Saving settings to file: %s", file)
    logger.debug("%s", settings)
    try:
        with open(file, "w") as f:
            json.dump(settings.encode_to_json(), f, indent=2)
    except Exception:
        logger.exception("Unexpected error writing settings to file")


def format_timestamp(timestamp: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
