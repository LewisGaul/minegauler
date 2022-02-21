# January 2020, Lewis Gaul

import runpy
import sys

import setuptools


# version = runpy.run_path("minegauler/app/_version.py")["__version__"]
# # Should be a release version, e.g. "4.0.1"
# if "-" in version:
#     print("WARNING: Version is not a release version", file=sys.stderr)


setuptools.setup(
    packages=setuptools.find_packages(include="minegauler*"),
    package_data={
        "minegauler/app": [
            "boards/sample.mgb",
            "files/*.txt",
            "images/icon.ico",
            "images/faces/*",
            "images/buttons/*/*",
            "images/markers/*/*",
            "images/numbers/*/*",
        ],
        "minegauler/cli": [
            "cli.yaml",
        ],
    },
    zip_safe=False,
)
