import pathlib
import sys


def run():
    sys.path.append(str(pathlib.Path(__file__).parent.parent))
    from server.bot import msgparse

    msgparse.main(sys.argv[1:])


run()
