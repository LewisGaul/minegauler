[![Codecov badge](https://img.shields.io/codecov/c/github/LewisGaul/minegauler?token=85d4f08d368940708556d49c3150c06a)](https://codecov.io/gh/LewisGaul/minegauler/)
[![Code style badge](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/en/stable/)

# Minegauler

Remake of the classic Minesweeper game, written in Python.


![img1](img/screenshots/beginner_start.png)
![img2](img/screenshots/beginner_win.png)


## Try it out!

### Run the code

You will need Python3.6+ to run the code.

 - Clone the repo: `git clone https://github.com/LewisGaul/minegauler`
 - Consider setting up a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
 - Install requirements with `pip install -r requirements.txt`
 - Run with `python -m minegauler`


### Download the executable application

[Download from here](https://raw.githubusercontent.com/LewisGaul/minegauler/master/releases/MineGauler1.2.2.zip) to try out my most feature-rich version without any Python requirements (for Windows and Linux).

Note that I initially wrote this in Python 2 using Tkinter (now using PyQt5) and have since attempted multiple rewrites. While the codebase has improved drastically, sadly a lot of the features I once had have not yet rematerialised. Try the link above if you're interested in playing an *extremely* feature-rich (and possibly a little unstable) version.

Read more about the project history on [my website](https://www.lewisgaul.co.uk/minegauler.html).



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
