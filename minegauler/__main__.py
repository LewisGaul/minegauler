# December 2018, Lewis Gaul

"""
Entry point for the application.

"""

# Workaround to get the mysql libcrypto and libssl libs loaded.
import mysql.connector  # isort:skip

import logging
import sys

from . import core, frontend, paths, shared
from ._version import __version__


logger = logging.getLogger(__name__)


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # Create file handler which logs debug messages.
    fh = logging.FileHandler("runtime.log")
    fh.setLevel(logging.DEBUG)
    # Create console handler with a higher log level.
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # Create formatter and add it to the handlers.
    formatter = logging.Formatter("%(asctime)s[%(levelname)s](%(name)s) %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # Add the handlers to the logger.
    root.addHandler(fh)
    root.addHandler(ch)


setup_logging()


read_settings = shared.read_settings_from_file(paths.SETTINGS_FILE)

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
ctrlr = core.UberController(game_opts)
# Init frontend and create controller.
frontend.init_app()
frontend_state = frontend.state.State.from_opts(game_opts, gui_opts)
frontend_state.difficulty = ctrlr.get_game_info().difficulty
gui = frontend.MinegaulerGUI(ctrlr, frontend_state)
# Register frontend with core controller.
ctrlr.register_listener(gui)

# Run the app.
logger.debug("Entering event loop")
rc = frontend.run_app(gui)
logger.debug("Exiting event loop")


persist_settings = shared.AllOptsStruct.from_structs(
    ctrlr.get_game_options(), gui.get_gui_opts()
)
shared.write_settings_to_file(persist_settings, paths.SETTINGS_FILE)


logger.info("Exiting with exit code %d", rc)

sys.exit(rc)
