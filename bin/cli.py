import pathlib
import sys
from typing import List


def run(argv: List[str]):
    sys.path.append(str(pathlib.Path(__file__).parent.parent))
    from bot import msgparse
    from bot import utils

    utils.USER_NAMES = {
        "legaul": "Siwel G",
        "someone": "Big O-dog",
        "person": "Felix",
        "stan": "stan",
        "kkw": "KKW",
    }
    msgparse.main(argv)


if __name__ == "__main__":
    run(sys.argv[1:])
