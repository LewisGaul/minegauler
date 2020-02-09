import pathlib
import sys


def run():
    sys.path.append(str(pathlib.Path(__file__).parent.parent))
    from server.bot import msgparse, utils

    utils.USER_NAMES = {"legaul": "Siwel G", "someone": "Big O-dog"}
    msgparse.main(sys.argv[1:])


run()
