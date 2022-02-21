# February 2022, Lewis Gaul

import runpy
import sys


if len(sys.argv) == 1:
    runpy.run_module("minegauler.app", run_name="__main__")
else:
    try:
        runpy.run_module("minegauler.cli", run_name="__main__")
    except ImportError:
        print("Expected no CLI arguments", file=sys.stderr)
        sys.exit(1)
