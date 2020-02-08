"""
msgparse.py - Parse bot messages

February 2020, Lewis Gaul
"""

__all__ = ("parse_msg",)

import argparse
import logging
import sys
from typing import Any, Iterable, Tuple


logger = logging.getLogger(__name__)

users = ["legaul", "pasta"]


class InvalidArgsError(Exception):
    pass


class PositionalArg:
    def __init__(
        self,
        name,
        *,
        parse_name=False,
        nargs=1,
        default=None,
        choices=None,
        type=None,
        validate=None,
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
                    )
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
    def add_username_arg(self, *, nargs=1):
        self.add_positional_arg("username", nargs=nargs, choices=users)

    def add_difficulty_arg(self):
        self.add_positional_arg(
            "difficulty", nargs="?", type=self._convert_difficulty_arg
        )

    def add_rank_type_arg(self):
        def convert(arg):
            try:
                return self._convert_difficulty_arg(arg)
            except ValueError as e:
                if arg == "combined":
                    return "combined"
                elif arg == "official":
                    return "official"
                else:
                    raise ValueError(f"Invalid rank type {arg!r}")

        self.add_positional_arg("rank_type", nargs="?", type=convert)

    def add_per_cell_arg(self):
        self.add_argument("per-cell", type=int, choices=[1, 2, 3])

    def add_drag_select_arg(self):
        self.add_argument("drag-select", choices=["on", "off"])

    @staticmethod
    def _convert_difficulty_arg(arg):
        if arg in ["b", "beginner"]:
            return "beginner"
        elif arg in ["i", "intermediate"]:
            return "intermediate"
        elif arg in ["e", "expert"]:
            return "expert"
        elif arg in ["m", "master"]:
            return "master"
        else:
            raise ValueError(f"Invalid difficulty {arg!r}")


def helpstring(text):
    def decorator(func):
        func.__helpstring__ = text
        return func

    return decorator


def help_(args):
    try:
        print(_map_to_cmd(" ".join(args))[0].__helpstring__)
    except:
        print("Generic help")


@helpstring("Get information about the game")
def info(args):
    print("INFO")
    BotMsgParser().parse_args(args)


@helpstring("Get player info")
def player(args):
    print("PLAYER")

    parser = BotMsgParser()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    print(args)


@helpstring("Get rankings")
def ranks(args):
    print("RANKS")

    parser = BotMsgParser()
    parser.add_rank_type_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    print(args)

    # kwargs = {k: getattr(args, k) for k in ["difficulty", "per_cell", "drag_select"]}
    # highscores = hs.filter_and_sort(
    #     hs.get_highscores(hs.HighscoresDatabases.REMOTE, **kwargs)
    # )
    # msg = "```\n{}\n```".format(format.format_highscores(highscores))

    return "Ranks"


@helpstring("Get stats")
def stats(args):
    print("STATS")
    parser = BotMsgParser()
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    print(args)
    return "Stats"


@helpstring("Get player stats")
def stats_players(args):
    print("STATS PLAYERS")
    parser = BotMsgParser()
    parser.add_username_arg(nargs="+")
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    print(args)
    return "Player stats {}".format(", ".join(args.username))


@helpstring("Get matchups for given players")
def matchups(args):
    print("MATCHUPS")
    parser = BotMsgParser()
    parser.add_username_arg(nargs="+")
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    print(args)
    return "Matchups {}".format(", ".join(args.username))


@helpstring("Get the best matchups")
def best_matchups(args):
    print("BEST-MATCHUPS")
    parser = BotMsgParser()
    parser.add_username_arg(nargs="*")
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    print(args)
    return "Best matchups {}".format(", ".join(args.username))


@helpstring("Challenge other players to a game")
def challenge(args):
    print("CHALLENGE")
    parser = BotMsgParser()
    parser.add_username_arg(nargs="+")
    parser.add_difficulty_arg()
    parser.add_per_cell_arg()
    parser.add_drag_select_arg()
    args = parser.parse_args(args)
    print(args)
    return "Challenge {}".format(", ".join(args.username))


@helpstring("Set your nickname")
def set_nickname(args):
    print("SET NICKNAME")
    parser = BotMsgParser()
    parser.add_positional_arg("nickname", validate=lambda s: len(s) < 10)
    args = parser.parse_args(args)
    print(args)
    return f"Nickname set to {args.nickname}"


# fmt: off
COMMANDS = {
    "help": help_,
    "info": info,
    "player": player,
    "ranks": ranks,
    "stats": {
        None: stats,
        "players": stats_players
    },
    "matchups": matchups,
    "best-matchups": best_matchups,
    "challenge": challenge,
    "set": {
        "nickname": set_nickname,
    },
}
# fmt: on


def _map_to_cmd(msg):
    cmds = COMMANDS
    func = None
    words = msg.split()

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


def parse_msg(msg: str) -> str:
    msg = msg.strip()
    if msg.endswith("?"):
        msg = "help " + msg[:-1]

    try:
        func, args = _map_to_cmd(msg)
        assert func is not None
    except:
        return "Invalid command"
    else:
        return func(args)


def main():
    msg = input("msg: ")
    print(parse_msg(msg))
    print()


if __name__ == "__main__":

    def test():
        parser = ArgParser()
        parser.add_positional_arg("foo", nargs=1)
        parser.add_positional_arg(
            "bar", nargs="*", parse_name=True, choices={1, 2}, type=int
        )
        parser.add_positional_arg("baz", nargs=1, choices={"on", "off"})
        parser.add_argument("zip")
        parser.add_argument("zap", nargs="*", type=float)
        args, extra = parser.parse_known_args(sys.argv[1:])
        print(args)
        print(extra)

    while True:
        try:
            main()
        except (SystemExit, TypeError, InvalidArgsError) as e:
            print()
            print("Invalid command:", e)
            print()
