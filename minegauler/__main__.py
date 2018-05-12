"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys

from .core.game_logic import Controller
from .gui import app, MainWindow, MinefieldWidget, PanelWidget


print("Running...")
x, y = 8, 4
ctrlr = Controller(x, y)
# Set up GUI.
main_window = MainWindow('MineGauler')
panel_widget = PanelWidget(main_window)
panel_widget.register_all_cbs(ctrlr)
mf_widget = MinefieldWidget(main_window, x, y, btn_size=56)
mf_widget.register_all_cbs(ctrlr)
main_window.set_panel_widget(panel_widget)
main_window.set_body_widget(mf_widget)
# Bind controller callbacks.
ctrlr.new_game_cb_list.append(panel_widget.new_game)
ctrlr.end_game_cb_list.append(panel_widget.end_game)
ctrlr.set_cell_cb_list.append(mf_widget.set_cell_image)
ctrlr.split_cell_cb_list.append(mf_widget.split_cell)
# Start the app.
main_window.show()
sys.exit(app.exec_())
