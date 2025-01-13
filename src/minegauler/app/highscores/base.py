# February 2022, Lewis Gaul

"""
Base classes/implementations for highscore handling.

"""

from __future__ import annotations


__all__ = (
    "HighscoreSettings",
    "HighscoreStruct",
    "HighscoresDB",
)

import abc
import logging
from collections.abc import Iterable
from typing import Optional, Union

import attrs

from ..shared.types import Difficulty, GameMode, ReachSetting
from ..shared.utils import StructConstructorMixin


logger = logging.getLogger(__name__)


@attrs.frozen
class HighscoreSettings(StructConstructorMixin):
    """A set of highscore settings."""

    game_mode: GameMode = attrs.field(converter=GameMode.from_str)
    difficulty: Difficulty = attrs.field(converter=Difficulty.from_str)
    per_cell: int
    reach: ReachSetting = attrs.field(converter=ReachSetting)
    drag_select: bool = attrs.field(converter=bool)

    @classmethod
    def get_default(cls) -> HighscoreSettings:
        return cls(GameMode.REGULAR, Difficulty.BEGINNER, 1, ReachSetting.NORMAL, False)


@attrs.frozen
class HighscoreStruct(HighscoreSettings):
    """A single highscore."""

    name: str
    timestamp: int
    elapsed: float
    bbbv: int
    bbbvps: float
    flagging: float

    def to_row(self) -> tuple[Union[int, float, str], ...]:
        return (
            self.difficulty.value,
            self.per_cell,
            self.reach.value,
            int(self.drag_select),
            self.name,
            self.timestamp,
            self.elapsed,
            self.bbbv,
            self.bbbvps,
            self.flagging,
        )


class HighscoresDB(abc.ABC):
    """Abstract base class for a highscores database."""

    @abc.abstractmethod
    def get_highscores(
        self,
        *,
        game_mode: Optional[GameMode] = None,
        difficulty: Optional[Difficulty] = None,
        per_cell: Optional[int] = None,
        reach: Optional[ReachSetting] = None,
        drag_select: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Iterable[HighscoreStruct]:
        """Fetch highscores from the database using the given filters."""

    @abc.abstractmethod
    def count_highscores(self) -> int:
        """Count the number of rows in the highscores table."""

    @abc.abstractmethod
    def insert_highscores(self, highscores: Iterable[HighscoreStruct]) -> int:
        """Insert highscores into the database."""
