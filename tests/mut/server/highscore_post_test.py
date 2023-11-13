# February 2022, Lewis Gaul

import pytest

from minegauler.app.highscores import HighscoreStruct
from minegauler.app.shared.types import Difficulty, GameMode, ReachSetting
from server import __main__ as server_main


# Mapping of supported app version to valid highscore post JSON.
SUPPORTED_VERSIONS = {
    "pre-4.1.2": {
        "difficulty": "M",
        "per_cell": 1,
        "drag_select": True,
        "name": "testname",
        "timestamp": 1234,
        "elapsed": 166.49,
        "bbbv": 322,
        "bbbvps": 1.94,
        "flagging": 0.0,
    },
    "4.1.2": {
        "app_version": "4.1.2",
        "highscore": {
            "game_mode": "regular",
            "difficulty": "M",
            "per_cell": 1,
            "drag_select": True,
            "name": "testname",
            "timestamp": 1234,
            "elapsed": 166.49,
            "bbbv": 322,
            "bbbvps": 1.94,
            "flagging": 0.0,
        },
    },
    "4.2.0": {
        "app_version": "4.2.0",
        "highscore": {
            "game_mode": "regular",
            "difficulty": "M",
            "per_cell": 1,
            "reach": 8,
            "drag_select": True,
            "name": "testname",
            "timestamp": 1234,
            "elapsed": 166.49,
            "bbbv": 322,
            "bbbvps": 1.94,
            "flagging": 0.0,
        },
    },
}

EXP_HIGHSCORE = HighscoreStruct(
    game_mode=GameMode.REGULAR,
    difficulty=Difficulty.MASTER,
    per_cell=1,
    reach=ReachSetting.NORMAL,
    drag_select=True,
    name="testname",
    timestamp=1234,
    elapsed=166.49,
    bbbv=322,
    bbbvps=1.94,
    flagging=0.0,
)


class TestConvertHighscore:
    """
    Tests for converting posted JSON to a highscore for supported app versions.
    """

    def test_v4_up_to_v4_1_2(self):
        hs = server_main.get_highscore_from_json(SUPPORTED_VERSIONS["pre-4.1.2"])
        assert hs == EXP_HIGHSCORE

    def test_v4_1_2(self):
        hs = server_main.get_highscore_from_json(SUPPORTED_VERSIONS["4.1.2"])
        assert hs == EXP_HIGHSCORE

    def test_v4_2_0(self):
        hs = server_main.get_highscore_from_json(SUPPORTED_VERSIONS["4.2.0"])
        assert hs == EXP_HIGHSCORE

    def test_beta_app_version(self):
        data = SUPPORTED_VERSIONS["4.1.2"].copy()  # note: shallow copy
        data["app_version"] = "4.1.2b8"
        hs = server_main.get_highscore_from_json(data)
        assert hs == EXP_HIGHSCORE

    def test_unexpected_app_version(self):
        data = SUPPORTED_VERSIONS["4.1.2"].copy()  # note: shallow copy
        data["app_version"] = "4.1.1"
        with pytest.raises(ValueError):
            server_main.get_highscore_from_json(data)
