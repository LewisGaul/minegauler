# January 2020, Lewis Gaul

"""
Server utils.

"""

__all__ = ("is_highscore_new_best", "multiple_contexts")

import contextlib
from typing import Optional

from minegauler.shared import highscores as hs


def is_highscore_new_best(h: hs.HighscoreStruct) -> Optional[str]:
    all_highscores = hs.get_highscores(hs.HighscoresDatabases.REMOTE, settings=h)
    return hs.is_highscore_new_best(h, all_highscores)


# TODO: Move to super-shared location.
@contextlib.contextmanager
def multiple_contexts(*contexts):
    """
    Context manager to activate multiple context managers.

    :param contexts:
        The context managers to activate.
    """
    stack = contextlib.ExitStack()
    entered = []
    for ctx in contexts:
        entered.append(stack.enter_context(ctx))
    try:
        yield tuple(entered)
    finally:
        stack.close()
