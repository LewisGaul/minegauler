"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""

import logging
import sys

from minegauler import core, frontend, utils


logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="runtime.log",
    level=logging.DEBUG,
    format="%(asctime)s[%(levelname)s](%(name)s) %(message)s",
)


read_settings = utils.read_settings_from_file()

if read_settings:
    game_opts = core.utils.GameOptsStruct._from_struct(read_settings)
    gui_opts = frontend.utils.GuiOptsStruct._from_struct(read_settings)
    logger.info("Settings read from file")
else:
    logger.info("Using default settings")
    game_opts = core.GameOptsStruct()
    gui_opts = frontend.GuiOptsStruct()
logger.debug("Game options: %s", game_opts)
logger.debug("GUI options: %s", gui_opts)


logger.info("Starting up")

ctrlr = core.BaseController(game_opts)
# ctrlr = core.create.CreateController(game_opts)

gui = frontend.create_gui(ctrlr, gui_opts, game_opts)

# TODO: Legacy - remove
# ctrlr.register_callback(frontend.get_callback(gui, gui.panel_widget, gui.body_widget))
ctrlr.register_listener(frontend.Listener(gui))

rc = frontend.run()


persist_settings = utils.PersistSettingsStruct._from_multiple_structs(
    ctrlr.opts, gui.gui_opts
)
utils.write_settings_to_file(persist_settings)


logger.info("Exiting with exit code %d", rc)

sys.exit(rc)
