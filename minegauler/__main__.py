"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys
import logging
logging.basicConfig(level=logging.DEBUG)

from .core.callbacks import cb_core 
from .core.game_logic import Controller
from .gui import app, MinegaulerGUI
from .gui.utils import FaceState


logging.info("Running...")

x, y = 8, 4
ctrlr = Controller(x, y)
# Set up GUI.
main_window = MinegaulerGUI(ctrlr.board, btn_size=56)
# Start the app.
main_window.show()
cb_core.new_game.emit()
sys.exit(app.exec_())
