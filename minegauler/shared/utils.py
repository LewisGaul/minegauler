"""
utils.py - General utils

March 2018, Lewis Gaul
"""

from os.path import dirname, abspath, join


root_dir = dirname(dirname(abspath(__file__)))
files_dir = join(root_dir, 'files')


def ASSERT(condition, message):
    """
    The built-in assert as a function.
    """
    assert condition, message
