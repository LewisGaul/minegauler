# January 2020, Lewis Gaul

"""
Entry script to the app.

The app can be run with 'python -m minegauler' or just by running this script.

This file is provided for use with pyinstaller.

"""

import sys


if len(sys.argv) >= 1 and sys.argv[1] == "bot":
    import shlex

    import minegauler.bot

    if len(sys.argv) > 2:
        sys.exit(minegauler.bot.msgparse.main(sys.argv[2:]))
    else:
        while True:
            try:
                minegauler.bot.msgparse.main(shlex.split(input("bot> ")))
            except (EOFError, KeyboardInterrupt):
                print()
                break
else:
    import minegauler.app.__main__
