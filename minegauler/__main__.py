"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys
import logging
logging.basicConfig(level=logging.DEBUG)

from minegauler.callback_core import core as cb_core 
from .core.game_logic import Controller
from .gui import app, MainWindow, MinefieldWidget, PanelWidget
from .gui.utils import FaceState


logging.info("Running...")

x, y = 8, 4
ctrlr = Controller(x, y)
# Set up GUI.
main_window = MainWindow('MineGauler')
panel_widget = PanelWidget(main_window)
mf_widget = MinefieldWidget(main_window, ctrlr.board, btn_size=56)
main_window.set_panel_widget(panel_widget)
main_window.set_body_widget(mf_widget)
# Start the app.
main_window.show()
cb_core.new_game.emit()
sys.exit(app.exec_())
