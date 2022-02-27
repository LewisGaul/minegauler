# August 2020, Lewis Gaul

"""
CLI entry-point.

"""

import logging
import pathlib
import runpy
import subprocess
import sys
from typing import Any, Callable, Dict

# Any 3rd-party dependencies must be vendored for venv creation.
import yaml  # noqa

from .parser import CLIParser


_THIS_DIR = pathlib.Path(__file__).absolute().parent

logger = logging.getLogger(__name__)


def run_app(args):
    runpy.run_module("minegauler.app", run_name="__main__")


def run_tests(args):
    # TODO: Use the venv python.
    # The double dash can be used to pass args through to pytest.
    try:
        args.remaining_args.remove("--")
    except ValueError:
        pass
    pytest_args = ["-h"] if args.pytest_help else args.remaining_args
    subprocess.run([sys.executable, "-m", "pytest"] + pytest_args)


def run_bot_cli(args):
    from minegauler import bot

    bot.utils.read_users_file()

    try:
        args.remaining_args.remove("--")
    except ValueError:
        pass
    return bot.msgparse.main(args.remaining_args)


_COMMANDS: Dict[str, Callable[[Any], int]] = {
    "run": run_app,
    "make-venv": lambda args: print("Not implemented"),
    "run-tests": run_tests,
    "bump-version": lambda args: print("Not implemented"),
    "bot": run_bot_cli,
}


def main(argv):
    # Load the CLI schema.
    with open(_THIS_DIR / "cli.yaml") as f:
        schema = yaml.safe_load(f)

    # Parse argv.
    prog = "run.bat" if sys.platform.startswith("win") else "run.sh"
    args = CLIParser(schema, prog=prog).parse_args(argv)
    logger.debug("Got args: %s", args)

    # Run the command!
    return _COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
