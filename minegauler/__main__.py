"""
__main__.py - Entry point for the application.

December 2018, Lewis Gaul
"""


import logging
import pickle
import sys
from pathlib import Path

from minegauler.backend import Controller, GameOptsStruct
from minegauler.frontend import run
from minegauler.shared.utils import root_dir


logging.basicConfig(filename='runtime.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


settings_file = Path(root_dir) / 'settings.cfg'


def retrieve_settings():
    logger.debug("Retrieving stored settings")
    read_settings = {}
    try:
        with open(settings_file, 'rb') as f:
            read_settings = pickle.load(f)
        logging.info("Settings read from file: %s", read_settings)
    except FileNotFoundError:
        logging.info("Settings file not found, default settings will be used")
    except pickle.UnpicklingError:
        logging.info("Unable to decode settings from file, default settings will "
                     "be used")
    except Exception as e:
        logging.info("Unexpected error reading settings from file, default "
                     "settings will be used")
        logging.debug("%s", e)

    game_opts = GameOptsStruct._from_dict(read_settings)
    # gui_opts  = GUIOptsStruct._from_dict(read_settings)

    return game_opts


def save_settings(ctrlr):
    write_settings = GameOptsStruct() #PersistOptsStruct()
    for k, v in ctrlr.opts.items():
        if k in write_settings:
            write_settings[k] = v
    # for k, v in main_window.opts.items():
    #     if k in write_settings.elements:
    #         save_settings[k] = v

    logger.info("Saving settings to file: %s", settings_file)
    with open(settings_file, 'wb') as f:
        pickle.dump(write_settings, f)


game_opts = retrieve_settings()

logger.info("Starting up")

ctrlr = Controller(game_opts)

rc = run(ctrlr)

save_settings(ctrlr)

logger.info("Exiting")

sys.exit(rc)