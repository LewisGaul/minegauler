# October 2021, Lewis Gaul

__all__ = ("Minefield",)

from ..regular.minefield import RegularMinefieldBase
from .board import Board


class Minefield(RegularMinefieldBase[Board]):
    """A split-cell minefield."""

    # Note: Properties like openings are dependent on the state of the board
    #  (whether cells are split). However, a minefield does still have the
    #  concept of 'minimum left clicks' (i.e. a variant of 3bv) and completed
    #  board - these are just more complex to compute!

    def _calc_3bv(self) -> int:
        """Calculate the 3bv of the board."""
        return 0  # TODO

    def _calc_completed_board(self) -> Board:
        """
        Create the completed board with the flags and numbers that should be
        seen upon game completion.
        """
        return Board(self.x_size, self.y_size)  # TODO
