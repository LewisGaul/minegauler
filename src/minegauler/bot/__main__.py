from __future__ import annotations

import sys

from . import msgparse, utils


def main(argv: list[str]) -> int:
    rc = 0
    utils.read_users_file()
    try:
        resp = msgparse.parse_msg(argv, msgparse.RoomType.LOCAL, username="")
    except (msgparse.InvalidArgsError, msgparse.InvalidMsgError) as exc:
        resp = str(exc)
        rc = 1
    print(resp)
    return rc


sys.exit(main(sys.argv[1:]))
