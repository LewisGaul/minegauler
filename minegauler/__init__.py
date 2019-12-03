"""
__init__.py - Available imports from the package

December 2018, Lewis Gaul
"""

import pathlib


ROOT_DIR: pathlib.Path = pathlib.Path(__file__).parent

SETTINGS_FILE: pathlib.Path = ROOT_DIR / "settings.cfg"
