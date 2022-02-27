# February 2020, Lewis Gaul

"""
Parse bot messages.

"""

__all__ = ("GENERAL_INFO", "RoomType", "parse_msg")

import argparse
import enum
import logging
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from minegauler.app.shared.types import Difficulty, GameMode

from . import formatter, utils


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Message parsing
# ------------------------------------------------------------------------------


class InvalidArgsError(Exception):
    pass


class InvalidMsgError(Exception):
    pass


class PositionalArg:
    def __init__(
        self,
        name: str,
        *,
        parse_name: bool = False,
        nargs: Union[int, str] = 1,
        default: Any = None,
        choices: Optional[Iterable[Any]] = None,
        type: Optional[Callable] = None,
        validate: Optional[Callable] = None,
    ):
        if (isinstance(nargs, int) and nargs < 1) and nargs not in ["?", "*", "+"]:
            raise ValueError(f"Bad nargs value {nargs!r}")
        self.name = name
        self.parse_name = parse_name
        self.nargs = nargs
        if default is None and nargs not in [1, "?"]:
            self.default = []
        else:
            self.default = default
        self._choices = choices
        self._type = type
        self._validate = validate

    def convert(self, value):
        if self._type is not None:
            return self._type(value)
        return value

    def validate(self, value):
        if self._choices is not None and value not in self._choices:
            return False
        if self._validate:
            return self._validate(value)
        return True


class ArgParser(argparse.ArgumentParser):
    """
    A specialised arg parser.

    The list of args to be parsed can contain the following, with no overlap:
     - Ordered positional args at the start
     - Regular argparse args with no order

    Positional args are added with 'add_positional_arg()'. The order of calls to
    this method determines the order the args must appear in. The following
    options are accepted:
     - parse_name: Whether the arg name should be parsed.
     - nargs: The number of args to accept. Accepted values are positive
        integers, "?" for 0 or 1, "*" for 0 or more, "+" for 1 or more.
     - choices: As for 'add_argument()'.
     - type: As for 'add_argument()'.

    Positional args are greedily consumed, but if an arg does not satisfy
    choices or if the 'type' callable raises an exception then no more values
    will be accepted for that arg.

    Examples:
     - If a positional arg has no type/choices restrictions and unbounded
        'nargs' (i.e. set to "*" or "+") then all positional options will be
        consumed by this arg.
     - If a positional arg has unbounded 'nargs' but has a 'type' that raises an
        exception for invalid args, subsequent args will take over the matching.
        Note that if insufficient options are matched (e.g. nargs="+" and no
        options are matched) then parsing ends with a standard error.

    Positional argument parsing ends as soon as an option starting with a dash
    is encountered, or when the positional args are exhausted. The remaining
    options are passed to a standard argparse parser to match args added with
    'add_argument()'.
    """

    def __init__(self):
        super().__init__(add_help=False)
        self._name_parse_args = []
        self._positional_args = []

    def parse_known_args(self, args: Iterable[str], namespace=None):
        """
        Override the default behaviour.
        """
        if namespace is None:
            namespace = argparse.Namespace()

        # Start with positional args.
        args = self._parse_positional_args(args, namespace)
        logger.debug("Remaining after parsing positional args: %s", args)

        # Replace optional args so that they don't require the dashes.
        for i, arg in enumerate(args):
            if arg in self._name_parse_args:
                args[i] = f"--{arg}"

        # Regular parsing of remaining args
        return super().parse_known_args(args, namespace)

    def add_argument(self, name, *args, **kwargs):
        """
        Override the default behaviour.
        """
        if not name.startswith("--"):
            self._name_parse_args.append(name)
            name = "--" + name.lstrip("-")
        super().add_argument(name, *args, **kwargs)

    def error(self, message):
        raise InvalidArgsError(message)

    def add_positional_arg(self, name: str, **kwargs) -> None:
        """
        Add a positional argument for parsing.

        :param name:
            The name of the argument - must be unique.
        :param kwargs:
            Arguments to pass to the 'PositionalArg' class.
        """
        self._positional_args.append(PositionalArg(name, **kwargs))

    def _parse_positional_args(self, kws: Iterable[str], namespace) -> Iterable[str]:
        """
        Parse the positional args.

        :param kws:
            The provided keywords.
        :param namespace:
            The namespace to set argument values in.
        :return:
            The remaining unmatched keywords.
        """
        for arg in self._positional_args:
            logger.debug(f"Parsing positional arg %r, kws: %s", arg.name, kws)
            result, kws = self._parse_single_positional_arg(arg, kws)
            setattr(namespace, arg.name, result)
        return kws

    def _parse_single_positional_arg(
        self, arg: PositionalArg, kws: Iterable[str]
    ) -> Tuple[Any, Iterable[str]]:
        """
        Parse a single positional arg. Raise InvalidArgsError if not enough
        matching args are found.
        """
        required = arg.nargs not in ["?", "*"]
        if isinstance(arg.nargs, int):
            max_matches = arg.nargs
            exp_args_string = str(arg.nargs)
        elif arg.nargs == "?":
            max_matches = 1
            exp_args_string = "optionally one"
        elif arg.nargs == "*":
            max_matches = None
            exp_args_string = "any number of"
        elif arg.nargs == "+":
            max_matches = None
            exp_args_string = "at least one"
        else:
            assert False

        # First parse the arg name if required.
        if kws and arg.parse_name:
            if kws[0] == arg.name:  # Found arg
                kws.pop(0)
            elif not required:  # No match
                return arg.default, kws
            else:
                raise InvalidArgsError(f"Expected to find {arg.name!r}")

        # Now parse argument values.
        matches = []
        while kws and (max_matches is None or len(matches) < max_matches):
            try:
                kw_value = arg.convert(kws[0])
                assert arg.validate(kw_value)
            except Exception as e:
                logger.debug(e)
                if arg.parse_name and not matches:
                    # We parsed the name of the arg, so we expected to find
                    # at least one value...
                    raise InvalidArgsError(
                        f"Got name of positional arg {arg.name!r} but no values"
                    ) from e
                else:
                    break
            else:
                matches.append(kw_value)
                kws.pop(0)

        if required and not matches:
            raise InvalidArgsError(f"Expected {exp_args_string} {arg.name!r} arg")
        elif isinstance(arg.nargs, int) and len(matches) != arg.nargs:
            assert len(matches) < arg.nargs
            raise InvalidArgsError(f"Expected {exp_args_string} {arg.name!r} arg")

        arg_value = arg.default
        if matches:
            if arg.nargs in [1, "?"]:
                assert len(matches) == 1
                arg_value = matches[0]
            else:
                arg_value = matches

        return arg_value, kws


class BotMsgParser(ArgParser):
    def add_game_mode_arg(self):
        self.add_positional_arg(
            "game_mode", nargs="?", type=GameMode.from_str, default=GameMode.REGULAR
        )

    def add_difficulty_arg(self):
        self.add_positional_arg("difficulty", nargs="?", type=Difficulty.from_str)

    def add_per_cell_arg(self):
        self.add_argument("per-cell", type=int, choices=[1, 2, 3])

    def add_drag_select_arg(self):
        def _arg_type(arg):
            if arg == "on":
                return True
            elif arg == "off":
                return False
            else:
                raise InvalidArgsError("Drag select should be one of {'on', 'off'}")

        self.add_argument("drag-select", type=_arg_type)


# ------------------------------------------------------------------------------
# Message handling
# ------------------------------------------------------------------------------


CommandMapping = Dict[Optional[str], Union[Callable, "CommandMapping"]]


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


def helpstring(text):
    def decorator(func):
        func.__helpstring__ = text
        return func

    return decorator


def schema(text):
    def decorator(func):
        func.__schema__ = text
        return func

    return decorator


def cmd_help(
    func: Callable, *, only_schema: bool = False, allow_markdown: bool = False
) -> str:
    lines = []
    if not only_schema:
        try:
            lines.append(func.__helpstring__)
        except AttributeError:
            logger.warning(
                "No helpstring found on message handling function %r", func.__name__
            )
    try:
        schema = func.__schema__
    except AttributeError:
        logger.warning("No schema found on message handling function %r", func.__name__)
    else:
        if allow_markdown:
            lines.append(f"`{schema}`")
        else:
            lines.append(schema)

    if not lines:
        return "Unexpected error: unable to get help message\n\n"

    return "\n\n".join(lines)


@helpstring("Get help for a command")
@schema("help [<command>]")
def help_(args, **kwargs):
    allow_markdown = kwargs.get("allow_markdown", False)
    room_type = kwargs.get("room_type", RoomType.DIRECT)
    cmds = room_type.to_cmds()

    linebreak = "\n\n" if allow_markdown else "\n"
    commands = _flatten_cmds(cmds)
    if allow_markdown:
        commands = f"`{commands}`"

    if not args:
        return commands

    func, _ = _map_to_cmd(args, cmds)
    if func is None:
        raise InvalidArgsError(linebreak.join(["Unrecognised command", commands]))
    return cmd_help(func, allow_markdown=allow_markdown)


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
    "[per-cell {1 | 2 | 3}]"
)
def player(args, username: str, allow_markdown=False, **kwargs):
    parser = BotMsgParser()
    username_choices = list(utils.USER_NAMES)
    if username:
        username_choices.append("me")
    parser.add_positional_arg("username", choices=username_choices)
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
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
    )

    filters_str = formatter.format_filters(
        game_mode=None,
        difficulty=None,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
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

    linebreak = "  \n" if allow_markdown else "\n"

    return linebreak.join(lines)


@helpstring("Get rankings")
@schema(
    "ranks "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}]"
)
def ranks(args, **kwargs) -> str:
    allow_markdown = kwargs.get("allow_markdown", False)

    parser = BotMsgParser()
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)

    times = utils.get_highscore_times(
        game_mode=args.game_mode,
        difficulty=args.difficulty,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
    )

    lines = [
        "Rankings for {}".format(
            formatter.format_filters(
                game_mode=args.game_mode,
                difficulty=args.difficulty,
                drag_select=args.drag_select,
                per_cell=args.per_cell,
            )
        )
    ]
    ranks = formatter.format_highscore_times(times)
    if allow_markdown:
        ranks = f"```\n{ranks}\n```"
    lines.append(ranks)

    return "\n".join(lines)


@helpstring("Get stats for played games")
@schema(  # @@@ This is bad because it requires knowledge of sub-commands.
    "stats [players ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}]"
)
def stats(args, **kwargs):
    parser = BotMsgParser()
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    return "Stats"


@helpstring("Get player stats")
@schema("stats players {all | <name> [<name> ...]}")
def stats_players(args, username: str, allow_markdown=False, **kwargs):
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
    if allow_markdown:
        lines = ["```", *lines, "```"]

    return "\n".join(lines)


@helpstring("Get matchups for given players")
@schema(
    "matchups <name> <name> [<name> ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}]"
)
def matchups(
    args,
    username: str,
    allow_markdown: bool = False,
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
        users=names,
    )
    matchups = utils.get_matchups(times)

    if allow_markdown and room_type is RoomType.GROUP:
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
            ),
        )
    ]
    lines.extend(formatter.format_matchups(matchups))
    linebreak = "  \n" if allow_markdown else "\n"

    return linebreak.join(lines)


@helpstring("Get best matchups including at least one of specified players")
@schema(
    "best-matchups [<name> ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}]"
)
def best_matchups(
    args, username: str, allow_markdown=False, room_type=RoomType.DIRECT, **kwargs
):
    parser = BotMsgParser()
    username_choices = list(utils.USER_NAMES)
    if username:
        username_choices.append("me")
    parser.add_positional_arg("username", nargs="*", choices=username_choices)
    parser.add_game_mode_arg()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    users = {u if u != "me" else username for u in args.username}
    names = {utils.USER_NAMES[u] for u in users}

    times = utils.get_highscore_times(
        game_mode=args.game_mode,
        difficulty=args.difficulty,
        drag_select=args.drag_select,
        per_cell=args.per_cell,
        users=utils.USER_NAMES.values(),
    )
    matchups = utils.get_matchups(times, include_users=names)[:10]

    if allow_markdown and room_type is RoomType.GROUP:
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
            ),
        )
    ]
    lines.extend(formatter.format_matchups(matchups))
    linebreak = "  \n" if allow_markdown else "\n"

    return linebreak.join(lines)


@helpstring("Challenge other players to a game")
@schema(
    "challenge <name> [<name> ...] "
    "[regular | split-cell] "
    "[b[eginner] | i[ntermediate] | e[xpert] | m[aster] | l[udicrous]] "
    "[drag-select {on | off}] "
    "[per-cell {1 | 2 | 3}]"
)
def challenge(args, username: str, **kwargs):
    parser = BotMsgParser()
    parser.add_positional_arg(
        "username",
        nargs="+",
        choices=set(utils.USER_NAMES) - {username} - utils.NO_TAG_USERS,
    )
    parser.add_positional_arg("game_mode", nargs="?", type=GameMode.from_str)
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
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
    "help": help_,
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


def _map_to_cmd(msg: Iterable[str], cmds: CommandMapping) -> Tuple[Callable, List[str]]:
    func = None
    words = list(msg)

    while words:
        next_word = words[0]
        if next_word in cmds:
            words.pop(0)
            if callable(cmds[next_word]):
                func = cmds[next_word]
                break
            else:
                cmds = cmds[next_word]
        else:
            break
        if None in cmds:
            func = cmds[None]

    return func, words


def _flatten_cmds(cmds: CommandMapping, root: bool = True) -> str:
    to_join = []
    for k, v in cmds.items():
        item = k
        if isinstance(v, dict):
            item += " " + _flatten_cmds(v, root=False)
        if item:
            to_join.append(item)
    ret = " | ".join(to_join)
    if None in cmds:
        ret = f"[{ret}]"
    elif len(cmds) > 1 and not root:
        ret = f"{{{ret}}}"
    return ret


def parse_msg(
    msg: Union[str, List[str]],
    room_type: RoomType,
    *,
    allow_markdown: bool = False,
    **kwargs,
) -> str:
    """
    Parse a message and perform the corresponding action.

    :param msg:
        The message to parse.
    :param room_type:
        The room type the message was received in.
    :param allow_markdown:
        Whether to allow markdown in the response.
    :param kwargs:
        Other arguments to pass on to sub-command functions.
    :return:
        Response text.
    :raise InvalidArgsError:
        Unrecognised command. The text of the error is a suitable error/help
        message.
    """
    orig_msg = msg
    if isinstance(msg, str):
        msg = msg.strip().split()
    else:
        msg = msg.copy()
    if not msg:
        msg = ["help"]
    if msg[-1] in ["?", "help"] and not msg[0] == "help":
        # Change "?" at the end to be treated as help, except for the case where
        # this is a double help intended for a subcommand, e.g.
        # 'help matchups ?'.
        msg.pop(-1)
        msg.insert(0, "help")

    cmds = room_type.to_cmds()
    func = None
    try:
        func, args = _map_to_cmd(msg, cmds)
        if func is None:
            raise InvalidArgsError("Base command not found")
        return func(args, allow_markdown=allow_markdown, room_type=room_type, **kwargs)
    except InvalidMsgError as e:
        logger.debug("Invalid message: %r", orig_msg)
        resp_msg = f"Invalid command: {str(e)}"
        raise InvalidMsgError(resp_msg) from e
    except InvalidArgsError as e:
        logger.debug("Invalid message: %r", orig_msg)
        if func is None:
            raise InvalidArgsError(
                "Unrecognised command - try 'help' or 'info' in direct chat"
            ) from e
        else:
            linebreak = "\n\n" if allow_markdown else "\n"
            resp_msg = cmd_help(func, only_schema=True, allow_markdown=allow_markdown)
            resp_msg = linebreak.join([f"Unrecognised command: {str(e)}", resp_msg])

        raise InvalidArgsError(resp_msg) from e


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    rc = 0
    utils.read_users_file()
    try:
        resp = parse_msg(argv, RoomType.LOCAL, username="")
    except (InvalidArgsError, InvalidMsgError) as e:
        resp = str(e)
        rc = 1
    print(resp)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
