"""
api.py - The API with the backend

December 2018, Lewis Gaul
"""

__all__ = ("AbstractController", "AbstractSwitchingController", "Listener")

import logging
import traceback
from typing import Dict

from .. import shared
from ..core.api import (
    AbstractController,
    AbstractListener,
    AbstractSwitchingController,
    EndedGameInfo,
)
from ..types import CellContentsType, GameState
from ..typing import Coord_T
from .main_window import MinegaulerGUI
from .minefield import MinefieldWidget
from .panel import PanelWidget


logger = logging.getLogger(__name__)


class Listener(AbstractListener):
    """
    Concrete implementation of a listener to receive callbacks from the
    backend.
    """

    def __init__(self, gui: MinegaulerGUI):
        self._gui: MinegaulerGUI = gui
        self._panel_widget: PanelWidget = self._gui.get_panel_widget()
        self._mf_widget: MinefieldWidget = self._gui.get_mf_widget()

    def reset(self) -> None:
        """
        Called to indicate the state should be reset.
        """
        self._panel_widget.reset()
        self._mf_widget.reset()

    def resize(self, x_size: int, y_size: int) -> None:
        """
        Called to indicate the board shape has changed.

        :param x_size:
            The number of rows.
        :param y_size:
            The number of columns.
        """
        self._gui.update_game_opts(x_size=x_size, y_size=y_size)
        self._mf_widget.resize(x_size, y_size)

    def set_mines(self, mines: int) -> None:
        """
        Called to indicate the default number of mines has changed.
        """
        self._gui.update_game_opts(mines=mines)
        self._panel_widget.set_mines(mines)

    def update_cells(self, cell_updates: Dict[Coord_T, CellContentsType]) -> None:
        for c, state in cell_updates.items():
            self._mf_widget.set_cell_image(c, state)

    def update_game_state(self, game_state: GameState) -> None:
        if game_state is not GameState.WON:
            self._gui.set_current_highscore(None)
        self._panel_widget.update_game_state(game_state)
        self._mf_widget.update_game_state(game_state)

    def update_mines_remaining(self, mines_remaining: int) -> None:
        self._panel_widget.set_mines_counter(mines_remaining)

    def handle_finished_game(self, info: EndedGameInfo) -> None:
        """
        Called once when a game ends.

        :param info:
            A store of end-game information.
        """
        self._panel_widget.timer.stop()
        self._panel_widget.timer.set_time(int(info.elapsed + 1))
        # Store the highscore if the game was won.
        if info.game_state is GameState.WON:
            highscore = shared.highscores.HighscoreStruct(
                difficulty=info.difficulty,
                per_cell=info.per_cell,
                timestamp=int(info.start_time),
                elapsed=info.elapsed,
                bbbv=info.bbbv,
                bbbvps=info.bbbv / info.elapsed,
                drag_select=self._gui.get_gui_opts().drag_select,  # TODO: this needs handling for when it's changed mid-game
                name=self._gui.get_gui_opts().name,
                flagging=info.flagging,
            )
            shared.highscores.insert_highscore(highscore)
            self._gui.set_current_highscore(highscore)
            # Check whether to pop up the highscores window.
            new_best = shared.highscores.is_highscore_new_best(highscore)
            if new_best:
                self._gui.open_highscores_window(highscore, new_best)

    def handle_exception(self, method: str, exc: Exception) -> None:
        logger.error(
            "Error occurred when calling %s() from backend:\n%s\n%s",
            method,
            "".join(traceback.format_exception(None, exc, exc.__traceback__)),
            exc,
        )
        raise RuntimeError(exc).with_traceback(exc.__traceback__)
