"""
main_window_test.py - Test the main window of the GUI

December 2018, Lewis Gaul

Uses pytest - simply run 'python -m pytest tests/ [-k main_window_test]' from
the root directory.
"""

from unittest import mock

import pytest
from pytestqt.qtbot import QtBot

from minegauler import shared
from minegauler.core import api
from minegauler.frontend import main_window, minefield, panel, state
from minegauler.frontend.main_window import MinegaulerGUI
from minegauler.types import GameState

from ..utils import make_true_mock
from . import utils


_MockPanelWidget = make_true_mock(panel.PanelWidget)
_MockMinefieldWidget = make_true_mock(minefield.MinefieldWidget)


class TestMinegaulerGUI:
    """
    Tests for the main GUI window.
    """

    initial_state = state.State()

    _panel_class_mock = None
    _minefield_class_mock = None
    _name_bar_class_mock = None

    @classmethod
    def setup_class(cls):
        cls._panel_class_mock = mock.patch(
            "minegauler.frontend.panel.PanelWidget", side_effect=_MockPanelWidget
        ).start()
        cls._minefield_class_mock = mock.patch(
            "minegauler.frontend.minefield.MinefieldWidget",
            side_effect=_MockMinefieldWidget,
        ).start()
        mock.patch("minegauler.frontend.minefield.init_or_update_cell_images").start()
        mock.patch("minegauler.shared.highscores.insert_highscore").start()
        mock.patch("minegauler.shared.highscores.is_highscore_new_best").start()

    @classmethod
    def teardown_class(cls):
        mock.patch.stopall()

    @pytest.fixture
    def gui(
        self, qtbot: QtBot, ctrlr: api.AbstractSwitchingController
    ) -> MinegaulerGUI:
        gui = MinegaulerGUI(ctrlr, self.initial_state)
        qtbot.addWidget(gui)
        self._reset_gui_mocks(gui)
        return gui

    # --------------------------------------------------------------------------
    # Testcases
    # --------------------------------------------------------------------------
    def test_create(self, qtbot: QtBot, ctrlr: api.AbstractSwitchingController):
        """Test basic creation of the window."""
        gui = MinegaulerGUI(ctrlr, self.initial_state)
        qtbot.addWidget(gui)
        assert gui.windowTitle() == "Minegauler"
        assert not gui.windowIcon().isNull()
        # Check the menubar.
        exp_menus = ["Game", "Options", "Help"]
        assert [a.text() for a in gui.menuBar().actions()] == exp_menus
        # Check the main child widgets.
        assert type(gui._panel_widget) is _MockPanelWidget
        self._panel_class_mock.assert_called_once()
        assert type(gui._mf_widget) is _MockMinefieldWidget
        self._minefield_class_mock.assert_called_once()
        assert type(gui._name_entry_widget) is main_window._NameEntryBar
        gui.show()
        utils.maybe_stop_for_interaction(qtbot)

    def test_listener_methods(self, qtbot: QtBot, gui: MinegaulerGUI):
        """Test the AbstractListener methods."""
        # reset()
        gui.reset()
        gui._panel_widget.reset.assert_called_once()
        gui._mf_widget.reset.assert_called_once()

        # resize()
        gui._state.x_size = 8
        gui._state.y_size = 8
        gui.resize(3, 6)
        assert gui._state.x_size == 3
        assert gui._state.y_size == 6
        gui._mf_widget.resize.assert_called_once_with(3, 6)
        self._reset_gui_mocks(gui)

        # set_mines()
        gui._state.mines = 10
        gui.set_mines(2)
        assert gui._state.mines == 2

        # update_cells()
        cells = {1: "a", 2: "b", 3: "c"}
        gui.update_cells(cells)
        gui._mf_widget.set_cell_image.assert_has_calls(
            [mock.call(k, v) for k, v in cells.items()], any_order=True
        )
        assert gui._mf_widget.set_cell_image.call_count == len(cells)

        # update_game_state()
        gui._state.game_status = GameState.WON
        gui._state.highscores_state.current_highscore = "HIGHSCORE"
        gui.update_game_state(GameState.READY)
        assert gui._state.game_status is GameState.READY
        assert gui._state.highscores_state.current_highscore is None
        gui._panel_widget.update_game_state.assert_called_once_with(GameState.READY)

        # update_mines_remaining()
        gui.update_mines_remaining(56)
        gui._panel_widget.set_mines_counter.assert_called_once_with(56)

        # handle_finished_game()
        info = api.EndedGameInfo(GameState.WON, "M", 2, 1234.5678, 99.01, 123, 0.4)
        shared.highscores.is_highscore_new_best.return_value = "3bv/s"
        gui._state.drag_select = False
        gui._state.name = "NAME"
        exp_highscore = shared.highscores.HighscoreStruct(
            "M", 2, False, "NAME", 1234, 99.01, 123, 123 / 99.01, 0.4
        )
        with mock.patch.object(gui, "open_highscores_window") as mock_open:
            gui.handle_finished_game(info)
            gui._panel_widget.timer.stop.assert_called_once()
            gui._panel_widget.timer.set_time.assert_called_once_with(100)
            shared.highscores.insert_highscore.assert_called_once_with(exp_highscore)
            mock_open.assert_called_once_with(mock.ANY, "3bv/s")

        # handle_exception()
        with pytest.raises(RuntimeError):
            gui.handle_exception("method", ValueError())

    # --------------------------------------------------------------------------
    # Helper methods
    # --------------------------------------------------------------------------
    def _reset_gui_mocks(self, gui: MinegaulerGUI) -> None:
        """Reset mocks associated with a gui instance."""
        gui._panel_widget.reset_mock()
        gui._mf_widget.reset_mock()
