"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys
from os.path import join
import json
from functools import partial
import logging
logging.basicConfig(level=logging.DEBUG)

from minegauler import core
from .utils import root_dir, GameCellMode
from .types import GameOptionsStruct, GUIOptionsStruct, PersistSettingsStruct
from .core import cb_core, Controller
from .gui import app, MinegaulerGUI


logging.info("Running...")


settings = {}
try:
    logging.info("Reading settings from file")
    with open(join(root_dir, 'settings.cfg'), 'r') as f:
        settings = json.load(f)
except FileNotFoundError:
    logging.info("Unable to read settings from file, will use defaults")
except json.JSONDecodeError:
    logging.info("Unable to decode settings from file, will use defaults")

game_opts = GameOptionsStruct(
       **{k: v for k, v in settings.items() if k in GameOptionsStruct.elements})
gui_opts  = GUIOptionsStruct(
       **{k: v for k, v in settings.items() if k in GUIOptionsStruct.elements})

# Create controller.                           
ctrlr = Controller(game_opts)

# Set up GUI.
main_window = MinegaulerGUI(ctrlr.board, gui_opts)
main_window.show()
cb_core.new_game.emit()


def save_settings():
    """Get the settings in use across the app and save to a file."""
    settings = PersistSettingsStruct()
    for k, v in ctrlr.opts.items():
        if k in settings.elements:
            settings[k] = v
    for k, v in main_window.opts.items():
        if k in settings.elements:
            settings[k] = v
    core.save_settings(settings)
                    
cb_core.save_settings.connect(save_settings)
                
                    
# Start the app.
sys.exit(app.exec_())
