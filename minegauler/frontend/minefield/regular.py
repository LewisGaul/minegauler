# October 2021, Lewis Gaul

__all__ = ("MinefieldWidget",)

from minegauler.core.regular import GameController

from .base import MinefieldWidgetBase


class MinefieldWidget(MinefieldWidgetBase):
    """
    Minefield widget for regular game.
    """

    ctrlr_cls = GameController
