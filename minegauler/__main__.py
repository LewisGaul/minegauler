"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""


import logging
import sys

from minegauler import frontend
from minegauler.backend import Controller, GameOptsStruct
from minegauler.frontend import GUIOptsStruct
from minegauler.shared.utils import (read_settings_from_file,
    write_settings_to_file)


logging.basicConfig(filename='runtime.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


read_settings = read_settings_from_file()

if read_settings:
    game_opts = GameOptsStruct._from_dict(read_settings)
    gui_opts = GUIOptsStruct._from_dict(read_settings)
    logger.info("Settings read from file")
else:
    logger.info("Using default settings")
    game_opts = GameOptsStruct()
    gui_opts = GUIOptsStruct()
logger.debug("Game options: %s", game_opts)
logger.debug("GUI options: %s", gui_opts)


logger.info("Starting up")

ctrlr = Controller(game_opts)

gui = frontend.create_gui(ctrlr, gui_opts)

ctrlr.register_callback(frontend.get_callback(gui,
                                              gui.panel_widget,
                                              gui.body_widget))

rc = frontend.run()


write_settings = {}
write_settings.update(ctrlr.opts)
write_settings.update(gui.opts)
write_settings_to_file(write_settings)


logger.info("Exiting")

sys.exit(rc)