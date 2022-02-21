# January 2022, Lewis Gaul

__all__ = (
    "RAISED_CELL",
    "SUNKEN_CELL",
    "FlagAction",
    "MinefieldWidgetImplBase",
    "update_cell_images",
)

import abc
import enum
import logging
import os.path
from typing import Dict, Mapping, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QGraphicsScene

from ... import api, paths
from ...core.board import BoardBase
from ...shared.types import CellContents, CellImageType, Coord
from ..state import State


logger = logging.getLogger(__name__)

RAISED_CELL = CellContents.Unclicked
SUNKEN_CELL = CellContents.UnclickedSunken


def update_cell_images(
    cell_images: Dict[CellContents, QPixmap],
    size: int,
    styles: Mapping[CellImageType, str],
    required: CellImageType = CellImageType.ALL,
) -> None:
    """
    Initialise or update the pixmap images for the minefield cells.

    :param cell_images:
        The dictionary to fill with the created pixmap images.
    :param size:
        The size in pixels to make the image (square).
    :param styles:
        The image styles to use.
    :param required:
        Which image types require updating.
    """

    def get_path(subdir: str, style: str, fname: str, *, fallback: bool = True) -> str:
        base_path = paths.IMG_DIR / subdir
        full_path = base_path / style / fname
        if not full_path.exists() and fallback:
            logger.warning(f"Missing image file at {full_path}, using standard style")
            full_path = base_path / "Standard" / fname
        return str(full_path)

    btn_style = styles[CellImageType.BUTTONS]
    mkr_style = styles[CellImageType.MARKERS]
    num_style = styles[CellImageType.NUMBERS]

    if required & CellImageType.BUTTONS:
        cell_images[RAISED_CELL] = _make_pixmap(
            size, get_path("buttons", btn_style, "btn_up.png")
        )
        cell_images[SUNKEN_CELL] = _make_pixmap(
            size, get_path("buttons", btn_style, "btn_down.png")
        )
    if required & (CellImageType.BUTTONS | CellImageType.NUMBERS):
        for i in range(1, 19):
            cell_images[CellContents.Num(i)] = _make_pixmap(
                size,
                get_path("buttons", btn_style, "btn_down.png"),
                get_path("numbers", num_style, f"num{i}.png"),
                propn=7 / 8,
            )
        num0_path = get_path("numbers", num_style, f"num0.png", fallback=False)
        if os.path.exists(num0_path):
            cell_images[CellContents.Num(0)] = _make_pixmap(
                size,
                get_path("buttons", btn_style, "btn_down.png"),
                num0_path,
                propn=7 / 8,
            )
        else:
            cell_images[CellContents.Num(0)] = cell_images[SUNKEN_CELL]
    if required & (CellImageType.BUTTONS | CellImageType.MARKERS):
        for i in range(1, 4):
            cell_images[CellContents.Flag(i)] = _make_pixmap(
                size,
                get_path("buttons", btn_style, "btn_up.png"),
                get_path("markers", mkr_style, f"flag{i}.png"),
                propn=5 / 8,
            )
            cell_images[CellContents.WrongFlag(i)] = _make_pixmap(
                size,
                get_path("buttons", btn_style, "btn_up.png"),
                get_path("markers", mkr_style, f"cross{i}.png"),
                propn=5 / 8,
            )
            cell_images[CellContents.Mine(i)] = _make_pixmap(
                size,
                get_path("buttons", btn_style, "btn_down.png"),
                get_path("markers", mkr_style, f"mine{i}.png"),
                propn=7 / 8,
            )
            cell_images[CellContents.HitMine(i)] = _make_pixmap(
                size,
                get_path("buttons", btn_style, "btn_down_hit.png"),
                get_path("markers", mkr_style, f"mine{i}.png"),
                propn=7 / 8,
            )


def _make_pixmap(
    size: int,
    bg_path: str,
    fg_path: Optional[str] = None,
    *,
    propn: float = 1.0,
) -> QPixmap:
    """
    Create a compound pixmap image, superimposing a foreground over a background.

    :param size:
        The size to create the pixmap.
    :param bg_path:
        Path to background image.
    :param fg_path:
        Path to foreground image, if any.
    :param propn:
        Proportion of the foreground image over the background image.
    :return:
        The created pixmap image.
    """
    if fg_path:
        image = QImage(bg_path).scaled(
            size, size, transformMode=Qt.SmoothTransformation
        )
        fg_size = int(propn * size)
        overlay = QPixmap(fg_path).scaled(
            fg_size, fg_size, transformMode=Qt.SmoothTransformation
        )
        painter = QPainter(image)
        margin = int(size * (1 - propn) / 2)
        painter.drawPixmap(margin, margin, overlay)
        painter.end()
        image = QPixmap.fromImage(image)
    else:
        image = QPixmap(bg_path).scaled(
            size, size, transformMode=Qt.SmoothTransformation
        )
    return image


class FlagAction(enum.Enum):
    FLAG = enum.auto()
    UNFLAG = enum.auto()
    SPLIT = enum.auto()


class MinefieldWidgetImplBase(metaclass=abc.ABCMeta):
    """
    An implementation of the logic that's specific to the given game mode.
    """

    def __init__(
        self, scene: QGraphicsScene, ctrlr: api.AbstractController, state: State
    ):
        self._scene = scene
        self._ctrlr = ctrlr
        self._state = state

    @property
    def _board(self) -> BoardBase:
        return self._ctrlr.board

    @property
    def x_size(self) -> int:
        return self._state.x_size

    @property
    def y_size(self) -> int:
        return self._state.y_size

    @property
    def btn_size(self) -> int:
        return self._state.btn_size

    @abc.abstractmethod
    def set_cell_image(self, coord: Coord, state: CellContents) -> None:
        """Set the image of a cell on the scene."""
        raise NotImplementedError

    @abc.abstractmethod
    def update_cell_images(self, img_type: CellImageType = CellImageType.ALL) -> None:
        """Update the cache of cell images for current size/styles."""
        raise NotImplementedError

    @abc.abstractmethod
    def right_down_action(self, coord: Coord) -> FlagAction:
        """Perform a right click, returning the action that was taken."""
        raise NotImplementedError

    @abc.abstractmethod
    def right_drag_action(self, coord: Coord, action: FlagAction) -> None:
        """Perform a right drag click that matches the given action."""
        raise NotImplementedError
