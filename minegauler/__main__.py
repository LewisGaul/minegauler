# December 2018, Lewis Gaul

"""
Entry point for the application.

"""

# Workaround to get the mysql libcrypto and libssl libs loaded.
import mysql.connector  # isort:skip

import logging
import sys

from . import core, frontend, shared
from ._version import __version__


logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="runtime.log",
    level=logging.DEBUG,
    format="%(asctime)s[%(levelname)s](%(name)s) %(message)s",
)


read_settings = shared.read_settings_from_file()

if read_settings:
    game_opts = shared.GameOptsStruct.from_structs(read_settings)
    gui_opts = shared.GUIOptsStruct.from_structs(read_settings)
    logger.info("Settings read from file")
else:
    logger.info("Using default settings")
    game_opts = shared.GameOptsStruct()
    gui_opts = shared.GUIOptsStruct()
logger.debug("Game options: %s", game_opts)
logger.debug("GUI options: %s", gui_opts)


logger.info("Starting up")

# Create core controller.
ctrlr = core.BaseController(game_opts)
# Init frontend and create controller.
frontend.init_app()
gui = frontend.MinegaulerGUI(ctrlr, frontend.state.State.from_opts(game_opts, gui_opts))
# Register frontend with core controller.
ctrlr.register_listener(gui)

# Run the app.
logger.debug("Entering event loop")
rc = frontend.run_app(gui)
logger.debug("Exiting event loop")


persist_settings = shared.AllOptsStruct.from_structs(
    ctrlr.get_game_options(), gui.get_gui_opts()
)
shared.write_settings_to_file(persist_settings)


logger.info("Exiting with exit code %d", rc)

sys.exit(rc)
