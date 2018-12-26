"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""


import sys

from minegauler.backend import Controller, GameOptsStruct
from minegauler.frontend import run


ctrlr = Controller(GameOptsStruct())

sys.exit(run(ctrlr))