# January 2020, Lewis Gaul

"""
Entry script to the app.

The app can be run with 'python -m minegauler' or just by running this script.

This file is provided for use with pyinstaller.

"""

import runpy


runpy.run_module("minegauler.app", run_name="__main__")
