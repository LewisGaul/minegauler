"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""


import logging
import sys

from minegauler.backend import Controller, GameOptsStruct
from minegauler.frontend import run


logging.basicConfig(filename='runtime.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


ctrlr = Controller(GameOptsStruct())

sys.exit(run(ctrlr))