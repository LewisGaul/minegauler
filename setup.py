"""
setup.py - Setup script

January 2020, Lewis Gaul
"""

import sys

import setuptools


long_description = """
[![Build badge](https://img.shields.io/github/workflow/status/LewisGaul/minegauler/Workflow%20for%20full%20test%20matrix/dev)](https://github.com/LewisGaul/minegauler/actions?query=workflow%3A%22Workflow+for+full+test+matrix%22+branch%3Adev)
[![Codecov badge](https://img.shields.io/codecov/c/github/LewisGaul/minegauler/dev)](https://codecov.io/gh/LewisGaul/minegauler/)
[![PyPI badge](https://img.shields.io/pypi/v/minegauler.svg)](https://pypi.python.org/pypi/minegauler/)
[![Downloads badge](https://img.shields.io/github/downloads/LewisGaul/minegauler/total)](https://github.com/LewisGaul/minegauler/releases/)
[![Code style badge](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/en/stable/)


A perfect clone of the classic Minesweeper game, with many added features.

Read more about the project history on [the project homepage](https://github.com/LewisGaul/minegauler).


![img1](https://raw.githubusercontent.com/LewisGaul/minegauler/26fbc3d0fad5c70e5e9f9a1c37114da1d92507e5/img/screenshots/beginner_start.png)
![img2](https://raw.githubusercontent.com/LewisGaul/minegauler/26fbc3d0fad5c70e5e9f9a1c37114da1d92507e5/img/screenshots/beginner_win.png)


## Install and Run

Install with `pip install minegauler`, and then run with `python -m minegauler`.


## Features

 - Basic functional game
 - Ability to specify custom board size/number of mines
 - Ability to replay a game
 - Mode to create boards
 - Ability to save and load boards (created or played)
 - Get current game information, including predicted completion time for lost game
 - Option of whether first click will guarantee an opening
 - Option to select cells by click-and-drag technique with the mouse
 - Option to allow multiple mines per cell
 - Local highscores for standard difficulty modes
 - Highscores uploaded to remote server when there is an internet connection
 - Custom cell styles
 - Option to change the cell size
 - Ability to reduce the window size and use scroll


## Contact

Email at minegauler@gmail.com, any questions/suggestions/requests welcome.

Alternatively, feel free to [open an issue](https://github.com/LewisGaul/minegauler/issues) if you find a bug or have a feature request.

"""

# Should be a release version, e.g. "4.0.1"
version = "4.1.0"
if "-" in version:
    print("WARNING: Version is not a release version", file=sys.stderr)


setuptools.setup(
    name="minegauler",
    version=version,
    author="Lewis Gaul",
    author_email="minegauler@gmail.com",
    description="A clone of the original minesweeper game with many added features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LewisGaul/minegauler",
    packages=setuptools.find_packages(include="minegauler*"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Topic :: Games/Entertainment :: Puzzle Games",
    ],
    python_requires=">=3.7",
    install_requires=[
        "attrs",
        "mysql-connector-python==8.*",
        "PyQt5",
        "requests",
    ],
    package_data={
        "minegauler": [
            "boards/sample.mgb",
            "files/*.txt",
            "images/icon.ico",
            "images/faces/*",
            "images/buttons/*/*",
            "images/markers/*/*",
            "images/numbers/*/*",
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/LewisGaul/minegauler/issues",
        "Source": "https://github.com/LewisGaul/minegauler/",
        "Background": "https://www.lewisgaul.com/minegauler",
    },
    zip_safe=False,
)
