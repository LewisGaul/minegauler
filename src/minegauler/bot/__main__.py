from __future__ import annotations

import sys

from . import handle_msg, msgparse, utils
from .commands import RoomType


def main(argv: list[str]) -> int:
    rc = 0
    utils.read_users_file()
    try:
        resp = handle_msg(argv, RoomType.LOCAL, markdown=False, username="")
    except (msgparse.InvalidArgsError, msgparse.InvalidMsgError) as exc:
        resp = str(exc)
        rc = 1
    print(resp)
    return rc


sys.exit(main(sys.argv[1:]))
