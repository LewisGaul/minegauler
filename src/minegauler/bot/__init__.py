# February 2020, Lewis Gaul

"""
Bot package.

"""

__all__ = ("commands", "formatter", "handle_msg", "msgparse", "utils")

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from . import commands, formatter, msgparse, utils
from .commands import RoomType


def handle_msg(
    msg: Union[str, List[str]],
    room_type: RoomType,
    *,
    markdown: bool,
    username: str,
) -> str:
    return msgparse.CmdParser(room_type.to_cmds(), markdown=markdown).handle_msg(
        msg, username=username, room_type=room_type
    )
