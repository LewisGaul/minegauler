import argparse
import logging
import os
import sys

from flask import Flask

from . import init_route_handling


logger = logging.getLogger(__name__)

app = Flask(__name__)


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, help="Override the default port")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    return parser.parse_args(argv)


def main(argv):
    args = _parse_args(argv)

    logging.basicConfig(
        filename="bot-server.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )

    init_route_handling(app)

    logger.info("Starting up")
    if args.dev:
        os.environ["FLASK_ENV"] = "development"
        app.run(debug=True, port=args.port)
    else:
        from waitress import serve

        serve(app, port=args.port)


main(sys.argv[1:])
