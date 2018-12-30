"""
api.py - The API with the backend

December 2018, Lewis Gaul
"""


from minegauler.shared.internal_types import GameState


def get_callback(gui, panel_widget, mf_widget):
    def callback(update):
        """
        Arguments:
        update (minegauler.backend.SharedInfo)
            The update from the backend.
        """
        if update.cell_updates is not None:
            for c, state in update.cell_updates.items():
                mf_widget.set_cell_image(c, state)

        if update.game_state is not None:
            panel_widget.update_game_state(update.game_state)

            if update.game_state in {GameState.WON, GameState.LOST}:
                mf_widget.ignore_clicks()
            else:
                mf_widget.accept_clicks()

        if update.mines_remaining is not None:
            panel_widget.set_mines_counter(update.mines_remaining)

    return callback