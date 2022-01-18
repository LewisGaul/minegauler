# October 2018, Lewis Gaul

"""
Test the game engine module.

The game and board modules are treated as trusted.

"""

import json
import logging
from unittest import mock

import pytest

from minegauler.core import engine
from minegauler.shared.types import Difficulty, GameMode, UIMode
from minegauler.shared.utils import GameOptsStruct

from .. import utils


logger = logging.getLogger(__name__)


class TestUberController:
    """
    Test the base controller class.

    The responsibility of this controller is to pass calls on to the
    appropriate sub-controller, and provide the ability to switch between
    sub-controllers. These tests check this functionality using mocked
    sub-controllers.
    """

    mock_game_mode_impl = mock.MagicMock()
    mock_game_ctrlr_cls = mock_game_mode_impl.GameController
    mock_create_ctrlr_cls = mock_game_mode_impl.CreateController

    # --------------------------------------------------------------------------
    # Fixtures
    # --------------------------------------------------------------------------
    @pytest.fixture(autouse=True)
    def setup(self):
        yield
        self.mock_game_mode_impl.reset_mock()

    @pytest.fixture
    def ctrlr(self) -> engine.UberController:
        opts = GameOptsStruct()
        with mock.patch.dict(
            engine.GAME_MODE_IMPL,
            {GameMode.REGULAR: self.mock_game_mode_impl},
            clear=True,
        ):
            yield engine.UberController(opts)

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def reset_mocks(self) -> None:
        self.mock_game_mode_impl.reset_mock()

    # --------------------------------------------------------------------------
    # Test cases
    # --------------------------------------------------------------------------
    def test_basic_init(self, ctrlr):
        """Test basic creation of a controller."""
        assert ctrlr._opts == GameOptsStruct()
        assert ctrlr.mode is GameMode.REGULAR
        assert ctrlr._ui_mode is UIMode.GAME
        self.mock_game_ctrlr_cls.assert_called_once()

    def test_delegated(self, ctrlr):
        """Test methods/properties that are delegated to the active ctrlr."""
        game_ctrlr = self.mock_game_ctrlr_cls()

        assert ctrlr.board is game_ctrlr.board
        assert ctrlr.get_game_info() is game_ctrlr.get_game_info()

        ctrlr.new_game()
        game_ctrlr.new_game.assert_called_once_with()
        game_ctrlr.reset_mock()

        ctrlr.restart_game()
        game_ctrlr.restart_game.assert_called_once_with()
        game_ctrlr.reset_mock()

        ctrlr.select_cell((0, 1))
        game_ctrlr.select_cell.assert_called_once_with((0, 1))
        game_ctrlr.reset_mock()

        ctrlr.flag_cell((0, 1))
        game_ctrlr.flag_cell.assert_called_once_with((0, 1), flag_only=False)
        game_ctrlr.reset_mock()

        ctrlr.chord_on_cell((0, 1))
        game_ctrlr.chord_on_cell.assert_called_once_with((0, 1))
        game_ctrlr.reset_mock()

        ctrlr.remove_cell_flags((0, 1))
        game_ctrlr.remove_cell_flags.assert_called_once_with((0, 1))
        game_ctrlr.reset_mock()

        ctrlr.resize_board(2, 3, 4)
        game_ctrlr.resize_board.assert_called_once_with(2, 3, 4)
        game_ctrlr.reset_mock()

        ctrlr.set_difficulty(Difficulty.BEGINNER)
        game_ctrlr.set_difficulty.assert_called_once_with(Difficulty.BEGINNER)
        game_ctrlr.reset_mock()

        ctrlr.set_first_success(True)
        game_ctrlr.set_first_success.assert_called_once_with(True)
        game_ctrlr.reset_mock()

        ctrlr.set_per_cell(2)
        game_ctrlr.set_per_cell.assert_called_once_with(2)
        game_ctrlr.reset_mock()

        ctrlr.save_current_minefield("file")
        game_ctrlr.save_current_minefield.assert_called_once_with("file")
        game_ctrlr.reset_mock()

    def test_switch_mode(self, ctrlr):
        """Test switching sub-controller via UI mode."""
        game_ctrlr = self.mock_game_ctrlr_cls()
        create_ctrlr = self.mock_create_ctrlr_cls()

        # No op
        self.reset_mocks()
        ctrlr.switch_ui_mode(UIMode.GAME)
        assert ctrlr._ui_mode is UIMode.GAME
        assert ctrlr._active_ctrlr is game_ctrlr
        self.mock_game_ctrlr_cls.assert_not_called()
        self.mock_create_ctrlr_cls.assert_not_called()

        # Switch
        self.reset_mocks()
        ctrlr.switch_ui_mode(UIMode.CREATE)
        assert ctrlr._ui_mode is UIMode.CREATE
        assert ctrlr._active_ctrlr is create_ctrlr
        self.mock_create_ctrlr_cls.assert_called_once()
        self.mock_game_ctrlr_cls.assert_not_called()

        # Switch back
        self.reset_mocks()
        ctrlr.switch_ui_mode(UIMode.GAME)
        assert ctrlr._ui_mode is UIMode.GAME
        assert ctrlr._active_ctrlr is game_ctrlr
        self.mock_create_ctrlr_cls.assert_not_called()
        self.mock_game_ctrlr_cls.assert_called_once()

        # Invalid mode
        self.reset_mocks()
        with pytest.raises(ValueError):
            ctrlr.switch_ui_mode(None)

    def test_reset_settings(self, ctrlr):
        """Test resetting controller settings."""
        game_ctrlr = self.mock_game_ctrlr_cls()
        ctrlr._opts.x_size = 100
        ctrlr.switch_ui_mode(UIMode.CREATE)
        self.reset_mocks()

        ctrlr.reset_settings()
        assert ctrlr._active_ctrlr == game_ctrlr
        assert ctrlr._ui_mode == UIMode.GAME
        self.mock_game_ctrlr_cls.assert_called_once()
        game_ctrlr.resize_board.assert_called_once_with(8, 8, 10)

    def test_load_minefield(self, ctrlr):
        """Test the method to load a minefield."""
        game_ctrlr = self.mock_game_ctrlr_cls()
        create_ctrlr = self.mock_create_ctrlr_cls()

        # Delegated in game mode.
        self.reset_mocks()
        with utils.patch_open("file", json.dumps({"type": "REGULAR"})):
            ctrlr.load_minefield("file")
        game_ctrlr.load_minefield.assert_called_once_with("file")

        # In create mode, the mode is switched first.
        self.reset_mocks()
        ctrlr.switch_ui_mode(UIMode.CREATE)
        assert ctrlr._active_ctrlr is create_ctrlr
        with utils.patch_open("file", json.dumps({"type": "REGULAR"})):
            ctrlr.load_minefield("file")
        assert ctrlr._ui_mode is UIMode.GAME
        assert ctrlr._active_ctrlr is game_ctrlr
        game_ctrlr.load_minefield.assert_called_once_with("file")
