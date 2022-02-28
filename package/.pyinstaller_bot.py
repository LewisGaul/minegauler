# February 2022, Lewis Gaul

"""
Bot entry script.

This file is provided for use with pyinstaller.

"""

import shlex
import sys

import minegauler.bot


if len(sys.argv) >= 2:
    sys.exit(minegauler.bot.msgparse.main(sys.argv[1:]))
else:
    while True:
        try:
            minegauler.bot.msgparse.main(shlex.split(input("bot> ")))
        except (EOFError, KeyboardInterrupt):
            print()
            break
