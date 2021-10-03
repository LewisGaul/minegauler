# October 2021, Lewis Gaul

__all__ = ("ControllerBase",)

import abc
from typing import Generic, Type, TypeVar

from ..shared.types import GameMode
from .board import BoardBase
from .game import GameBase


M = TypeVar("M", bound=GameMode)


class ControllerBase(Generic[M], metaclass=abc.ABCMeta):
    """Base controller class, generic over game mode."""

    mode: M
    board_cls: Type[BoardBase[M]]
    game_cls: Type[GameBase]
