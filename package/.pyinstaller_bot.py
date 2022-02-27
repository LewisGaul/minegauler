# February 2022, Lewis Gaul

"""
Entry script to the bot.

This file is provided for use with pyinstaller.

"""

import shlex

from minegauler.bot import msgparse


while True:
    try:
        msgparse.main(shlex.split(input("bot> ")))
    except (EOFError, KeyboardInterrupt):
        print()
        break
