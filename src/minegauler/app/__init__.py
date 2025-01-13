__all__ = ("__version__", "api", "paths")

from . import paths
from ._metadata import VERSION
from .core import api


__version__ = VERSION
