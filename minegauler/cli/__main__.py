# August 2020, Lewis Gaul

"""
CLI entry-point.

"""

import logging
import pathlib
import subprocess
import sys
from typing import Any, Callable, Dict

# Any 3rd-party dependencies must be vendored for venv creation.
import yaml

from .parser import CLIParser


_THIS_DIR = pathlib.Path(__file__).absolute().parent

logger = logging.getLogger(__name__)


def run_app(args):
    # TODO: Use the venv python.
    subprocess.run(["python", "-m", "minegauler"])


def run_tests(args):
    # TODO: Use the venv python.
    # The double dash can be used to pass args through to pytest.
    try:
        args.remaining_args.remove("--")
    except ValueError:
        pass
    if args.pytest_help:
        subprocess.run(["python", "-m", "pytest", "-h"])
    else:
        subprocess.run(["python", "-m", "pytest"] + args.remaining_args)


def run_bot_cli(args):
    from .. import bot

    bot.utils.read_users_file()

    try:
        args.remaining_args.remove("--")
    except ValueError:
        pass
    return bot.msgparse.main(args.remaining_args)


def add_bot_player(args):
    from .. import bot

    bot.utils.read_users_file()
    bot.utils.set_user_nickname(args.player_name, args.player_name)


def remove_bot_player(args):
    from .. import bot

    bot.utils.read_users_file()
    bot.utils.USER_NAMES.pop(args.player_name)
    bot.utils.save_users_file()


_COMMANDS: Dict[str, Callable[[Any], int]] = {
    "run": run_app,
    "make-venv": lambda args: print("Not implemented"),
    "run-tests": run_tests,
    "bump-version": lambda args: print("Not implemented"),
    "bot": run_bot_cli,
    "bot-add-player": add_bot_player,
    "bot-remove-player": remove_bot_player,
}


def main(argv):
    # Load the CLI schema.
    with open(_THIS_DIR / "cli.yaml") as f:
        schema = yaml.safe_load(f)

    # Parse argv.
    prog = "run.bat" if sys.platform.startswith("win") else "run.sh"
    args = CLIParser(schema, prog=prog).parse_args(argv)
    logger.debug("Got args:", args)

    # Run the command!
    return _COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
