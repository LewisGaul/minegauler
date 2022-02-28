# January 2020, Lewis Gaul

"""
Entry script to the app.

The app can be run with 'python -m minegauler' or just by running this script.

This file is provided for use with pyinstaller.

"""

import sys

from minegauler.app.__main__ import main


sys.exit(main())
