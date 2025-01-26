# February 2022, Lewis Gaul

"""
Base classes and types for highscore handling.

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
from typing import Optional

import attrs
import attrs.validators as av
from typing_extensions import Self

from ..shared.types import Difficulty, GameMode, ReachSetting
from ..shared.utils import StructConstructorMixin


logger = logging.getLogger(__name__)


@attrs.frozen(kw_only=True)
class HighscoreSettings(StructConstructorMixin):
    """A set of highscore settings."""

    game_mode: GameMode = attrs.field(converter=GameMode.from_str)
    difficulty: Difficulty = attrs.field(converter=Difficulty.from_str)
    per_cell: int = attrs.field(validator=av.in_([1, 2, 3]))
    reach: ReachSetting = attrs.field(converter=ReachSetting)
    drag_select: bool = attrs.field(converter=bool)

    @classmethod
    def original(cls) -> Self:
        return cls(
            game_mode=GameMode.REGULAR,
            difficulty=Difficulty.BEGINNER,
            per_cell=1,
            reach=ReachSetting.NORMAL,
            drag_select=False,
        )


@attrs.frozen(kw_only=True)
class HighscoreStruct:  # TODO: Rename to just 'Highscore'
    """A single highscore."""

    settings: HighscoreSettings
    name: str
    timestamp: int = attrs.field(validator=av.gt(0))
    elapsed: float = attrs.field(validator=av.gt(0))
    bbbv: int = attrs.field(validator=av.gt(0))
    flagging: float = attrs.field(validator=av.and_(av.ge(0), av.le(1)))

    @property
    def bbbvps(self) -> float:
        return self.bbbv / self.elapsed

    @classmethod
    def flat_fields(cls) -> Iterable[str]:
        return (
            f.name
            for f in (*attrs.fields(HighscoreSettings), *attrs.fields(HighscoreStruct))
            if f.name != "settings"
        )

    @classmethod
    def from_flat_json(cls, data: dict[str, str | int | float | bool | None]) -> Self:
        return cls(
            settings=HighscoreSettings(
                **{f: data[f] for f in attrs.fields_dict(HighscoreSettings)}
            ),
            **{f: data[f] for f in attrs.fields_dict(cls) if f != "settings"},
        )

    def to_flat_json(self) -> dict[str, str | int | float | bool | None]:
        return {
            **attrs.asdict(self.settings),
            **attrs.asdict(self, filter=attrs.filters.exclude("settings")),
        }


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
