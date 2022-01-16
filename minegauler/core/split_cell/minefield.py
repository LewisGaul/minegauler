# October 2021, Lewis Gaul

__all__ = ("Minefield",)

from typing import Any, Mapping

from ...shared.types import CellContents
from ..regular.minefield import RegularMinefieldBase
from .board import Board
from .types import Coord


class Minefield(RegularMinefieldBase[Coord, Board]):
    """A split-cell minefield."""

    # Note: Properties like openings are dependent on the state of the board
    #  (whether cells are split). However, a minefield does still have the
    #  concept of 'minimum left clicks' (i.e. a variant of 3bv) and completed
    #  board - these are just more complex to compute!

    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> "Minefield":
        """
        Create a minefield instance from a JSON encoding.

        :param obj:
            The dictionary obtained from decoding JSON. Must contain the
            following fields: 'x_size', 'y_size', 'mine_coords'.
        :raise ValueError:
            If the dictionary is missing required fields.
        """
        try:
            return cls.from_coords(
                (
                    Coord(x, y, True)
                    for x in range(obj["x_size"])
                    for y in range(obj["y_size"])
                ),
                mine_coords=[Coord(*c, True) for c in obj["mine_coords"]],
                per_cell=obj.get("per_cell", 1),
            )
        except KeyError as e:
            raise ValueError(
                "Missing key in dictionary when trying to create minefield"
            ) from e

    def to_json(self) -> Mapping[str, Any]:
        return dict(
            type="split_cell",
            x_size=self.x_size,
            y_size=self.y_size,
            mine_coords=[(c.x, c.y) for c in self.mine_coords],
            per_cell=self.per_cell,
        )

    def _calc_3bv(self) -> int:
        """Calculate the 3bv of the board."""
        return 0  # TODO

    def _calc_completed_board(self) -> Board:
        """
        Create the completed board with the flags and numbers that should be
        seen upon game completion.
        """
        board = Board(self.x_size, self.y_size)
        # First mark all mines as flags, splitting the containing big cells.
        for coord in set(self.mine_coords):
            if coord not in board:
                big_coord = board.get_coord_at(coord.x, coord.y)
                board.split_coord(big_coord)
            board[coord] = CellContents.Flag(self.mine_coords.count(coord))
        # Now calculate numbers for all remaining cells.
        for coord in board.all_coords:
            if board[coord] is not CellContents.Unclicked:
                continue
            num = sum(
                self[c]
                for c in board.get_nbrs(coord)
                if type(board[c]) is CellContents.Flag
            )
            board[coord] = CellContents.Num(num)
        return board
