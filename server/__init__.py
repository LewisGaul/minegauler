__all__ = ("add_new_highscore_hook", "get_new_highscore_hooks", "utils")

from typing import Callable, Iterable

from minegauler.shared import highscores as hs

from . import utils


_new_highscore_hooks = []


def add_new_highscore_hook(func: Callable[[hs.HighscoreStruct], None]):
    _new_highscore_hooks.append(func)


def get_new_highscore_hooks() -> Iterable[Callable[[hs.HighscoreStruct], None]]:
    return iter(_new_highscore_hooks)
