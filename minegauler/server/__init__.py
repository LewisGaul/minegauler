__all__ = ("add_new_highscore_hook", "get_new_highscore_hooks")

from typing import Callable, Iterable

from ..app import highscores as hs


_new_highscore_hooks = []


def add_new_highscore_hook(func: Callable[[hs.HighscoreStruct], None]):
    _new_highscore_hooks.append(func)


def get_new_highscore_hooks() -> Iterable[Callable[[hs.HighscoreStruct], None]]:
    return iter(_new_highscore_hooks)
