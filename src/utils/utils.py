"""
utils.py - General utils to be * imported from any file in the app

March 2018, Lewis Gaul
"""


def ASSERT(condition, message):
    """
    The built-in assert as a function.
    """
    assert condition, message
