"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys
from os.path import join
from types import SimpleNamespace
import json
from functools import partial
import logging
logging.basicConfig(level=logging.DEBUG)

from minegauler import core
from .utils import root_dir, GameCellMode
from .core import cb_core, Controller
from .gui import app, MinegaulerGUI


logging.info("Running...")

settings = None
try:
    logging.info("Reading settings from file")
    with open(join(root_dir, 'settings.cfg'), 'r') as f:
        settings = json.load(f)
except FileNotFoundError:
    logging.info("Unable to read settings from file, will use defaults")
except json.JSONDecodeError:
    logging.info("Unable to decode settings from file, will use defaults")
finally:
    if settings:
        opts = SimpleNamespace(**settings)
    else:
        opts = SimpleNamespace(x_size=8,
                               y_size=8,
                               mines=10,
                               first_success=True,
                               per_cell=1)
                               #game_mode=GameCellMode.NORMAL)  @@@

# Create controller.                           
ctrlr = Controller(opts)
cb_core.save_settings.connect(partial(core.save_settings, ctrlr.opts.__dict__))

# Set up GUI.
main_window = MinegaulerGUI(ctrlr.board, btn_size=36)
# Start the app.
main_window.show()
cb_core.new_game.emit()
sys.exit(app.exec_())
