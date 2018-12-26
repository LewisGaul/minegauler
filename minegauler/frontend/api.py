"""
api.py - The API with the backend

December 2018, Lewis Gaul
"""


def get_callback(gui, panel_widget, mf_widget):
    def callback(update):
        """
        Arguments:
        update (minegauler.backend.SharedInfo)
            The update from the backend.
        """
        for c, state in update.cell_updates.items():
            mf_widget.set_cell_image(c, state)

        panel_widget.update_game_state(update.game_state)
        panel_widget.set_mines_counter(update.mines_remaining)

    return callback