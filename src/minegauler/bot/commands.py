"""
Handle bot messages.
"""

__all__ = ("RoomType",)

import enum
import logging

from minegauler.app.shared.types import GameMode

from . import formatter, utils
from .msgparse import BotMsgParser, CommandMapping, InvalidArgsError, helpstring, schema


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Message handling
# ------------------------------------------------------------------------------


class RoomType(enum.Enum):
    GROUP = "group"
    DIRECT = "direct"
    LOCAL = "local"

    def to_cmds(self) -> CommandMapping:
        if self is RoomType.GROUP:
            return _GROUP_COMMANDS
        elif self is RoomType.DIRECT:
            return _DIRECT_COMMANDS
        elif self is RoomType.LOCAL:
            return _LOCAL_COMMANDS
        else:
            assert False


GENERAL_INFO = """\
Welcome to the Minegauler bot!

Instructions for downloading Minegauler can be found in the \
[GitHub repo](https://github.com/LewisGaul/minegauler/blob/main/README.md).

The bot provides the ability to check highscores and matchups for games of \
Minegauler, and also gives notifications whenever anyone in the group sets a \
new highscore.

There are a few settings to filter Minegauler games with:
 - mode: One of 'regular' or 'split-cell' (defaults to 'regular').
 - difficulty: One of 'beginner', 'intermediate', 'expert' or 'master'.  
   By default the combination of beginner, intermediate and expert is used, \
with a score of 1000 used for any difficulties not completed.
 - drag-select: One of 'on' or 'off'.  
   By default no filter is applied (the best time of either mode is used).
 - per-cell: One of 1, 2 or 3.  
   By default no filter is applied (the best time of any mode is used).
 - reach: One of 4, 8 or 24.  
   By default reach=8 is used (the normal mode).

All highscores are independent of each of the above modes, and all commands \
accept these filters to view specific times. E.g. 'ranks beginner per-cell 1'.

Commands can be issued in group chat and direct chat. Most of the commands are \
the same, however some are only available in one of the other (e.g. \
'set nickname'). Type 'help' or '?' to check the available commands.

To interact with a bot in Webex Teams group chats, the bot must be tagged. To \
do this, type @ followed by the bot's name. The client should auto-suggest a \
completion, at which point you'll need to press enter or tab to select the \
completion and turn it into a tag.

Some useful common commands:  
'ranks' - display rankings  
'matchups <name> <name> ...' - display comparison of times between users

Some useful group-chat commands:  
'challenge <name> ...' - challenge other users to a game

Some useful direct-chat commands:  
'set nickname' - set your nickname that you use in the Minegauler app
"""


LOCAL_INFO = """\
Welcome to the Minegauler bot!

Instructions for downloading Minegauler can be found in the \
[GitHub repo](https://github.com/LewisGaul/minegauler/blob/main/README.md).

The local bot provides the ability to check highscores and matchups for games \
of Minegauler.

There are a few settings to filter Minegauler games with:
 - mode: One of 'regular' or 'split-cell' (defaults to 'regular').
 - difficulty: One of 'beginner', 'intermediate', 'expert' or 'master'.  
   By default the combination of beginner, intermediate and expert is used, \
with a score of 1000 used for any difficulties not completed.
 - drag-select: One of 'on' or 'off'.  
   By default no filter is applied (the best time of either mode is used).
 - per-cell: One of 1, 2 or 3.  
   By default no filter is applied (the best time of any mode is used).

All highscores are independent of each of the above modes, and all commands \
accept these filters to view specific times. E.g. 'ranks beginner per-cell 1'.

Some useful common commands:  
'ranks' - display rankings  
'player <name>' - display player info  
'matchups <name> <name> ...' - display comparison of times between users
"""


@helpstring("Get information about the game")
@schema("info")
def info(args, **kwargs):
    # Check no args given.
    BotMsgParser().parse_args(args)
    if kwargs["room_type"] is RoomType.LOCAL:
        return LOCAL_INFO
    else:
        return GENERAL_INFO


@helpstring("Get player info")
@schema(
    "player <name> "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}] "
    "[reach {4 | 8 | 24}]"
)
def player(args, username: str, markdown: bool = False, **kwargs):
    parser = BotMsgParser()
    username_choices = list(utils.USER_NAMES)
    if username:
        username_choices.append("me")
    parser.add_positional_arg("username", choices=username_choices)
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_reach_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    if args.username == "me":
        args.username = username

    highscores = utils.get_highscores(
        name=utils.USER_NAMES[args.username],
        game_mode=args.game_mode,
        difficulty=args.difficulty,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
        reach=args.reach,
    )

    filters_str = formatter.format_filters(
        game_mode=None,
        difficulty=None,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
        reach=args.reach,
        no_difficulty=True,
    )
    if filters_str:
        filters_str = " with " + filters_str
    if utils.USER_NAMES[args.username] == args.username:
        username_str = ""
    else:
        username_str = f" ({utils.USER_NAMES[args.username]})"
    lines = [
        "Player info for {name}{username} on {mode} mode{filters}:".format(
            name=args.username,
            username=username_str,
            mode=args.game_mode.value,
            filters=filters_str,
        )
    ]
    lines.extend(
        formatter.format_player_highscores(list(highscores), difficulty=args.difficulty)
    )

    linebreak = "  \n" if markdown else "\n"

    return linebreak.join(lines)


@helpstring("Get rankings")
@schema(
    "ranks "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}] "
    "[reach {4 | 8 | 24}]"
)
def ranks(args, **kwargs) -> str:
    markdown = kwargs.get("markdown", False)

    parser = BotMsgParser()
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_reach_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)

    times = utils.get_highscore_times(
        game_mode=args.game_mode,
        difficulty=args.difficulty,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
        reach=args.reach,
    )

    lines = [
        "Rankings for {}".format(
            formatter.format_filters(
                game_mode=args.game_mode,
                difficulty=args.difficulty,
                drag_select=args.drag_select,
                per_cell=args.per_cell,
                reach=args.reach,
            )
        )
    ]
    ranks = formatter.format_highscore_times(times)
    if markdown:
        ranks = f"```\n{ranks}\n```"
    lines.append(ranks)

    return "\n".join(lines)


@helpstring("Get stats for played games")
@schema(  # @@@ This is bad because it requires knowledge of sub-commands.
    "stats [players ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}] "
    "[reach {4 | 8 | 24}]"
)
def stats(args, **kwargs):
    parser = BotMsgParser()
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_reach_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    return "Stats"


@helpstring("Get player stats")
@schema("stats players {all | <name> [<name> ...]}")
def stats_players(args, username: str, markdown=False, **kwargs):
    parser = BotMsgParser()
    username_choices = list(utils.USER_NAMES) + ["all"]
    if username:
        username_choices.append("me")
    parser.add_positional_arg("username", nargs="+", choices=username_choices)
    args = parser.parse_args(args)
    if "all" in args.username:
        if len(args.username) > 1:
            raise InvalidArgsError("'all' should be specified without usernames")
        users = utils.USER_NAMES.keys()
    else:
        users = {u if u != "me" else username for u in args.username}

    player_info = [utils.get_player_info(u) for u in users]
    lines = [formatter.format_player_info(player_info)]
    if markdown:
        lines = ["```", *lines, "```"]

    return "\n".join(lines)


@helpstring("Get matchups for given players")
@schema(
    "matchups <name> <name> [<name> ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}] "
    "[reach {4 | 8 | 24}]"
)
def matchups(
    args,
    username: str,
    markdown: bool = False,
    room_type=RoomType.DIRECT,
    **kwargs,
):
    parser = BotMsgParser()
    username_choices = list(utils.USER_NAMES)
    if username:
        username_choices.append("me")
    parser.add_positional_arg("username", nargs="+", choices=username_choices)
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_reach_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    users = {u if u != "me" else username for u in args.username}
    if len(users) < 2 or len(users) > 5:
        raise InvalidArgsError("Require between 2 and 5 username args")
    names = {utils.USER_NAMES[u] for u in users}

    times = utils.get_highscore_times(
        game_mode=args.game_mode,
        difficulty=args.difficulty,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
        reach=args.reach,
        users=names,
    )
    matchups = utils.get_matchups(times)

    if markdown and room_type is RoomType.GROUP:
        users_str = ", ".join(utils.tag_user(u) for u in users)
    else:
        users_str = ", ".join(users)
    lines = [
        "Matchups between {users} for {filters}:".format(
            users=users_str,
            filters=formatter.format_filters(
                game_mode=args.game_mode,
                difficulty=args.difficulty,
                drag_select=args.drag_select,
                per_cell=args.per_cell,
                reach=args.reach,
            ),
        )
    ]
    lines.extend(formatter.format_matchups(matchups))
    linebreak = "  \n" if markdown else "\n"

    return linebreak.join(lines)


@helpstring("Get best matchups including at least one of specified players")
@schema(
    "best-matchups [<name> ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}] "
    "[reach {4 | 8 | 24}]"
)
def best_matchups(
    args, username: str, markdown=False, room_type=RoomType.DIRECT, **kwargs
):
    parser = BotMsgParser()
    username_choices = list(utils.USER_NAMES)
    if username:
        username_choices.append("me")
    parser.add_positional_arg("username", nargs="*", choices=username_choices)
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_reach_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    users = {u if u != "me" else username for u in args.username}
    names = {utils.USER_NAMES[u] for u in users}

    times = utils.get_highscore_times(
        game_mode=args.game_mode,
        difficulty=args.difficulty,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
        reach=args.reach,
        users=utils.USER_NAMES.values(),
    )
    matchups = utils.get_matchups(times, include_users=names)[:10]

    if markdown and room_type is RoomType.GROUP:
        users_str = ", ".join(utils.tag_user(u) for u in users)
    else:
        users_str = ", ".join(users)
    if users_str:
        users_str = " including " + users_str
    lines = [
        "Best matchups{users} for {filters}:".format(
            users=users_str,
            filters=formatter.format_filters(
                game_mode=args.game_mode,
                difficulty=args.difficulty,
                drag_select=args.drag_select,
                per_cell=args.per_cell,
                reach=args.reach,
            ),
        )
    ]
    lines.extend(formatter.format_matchups(matchups))
    linebreak = "  \n" if markdown else "\n"

    return linebreak.join(lines)


@helpstring("Challenge other players to a game")
@schema(
    "challenge <name> [<name> ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}] "
    "[reach {4 | 8 | 24}]"
)
def challenge(args, username: str, **kwargs):
    parser = BotMsgParser()
    parser.add_positional_arg(
        "username",
        nargs="+",
        choices=set(utils.USER_NAMES) - {username},
    )
    parser.add_positional_arg("game_mode", nargs="?", type=GameMode.from_str)
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_reach_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    names = {u for u in args.username}

    users_str = ", ".join(utils.tag_user(u) for u in names)
    mode_str = args.game_mode.value + " " if args.game_mode else ""
    mode_str += args.difficulty.name.lower() + " " if args.difficulty else ""
    filters_str = formatter.format_filters(
        game_mode=None,
        difficulty=None,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
        reach=args.reach,
        no_difficulty=True,
    )
    if filters_str:
        filters_str = " with " + filters_str

    return "{user} has challenged {opponents} to a {mode}game of Minegauler{filters}".format(
        user=username, opponents=users_str, mode=mode_str, filters=filters_str
    )


@helpstring("Set your nickname")
@schema("set nickname <name>")
def set_nickname(args, username: str, **kwargs):
    new = " ".join(args)
    if len(new) > 10:
        raise InvalidArgsError("Nickname must be no longer than 10 characters")
    for other in utils.USER_NAMES.values():
        if new.lower() == other.lower():
            raise InvalidArgsError(f"Nickname {other!r} already in use")
    if new.lower() in utils.USER_NAMES.keys() and new != username:
        raise InvalidArgsError(f"Cannot set nickname to someone else's username!")
    old = utils.USER_NAMES[username]
    logger.debug("Changing nickname of %s from %r to %r", username, old, new)
    utils.set_user_nickname(username, new)
    return f"Nickname changed from {old!r} to {new!r}"


@helpstring("Add a user to the local rankings")
@schema("user add <name>")
def add_user(args, **kwargs):
    parser = BotMsgParser()
    parser.add_positional_arg("name")
    args = parser.parse_args(args)
    for user in utils.USER_NAMES:
        if args.name.lower() == user.lower():
            raise InvalidMsgError(f"User {user!r} already added")
    logger.debug("Adding user %r", args.name)
    utils.set_user_nickname(args.name, args.name)
    return f"Added user {args.name!r}"


@helpstring("Remove a user from the local rankings")
@schema("user remove <name>")
def remove_user(args, **kwargs):
    parser = BotMsgParser()
    parser.add_positional_arg("name")
    args = parser.parse_args(args)
    try:
        utils.USER_NAMES.pop(args.name)
    except KeyError as e:
        raise InvalidMsgError(f"User {args.name!r} not found") from e
    else:
        utils.save_users_file()
    logger.debug("Removed user %r", args.name)
    return f"Removed user {args.name!r}"


@helpstring("List users on the local rankings")
@schema("user list")
def list_users(args, **kwargs):
    parser = BotMsgParser()
    parser.parse_args(args)
    msg = "The following users are on the local rankings:"
    for user in sorted(utils.USER_NAMES, key=lambda x: x.lower()):
        msg += "\n - " + user
    return msg


_COMMON_COMMANDS = {
    "player": player,
    "ranks": ranks,
    "stats": {
        # None: stats,
        "players": stats_players,
    },
    "matchups": matchups,
    "best-matchups": best_matchups,
}

_GROUP_COMMANDS = {
    **_COMMON_COMMANDS,
    "challenge": challenge,
}

_DIRECT_COMMANDS = {
    **_COMMON_COMMANDS,
    "info": info,
    "set": {
        "nickname": set_nickname,
    },
}

_LOCAL_COMMANDS = {
    **_COMMON_COMMANDS,
    "info": info,
    "user": {
        "add": add_user,
        "remove": remove_user,
        "list": list_users,
    },
}
