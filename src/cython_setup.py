import sys
import os, shutil
from distutils.core import setup, Extension

from Cython.Build import cythonize


fname = sys.argv.pop(1)
sys.argv += ['build_ext', '--inplace']

setup(
    ext_modules = cythonize('{}.pyx'.format(fname))
)

print("Removing build files...")
os.remove('{}.c'.format(fname))
shutil.rmtree('build', ignore_errors=True)
