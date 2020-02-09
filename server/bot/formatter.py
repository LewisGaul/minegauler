"""
formatter.py - Format bot messages

February 2020, Lewis Gaul
"""

__all__ = ("format_highscores",)

from typing import Iterable, Mapping

from minegauler.shared import highscores as hs


def format_highscores(highscores: Iterable[hs.HighscoreStruct]) -> str:
    lines = [f"{h.name:<15s}  {h.elapsed:.2f}" for h in highscores]
    return "\n".join(lines)


def format_kwargs(kwargs: Mapping) -> str:
    return ", ".join(f"{k}={v}" for k, v in kwargs.items())
