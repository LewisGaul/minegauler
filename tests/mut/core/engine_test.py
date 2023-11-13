# October 2018, Lewis Gaul

"""
Test the game engine module.

The game and board modules are treated as trusted.

"""

import json
import logging
from unittest import mock

import pytest

from minegauler.app.core import engine
from minegauler.app.shared.types import Difficulty, GameMode, UIMode, ReachSetting
from minegauler.app.shared.utils import GameOptsStruct

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

    mock_regular_game_mode_impl = mock.MagicMock()
    mock_regular_game_ctrlr_cls = mock_regular_game_mode_impl.GameController
    mock_regular_create_ctrlr_cls = mock_regular_game_mode_impl.CreateController
    mock_split_cell_game_mode_impl = mock.MagicMock()
    mock_split_cell_game_ctrlr_cls = mock_split_cell_game_mode_impl.GameController
    mock_split_cell_create_ctrlr_cls = mock_split_cell_game_mode_impl.CreateController

    # --------------------------------------------------------------------------
    # Fixtures
    # --------------------------------------------------------------------------
    @pytest.fixture(autouse=True)
    def setup(self):
        yield
        self.reset_mocks()

    @pytest.fixture
    def ctrlr(self) -> engine.UberController:
        opts = GameOptsStruct()
        with mock.patch.dict(
            engine.GAME_MODE_IMPL,
            {
                GameMode.REGULAR: self.mock_regular_game_mode_impl,
                GameMode.SPLIT_CELL: self.mock_split_cell_game_mode_impl,
            },
            clear=True,
        ):
            yield engine.UberController(opts)

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def reset_mocks(self) -> None:
        self.mock_regular_game_mode_impl.reset_mock()
        self.mock_split_cell_game_mode_impl.reset_mock()

    # --------------------------------------------------------------------------
    # Test cases
    # --------------------------------------------------------------------------
    def test_basic_init(self, ctrlr):
        """Test basic creation of a controller."""
        assert ctrlr._opts == GameOptsStruct()
        assert ctrlr.mode is GameMode.REGULAR
        assert ctrlr._ui_mode is UIMode.GAME
        self.mock_regular_game_ctrlr_cls.assert_called_once()

    def test_delegated(self, ctrlr):
        """Test methods/properties that are delegated to the active ctrlr."""
        game_ctrlr = self.mock_regular_game_ctrlr_cls()

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

    def test_switch_ui_mode(self, ctrlr):
        """Test switching sub-controller via UI mode."""
        game_ctrlr = self.mock_regular_game_ctrlr_cls()
        create_ctrlr = self.mock_regular_create_ctrlr_cls()

        # No op
        self.reset_mocks()
        ctrlr.switch_ui_mode(UIMode.GAME)
        assert ctrlr._ui_mode is UIMode.GAME
        assert ctrlr._active_ctrlr is game_ctrlr
        self.mock_regular_game_ctrlr_cls.assert_not_called()
        self.mock_regular_create_ctrlr_cls.assert_not_called()

        # Switch
        self.reset_mocks()
        ctrlr.switch_ui_mode(UIMode.CREATE)
        assert ctrlr._ui_mode is UIMode.CREATE
        assert ctrlr._active_ctrlr is create_ctrlr
        self.mock_regular_create_ctrlr_cls.assert_called_once()
        self.mock_regular_game_ctrlr_cls.assert_not_called()

        # Switch back
        self.reset_mocks()
        ctrlr.switch_ui_mode(UIMode.GAME)
        assert ctrlr._ui_mode is UIMode.GAME
        assert ctrlr._active_ctrlr is game_ctrlr
        self.mock_regular_create_ctrlr_cls.assert_not_called()
        self.mock_regular_game_ctrlr_cls.assert_called_once()

        # Invalid mode
        self.reset_mocks()
        with pytest.raises(ValueError):
            ctrlr.switch_ui_mode(None)

    def test_switch_game_mode(self, ctrlr):
        """Test switching sub-controller via game mode."""
        regular_ctrlr = self.mock_regular_game_ctrlr_cls()
        split_ctrlr = self.mock_split_cell_game_ctrlr_cls()

        # No op
        self.reset_mocks()
        ctrlr.switch_game_mode(GameMode.REGULAR)
        assert ctrlr.mode is GameMode.REGULAR
        assert ctrlr._active_ctrlr is regular_ctrlr
        self.mock_regular_game_ctrlr_cls.assert_not_called()
        self.mock_regular_create_ctrlr_cls.assert_not_called()
        self.mock_split_cell_game_ctrlr_cls.assert_not_called()
        self.mock_split_cell_create_ctrlr_cls.assert_not_called()

        # Switch to split-cell (resets 'reach' setting)
        ctrlr._opts.reach = ReachSetting.SHORT
        self.reset_mocks()
        ctrlr.switch_game_mode(GameMode.SPLIT_CELL)
        assert ctrlr.mode is GameMode.SPLIT_CELL
        assert ctrlr._active_ctrlr is split_ctrlr
        assert ctrlr._opts.reach is ReachSetting.NORMAL
        self.mock_split_cell_game_ctrlr_cls.assert_called_once()
        self.mock_regular_game_ctrlr_cls.assert_not_called()

        # Switch back to regular
        self.reset_mocks()
        ctrlr.switch_game_mode(GameMode.REGULAR)
        assert ctrlr.mode is GameMode.REGULAR
        assert ctrlr._active_ctrlr is regular_ctrlr
        self.mock_split_cell_game_ctrlr_cls.assert_not_called()
        self.mock_regular_game_ctrlr_cls.assert_called_once()

    def test_reset_settings(self, ctrlr):
        """Test resetting controller settings."""
        regular_game_ctrlr = self.mock_regular_game_ctrlr_cls()
        split_cell_game_ctrlr = self.mock_split_cell_game_ctrlr_cls()

        # Reset from regular game mode, create UI mode.
        ctrlr._opts.x_size = 100
        ctrlr._opts.reach = ReachSetting.SHORT
        ctrlr.switch_ui_mode(UIMode.CREATE)
        self.reset_mocks()
        ctrlr.reset_settings()
        assert ctrlr._active_ctrlr is regular_game_ctrlr
        assert ctrlr._ui_mode is UIMode.GAME
        assert ctrlr._opts.reach is ReachSetting.NORMAL
        self.mock_split_cell_game_ctrlr_cls.assert_not_called()
        self.mock_regular_game_ctrlr_cls.assert_called_once()
        regular_game_ctrlr.resize_board.assert_called_once_with(8, 8, 10)

        # Reset from split-cell game mode, game UI mode.
        ctrlr._opts.mode = GameMode.SPLIT_CELL
        ctrlr._opts.x_size = 100
        self.reset_mocks()
        ctrlr.reset_settings()
        assert ctrlr._active_ctrlr is regular_game_ctrlr
        assert ctrlr._ui_mode is UIMode.GAME
        assert ctrlr.mode is GameMode.REGULAR
        self.mock_split_cell_game_ctrlr_cls.assert_not_called()
        self.mock_regular_game_ctrlr_cls.assert_called_once()
        regular_game_ctrlr.resize_board.assert_called_once_with(8, 8, 10)

    def test_load_minefield(self, ctrlr):
        """Test the method to load a minefield."""
        game_ctrlr = self.mock_regular_game_ctrlr_cls()
        create_ctrlr = self.mock_regular_create_ctrlr_cls()

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
