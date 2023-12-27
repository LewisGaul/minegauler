#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from typing import Iterable

from minegauler.app import highscores as hs


logger = logging.getLogger(__name__)


def format_timestamp(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts).isoformat()


def print_highscore_stats(highscores: Iterable[hs.HighscoreStruct]) -> None:
    print("Total:", len(highscores))
    print("Oldest:", format_timestamp(min(h.timestamp for h in highscores)))
    print("Most recent:", format_timestamp(max(h.timestamp for h in highscores)))
    print("Number of usernames:", len({h.name for h in highscores}))
    print("Number of modes:", len({(h.game_mode, h.difficulty, h.per_cell, h.reach, h.drag_select) for h in highscores}))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logs")
    parser.add_argument("file", help="SQLite DB file path")
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    db = hs.SQLiteDB(args.file)
    all_highscores = hs.get_highscores(database=db)
    print_highscore_stats(all_highscores)


if __name__ == "__main__":
    main(sys.argv[1:])
