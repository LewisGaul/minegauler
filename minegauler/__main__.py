"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys
from types import SimpleNamespace
import logging
logging.basicConfig(level=logging.DEBUG)

from .core import cb_core, Controller
from .gui import app, MinegaulerGUI
from .utils import GameCellMode


logging.info("Running...")

opts = SimpleNamespace(x_size=8,
                       y_size=4,
                       mines=7,
                       first_success=True,
                       per_cell=1,
                       game_mode=GameCellMode.NORMAL)
ctrlr = Controller(opts)
# Set up GUI.
main_window = MinegaulerGUI(ctrlr.board, btn_size=36)
# Start the app.
main_window.show()
cb_core.new_game.emit()
sys.exit(app.exec_())
