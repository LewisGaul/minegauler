__all__ = ("format_highscores",)

from typing import Iterable

from minegauler.shared import highscores as hs


def format_highscores(highscores: Iterable[hs.HighscoreStruct]) -> str:
    lines = [f"{h.name:<15s}  {h.elapsed:.2f}" for h in highscores]
    return "\n".join(lines)
