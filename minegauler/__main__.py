"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys

from .core.game_logic import Controller
from .gui import app, MainWindow, MinefieldWidget


print("Running...")
x, y = 8, 4
main_window = MainWindow('MineGauler')
ctrlr = Controller(x, y)
mf_widget = MinefieldWidget(main_window, x, y, btn_size=56)
mf_widget.register_all_cbs(ctrlr)
ctrlr.set_cell_fn = mf_widget.set_cell_image
ctrlr.split_cell_fn = mf_widget.split_cell
main_window.set_body_widget(mf_widget)
main_window.show()
sys.exit(app.exec_())
