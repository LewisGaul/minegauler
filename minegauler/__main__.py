"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""

import logging
import sys

import minegauler.shared.utils

from . import core, frontend, utils
from ._version import __version__


logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="runtime.log",
    level=logging.DEBUG,
    format="%(asctime)s[%(levelname)s](%(name)s) %(message)s",
)


read_settings = minegauler.shared.utils.read_settings_from_file()

if read_settings:
    game_opts = minegauler.shared.utils.GameOptsStruct.from_structs(read_settings)
    gui_opts = minegauler.shared.utils.GUIOptsStruct.from_structs(read_settings)
    logger.info("Settings read from file")
else:
    logger.info("Using default settings")
    game_opts = minegauler.shared.utils.GameOptsStruct()
    gui_opts = minegauler.shared.utils.GUIOptsStruct()
logger.debug("Game options: %s", game_opts)
logger.debug("GUI options: %s", gui_opts)


logger.info("Starting up")

# Create core controller.
ctrlr = core.BaseController(game_opts)
# Init frontend and create controller.
frontend.init_app()
gui = frontend.MinegaulerGUI(
    ctrlr, minegauler.shared.utils.AllOptsStruct.from_structs(game_opts, gui_opts)
)
# Register frontend with core controller.
ctrlr.register_listener(gui)

# Run the app.
logger.debug("Entering event loop")
rc = frontend.run_app(gui)
logger.debug("Exiting event loop")


persist_settings = minegauler.shared.utils.AllOptsStruct.from_structs(
    ctrlr.get_game_options(), gui.get_gui_opts()
)
minegauler.shared.utils.write_settings_to_file(persist_settings)


logger.info("Exiting with exit code %d", rc)

sys.exit(rc)
