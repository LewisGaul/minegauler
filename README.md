[![Codecov badge](https://img.shields.io/codecov/c/github/LewisGaul/minegauler?token=85d4f08d368940708556d49c3150c06a)](https://codecov.io/gh/LewisGaul/minegauler/)
[![Code style badge](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/en/stable/)

# Minegauler

Remake of the classic Minesweeper game, written in Python.

Read more about the project history on [my website](https://www.lewisgaul.co.uk/minegauler.html).


![img1](img/screenshots/beginner_start.png)
![img2](img/screenshots/beginner_win.png)


## Try it out!

### Download the executable

The application has been packaged with PyInstaller so that it can be played without setting up Python.

Download links available here:
 - [Linux (64 bit)](https://raw.githubusercontent.com/LewisGaul/minegauler/master/releases/minegauler-4.0.4-linux-x86_64.tar.gz)


### Install from PyPI

The Python package is also available on PyPI: https://pypi.org/project/minegauler/.

 1. Python 3.6+ required (see note below for Python 3.8+)
 2. Install with `pip install minegauler`
 3. Run with `python -m minegauler`


### Clone the repo

You will need Python 3.6+ to run the code (see note below for getting it to run on Python 3.8+).

 1. Clone the repo: `git clone https://github.com/LewisGaul/minegauler`
 2. Consider setting up a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
 3. Install requirements with `pip install -r requirements.txt`
 4. Run with `python -m minegauler`


#### Python 3.8+

Annoyingly, the requirements listed in `requirements.txt` don't seem to work for Python 3.8+ due to the following dependency facts:

 - The oldest version of `PyQt5-sip` (required by `PyQt5`) supported on Python 3.8 is `4.19.17`.
 - `PyQt5` versions prior to `12.0` require a version of `PyQt5-sip` older than `4.19.17`.

The reason for not updating the requirements, is that `PyQt5` version `12.0` introduced a new system dependency on Ubuntu (`libxkbcommon-x11-0`) which isn't installed when you run `pip install pyqt5`.

However, if you want to run on Python 3.8+ you can do so!

 1. Follow steps `1.` and `2.` above
 2. Edit `requirements.txt`:
    - Replace `PyQt5==5.11.3` with `PyQt5==5.14.0`
    - Replace `PyQt5-sip==4.19.13` with `PyQt5-sip==12.7.0`
 3. Run with `python -m minegauler`
    - If this fails with `Aborted (core dumped)` on Linux, try installing the dependency with `sudo apt install libxkbcommon-x11-0`


## What's new/upcoming?

Check the [changelog](CHANGELOG.md) to see a log of changes that have been made, as well as some of the upcoming features and planned fixes.

If there's a feature you'd like to see added, please don't hesitate to [contact me](#Contact)!


## Development guide

Install the developer requirements (e.g. pytest + plugins) with `pip install -r requirements-dev.txt`.

Run the tests with the command: `python -m pytest`.

Get coverage information using the pytest-cov plugin: `python -m pytest --cov [--cov-report html]`.



## Contact

Email at minegauler@gmail.com, any questions/suggestions/requests welcome.

Alternatively, feel free to open an issue if you find a bug or have a feature request.
