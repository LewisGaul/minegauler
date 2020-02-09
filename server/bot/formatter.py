"""
formatter.py - Format bot messages

February 2020, Lewis Gaul
"""

__all__ = (
    "format_highscores",
    "format_highscore_times",
    "format_kwargs",
    "format_matchups",
)

from typing import Dict, Iterable, List, Mapping

from minegauler.shared import highscores as hs

from .utils import Matchup


def format_highscores(highscores: Iterable[hs.HighscoreStruct]) -> str:
    return format_highscore_times([(h.name, h.elapsed) for h in highscores])


def format_highscore_times(highscores: Dict[str, float]) -> str:
    lines = [
        f"{i+1}. {h[0]:<15s}  {h[1]:.2f}" for i, h in enumerate(highscores.items())
    ]
    return "\n".join(lines)


def format_kwargs(kwargs: Mapping) -> str:
    return ", ".join(f"{k}={v}" for k, v in kwargs.items())


def format_matchups(matchups: Iterable[Matchup]) -> List[str]:
    return [
        "{} ({:.2f}) vs {} ({:.2f}) - {:.2f}% difference".format(*m) for m in matchups
    ]
