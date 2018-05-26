"""
main.py - Entry point for the main application

March 2018, Lewis Gaul
"""

import sys

from .core.game_logic import Controller
from .gui import app, MainWindow, MinefieldWidget, PanelWidget
from .gui.utils import FaceState


print("Running...")
x, y = 8, 4
ctrlr = Controller(x, y)
# Set up GUI.
main_window = MainWindow('MineGauler')
panel_widget = PanelWidget(main_window, ctrlr)
mf_widget = MinefieldWidget(main_window, ctrlr, btn_size=56)
main_window.set_panel_widget(panel_widget)
main_window.set_body_widget(mf_widget)
# Bind callbacks.
mf_widget.at_risk_cb = lambda : panel_widget.set_face(FaceState.ACTIVE)
mf_widget.no_risk_cb = lambda : panel_widget.set_face(FaceState.READY)
ctrlr.new_game_cb_list.append(panel_widget.new_game)
ctrlr.new_game_cb_list.append(
    lambda : setattr(mf_widget, 'clicks_enabled', True))
ctrlr.end_game_cb_list.append(panel_widget.end_game)
ctrlr.end_game_cb_list.append(
    lambda s: setattr(mf_widget, 'clicks_enabled', False))
ctrlr.set_cell_cb_list.append(mf_widget.set_cell_image)
ctrlr.split_cell_cb_list.append(mf_widget.split_cell)
# Start the app.
main_window.show()
sys.exit(app.exec_())
