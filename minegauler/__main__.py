"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys

from .core.game_logic import Processor
from .gui import app, MainWindow, MinefieldWidget


print("Running...")
main_window = MainWindow('MineGauler')
procr = Processor(8, 4)
mf_widget = MinefieldWidget(main_window, procr, btn_size=36)
main_window.set_body_widget(mf_widget)
main_window.show()
sys.exit(app.exec_())
