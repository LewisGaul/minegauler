# January 2020, Lewis Gaul

import runpy
import sys

import setuptools


with open("README.pypi.md", "r", encoding="utf-8") as f:
    long_description = f.read()

version = runpy.run_path("src/minegauler/app/_version.py")["__version__"]
# Should be a release version, e.g. "4.0.1"
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
    project_urls={
        "Bug Reports": "https://github.com/LewisGaul/minegauler/issues",
        "Source": "https://github.com/LewisGaul/minegauler/",
        "Background": "https://www.lewisgaul.co.uk/blog/coding/2020/02/12/minegauler/",
    },
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
    packages=setuptools.find_packages(where="src", include=("minegauler*",)),
    package_dir={"": "src"},
    package_data={
        "minegauler.app": [
            "boards/sample.mgb",
            "files/*.txt",
            "images/icon.ico",
            "images/faces/*",
            "images/buttons/*/*",
            "images/markers/*/*",
            "images/numbers/*/*",
        ],
    },
    install_requires=[
        "attrs",
        "PyQt5",
        "requests",
        "typing-extensions",
        "zig-minesolver >= 0.1.1, < 0.2",
    ],
    extras_require={
        "bot": [
            "pytz",
            "requests-toolbelt",
            "tabulate",
        ],
    },
    entry_points={
        "gui_scripts": [
            "minegauler = minegauler.app.__main__:main",
        ],
        "console_scripts": [
            "minegauler-bot = minegauler.bot.msgparse:main [bot]",
        ],
    },
    zip_safe=False,
)
