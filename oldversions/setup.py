# setup.py
from distutils.core import setup
import py2exe
import os

direc = os.getcwd()

setup(console=[os.path.join(direc, "minesweeper8.pyw")])
