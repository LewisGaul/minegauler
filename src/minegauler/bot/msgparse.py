"""
Parse bot messages.

"""

__all__ = (
    "BotMsgParser",
    "CmdParser",
    "CommandMapping" "InvalidArgsError",
    "InvalidMsgError",
    "helpstring",
    "schema",
)

import argparse
import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from minegauler.app.shared.types import Difficulty, GameMode, ReachSetting


logger = logging.getLogger(__name__)


class InvalidArgsError(Exception):
    pass


class InvalidMsgError(Exception):
    pass


CommandMapping = Dict[Optional[str], Union[Callable, "CommandMapping"]]


def helpstring(text):
    """Decorator for a command function providing the help for the command."""

    def decorator(func):
        func.__helpstring__ = text
        return func

    return decorator


def schema(text):
    """Decorator for a command function providing the schema for the command."""

    def decorator(func):
        func.__schema__ = text
        return func

    return decorator


class CmdParser:
    """A parser to handle commands mapped to functions."""

    def __init__(self, cmds: CommandMapping, markdown: bool = False):
        """
        :param cmds:
            The dictionary of commands to support.
        :param markdown:
            Whether to enable markdown in the response.
        """
        self._cmds: CommandMapping = {**cmds, "help": self.help_}
        self._markdown: bool = markdown

    @helpstring("Get help for a command")
    @schema("help [<command>]")
    def help_(self, args, **kwargs):
        linebreak = "\n\n" if self._markdown else "\n"
        flat_cmds = self._flatten_cmds(self._cmds)
        if self._markdown:
            flat_cmds = f"`{flat_cmds}`"

        if not args:
            return flat_cmds

        func, _ = self._map_to_cmd(args)
        if func is None:
            raise InvalidArgsError(linebreak.join(["Unrecognised command", flat_cmds]))
        return self._get_cmd_help(func)

    def handle_msg(self, msg: Union[str, List[str]], **kwargs) -> str:
        """
        Parse a message and perform the corresponding action.

        :param msg:
            The message to handle.
        :param kwargs:
            Arguments to pass on to sub-command functions.
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

        func = None
        try:
            func, args = self._map_to_cmd(msg)
            if func is None:
                raise InvalidArgsError("Base command not found")
            return func(args, markdown=self._markdown, **kwargs)
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
                linebreak = "\n\n" if self._markdown else "\n"
                resp_msg = self._get_cmd_help(func, only_schema=True)
                resp_msg = linebreak.join([f"Unrecognised command: {str(e)}", resp_msg])

            raise InvalidArgsError(resp_msg) from e

    def _get_cmd_help(self, func: Callable, *, only_schema: bool = False) -> str:
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
            logger.warning(
                "No schema found on message handling function %r", func.__name__
            )
        else:
            if self._markdown:
                lines.append(f"`{schema}`")
            else:
                lines.append(schema)

        if not lines:
            return "Unexpected error: unable to get help message\n\n"

        return "\n\n".join(lines)

    def _map_to_cmd(self, msg: Iterable[str]) -> Tuple[Callable, List[str]]:
        cmds = self._cmds
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

    @classmethod
    def _flatten_cmds(cls, cmds: CommandMapping, root: bool = True) -> str:
        to_join = []
        for k, v in cmds.items():
            item = k
            if isinstance(v, dict):
                item += " " + cls._flatten_cmds(v, root=False)
            if item:
                to_join.append(item)
        ret = " | ".join(to_join)
        if None in cmds:
            ret = f"[{ret}]"
        elif len(cmds) > 1 and not root:
            ret = f"{{{ret}}}"
        return ret


class _PositionalArg:
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


class _ArgParser(argparse.ArgumentParser):
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
            Arguments to pass to the '_PositionalArg' class.
        """
        self._positional_args.append(_PositionalArg(name, **kwargs))

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
        self, arg: _PositionalArg, kws: Iterable[str]
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


class BotMsgParser(_ArgParser):
    """Subclass of argparse.ArgumentParser with support for bot message args."""

    def add_game_mode_arg(self):
        self.add_positional_arg(
            "game_mode", nargs="?", type=GameMode.from_str, default=GameMode.REGULAR
        )

    def add_difficulty_arg(self):
        self.add_positional_arg("difficulty", nargs="?", type=Difficulty.from_str)

    def add_per_cell_arg(self):
        self.add_argument("per-cell", type=int, choices=[1, 2, 3])

    def add_reach_arg(self):
        self.add_argument(
            "reach",
            type=ReachSetting,
            choices=[x.value for x in ReachSetting],
            default=ReachSetting.NORMAL,
        )

    def add_drag_select_arg(self):
        def _arg_type(arg):
            if arg == "on":
                return True
            elif arg == "off":
                return False
            else:
                raise InvalidArgsError("Drag select should be one of {'on', 'off'}")

        self.add_argument("drag-select", type=_arg_type)
