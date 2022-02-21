# February 2020, Lewis Gaul

"""
Bot package.

"""

from . import formatter, msgparse, utils


try:
    from . import routes
except ImportError:
    pass
