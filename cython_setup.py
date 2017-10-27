import sys
import os
from os.path import exists
import shutil
from distutils.core import setup, Extension
import platform
from glob import glob

from Cython.Build import cythonize


fname = sys.argv.pop(1)
sys.argv += ['build_ext', '--inplace']

setup(
    ext_modules = cythonize('{}.pyx'.format(fname))
)
if platform.system() == 'Windows':
	extension = '.pyd'
elif platform.system() == 'Linux':
	extension = '.so'
else:
	print("Unexpected platform '{}'".format(platform.system()))
if exists('{}{}'.format(fname, extension)):
    os.remove('{}{}'.format(fname, extension))
output = glob('{}.*{}'.format(fname, extension))[0] #Must  be only file of this form
os.rename(output, '{}{}'.format(fname, extension))

print("Removing build files...")
os.remove('{}.c'.format(fname))
shutil.rmtree('build', ignore_errors=True)
