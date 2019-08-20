"""
__init__.py - The solver package API

August 2019, Lewis Gaul

There are a number of elements to solving a minesweeper board. The main two approaches are finding
the certain safe/unsafe cells and calculating the probability of each uncertain cell containing a
mine. Both approaches have their place, but are quite distinct (even though it is possible to
deduce certainties from probability calculations, these computations are often relatively slow).

The API to any of the functions that operate on a minesweeper board is to pass in a Board instance,
and a custom Grid instance will be returned (possibly a mutated version of the passed-in Board).
"""

from .deducer import deducer
from .probabilities import probabilities