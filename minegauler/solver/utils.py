"""
utils.py - Enumerations, constants and other utils

April 2018, Lewis Gaul
"""

from minegauler.utils import Grid


class ProbBoard(Grid):
    """ProbBoard class for handling displaying board probabilities."""
    def __repr__(self):
        return f"<{self.x_size}x{self.y_size} probability board>"
    def __str__(self):
        mapping = {}
        return super().__str__(mapping, cell_size=4)
