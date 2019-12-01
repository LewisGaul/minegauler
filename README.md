# Minegauler

Remake of the classic Minesweeper game, written in Python (requires Python 3.6+).


### Quick Start

 - Clone the repo
 - Recommended to set up a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
 - Install requirements with `pip install -r requirements.txt`
 - Run with `python -m minegauler`


### Download the Executable Application

[Download from here](https://raw.githubusercontent.com/LewisGaul/minegauler/master/releases/MineGauler1.2.2.zip) to try out my most feature-rich version without any Python requirements (for Windows and Linux).

Note that I initially wrote this in Python 2 using Tkinter (now using PyQt5) and have since attempted multiple rewrites. While the codebase has improved drastically, sadly a lot of the features I once had have not yet rematerialised. Try the link above if you're interested in playing an *extremely* feature-rich (and possibly a little unstable) version.

Read more about the project history on [my website](https://www.lewisgaul.co.uk/minegauler.html).


### Contact

Email at minegauler@gmail.com, any questions/suggestions/requests welcome.

Alternatively, feel free to open an issue if you find a bug or have a feature request.


## Developer information

Install the developer requirements (e.g. pytest + plugins) with `pip install -r requirements-dev.txt`.

Run the tests with the command: `python -m pytest`.

Get coverage information using the pytest-cov plugin: `python -m pytest --cov [--cov-report html]`.
