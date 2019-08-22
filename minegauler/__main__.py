"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""


import logging
import sys

import attr

from minegauler import frontend
from minegauler.core import Controller, GameOptsStruct
from minegauler.frontend import GuiOptsStruct
from minegauler.shared.utils import (read_settings_from_file,
    write_settings_to_file, PersistSettingsStruct
)


logging.basicConfig(filename='runtime.log', level=logging.DEBUG,
                    format='%(asctime)s[%(levelname)s](%(name)s) %(message)s')

logger = logging.getLogger(__name__)


read_settings = read_settings_from_file()

if read_settings:
    game_opts = GameOptsStruct._from_struct(read_settings)
    gui_opts = GuiOptsStruct._from_struct(read_settings)
    logger.info("Settings read from file")
else:
    logger.info("Using default settings")
    game_opts = GameOptsStruct()
    gui_opts = GuiOptsStruct()
logger.debug("Game options: %s", game_opts)
logger.debug("GUI options: %s", gui_opts)


logger.info("Starting up")

ctrlr = Controller(game_opts)

gui = frontend.create_gui(ctrlr, gui_opts)

ctrlr.register_callback(frontend.get_callback(gui,
                                              gui.panel_widget,
                                              gui.body_widget))

rc = frontend.run()



persist_settings = PersistSettingsStruct._from_multiple_structs(ctrlr.opts, gui.opts)
write_settings_to_file(persist_settings)


logger.info("Exiting with exit code %d", rc)

sys.exit(rc)