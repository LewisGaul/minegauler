"""
legacy_highscores.py - Compatibility layer with old versions

January 2020, Lewis Gaul
"""

import json
import logging
from typing import List, Optional

import attr

from minegauler.app.shared import highscores as hs


logger = logging.getLogger(__name__)


def _key_to_highscore_settings_v1_2(key: str) -> Optional[hs.HighscoreSettingsStruct]:
    """
    Convert an old highscore key to highscore settings.

    :param key:
        "<detection>,<difficulty>,<distance_to>,<drag_select>,<lives>,<per_cell>",
        e.g. "2,b,False,False,1,2".
    :return:
        The highscore settings, or None if not supported settings.
    :raise ValueError:
        If the key does not correspond to valid settings.
    """
    values = key.split(",")
    if len(values) != 6:
        raise ValueError(f"Expected key to have 6 values, got {len(values)}")

    detection = values[0]
    try:
        detection = float(detection)
    except ValueError:
        raise ValueError(f"Invalid detection value: {detection}")

    difficulty = values[1].upper()
    if difficulty not in ["B", "I", "E", "M"]:
        raise ValueError(f"Invalid difficulty value: {difficulty}")

    distance_to = values[2]
    if distance_to not in ["True", "False"]:
        raise ValueError(f"Unexpected distance_to value: {distance_to}")

    drag_select = values[3]
    if drag_select == "True":
        drag_select = True
    elif drag_select == "False":
        drag_select = False
    else:
        raise ValueError(f"Unexpected drag_select value: {drag_select}")

    lives = values[4]
    try:
        lives = int(lives)
    except ValueError:
        raise ValueError(f"Invalid lives value: {lives}")

    per_cell = values[5]
    try:
        per_cell = int(per_cell)
    except ValueError:
        raise ValueError(f"Invalid per_cell value: {per_cell}")

    if detection != 1 or distance_to is True or lives != 1 or not 1 <= per_cell <= 3:
        return None

    return hs.HighscoreSettingsStruct(
        difficulty=difficulty, per_cell=per_cell, drag_select=drag_select
    )


def read_highscore_file(file, version="1.2") -> List[hs.HighscoreStruct]:
    if version != "1.2":
        raise ValueError("Currently only support version 1.2")

    with open(file) as f:
        data = json.load(f)

    ret = []
    for k, values in data.items():
        settings = _key_to_highscore_settings_v1_2(k)
        if settings is None:
            logger.debug("Skipping unsupported settings key %r", k)
            continue
        logger.info("Proceeding with highscores for settings %s", settings)

        settings = attr.asdict(settings)
        for v in values:
            try:
                if not isinstance(v["name"], str) or v["name"] == "":
                    raise ValueError(
                        f"Name field should be non-empty string, got {v['name']}"
                    )
                fields = {
                    "timestamp": int(v["date"]),
                    "bbbv": int(v["3bv"]),
                    "bbbvps": float(v["3bv/s"]),
                    "elapsed": float(v["time"]),
                    "flagging": float(v["flagging"]),
                    "name": v["name"],
                }
            except (ValueError, TypeError) as e:
                logger.debug("Skipping highscore with invalid type: %s", str(e))
                continue

            ret.append(hs.HighscoreStruct(**settings, **fields))

    return ret
