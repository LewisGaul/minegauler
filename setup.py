from distutils.core import setup
import py2exe, sys, os
from os.path import join, isdir, dirname
from glob import glob
import shutil
import json
import winshell

import numpy # So that all 'dll's are found.


main_direc = os.getcwd()
source_direc = join(main_direc, 'source')
sys.path.append(source_direc)
from main import (encode_highscore, get_highscores,
    __name__ as name, __version__ as version)

im_direc = join(dirname(main_direc), 'images')
data_direc = join(main_direc, 'data')
dest_direc = join(main_direc, 'Package')
if isdir(dest_direc):
    shutil.rmtree(dest_direc, ignore_errors=True)
if not isdir(dest_direc):
    os.mkdir(dest_direc)
desktop = winshell.desktop()


sys.argv.append('py2exe') # No need to type in command line.


target = raw_input("Who is this for?\n" +
                    "1) Home use (default)\n" +
                    "2) New user\n" +
                    "3) Other user\n"
                    "4) Archive\n")
if target == '2':
    target = ''
    with open(join(data_direc, 'data.txt'), 'r') as f:
        highscores = get_highscores(json.load(f), 1, 'Siwel G')
elif target == '3':
    target = raw_input("Input user's name: ")
    with open(join(data_direc, 'data.txt'), 'r') as f:
        highscores = get_highscores(json.load(f), name=target)
elif target == '4':
    target = 'archive'
else:
    target = 'home'
    with open(join(data_direc, 'data.txt'), 'r') as f:
        highscores = get_highscores(json.load(f))


# Image files
data_files = [('images', [join(im_direc, '3mine.ico')])]
for folder in ['mines', 'flags']:
    data_files.append((join('images', folder),
        glob(join(im_direc, folder, '*.png'))))
data_files.append((join('images', 'faces'),
        glob(join(im_direc, 'faces', '*.ppm'))))
# Text files
data_files.append(
    ('files', glob(join(main_direc, 'files', '*.txt'))))
data_files.append((dest_direc, glob(join(main_direc, '*.txt'))))
# Board files
data_files.append((join('boards', 'sample'),
    glob(join(main_direc, 'boards', 'sample', '*.mgb'))))
if target == 'archive':
    data_files.append(
        (join(dest_direc, 'dist', 'files'), [join(data_direc, 'data.txt')]))
    # Add source code files (not .pyc files).
    # This should go in the setup function.
    data_files.append(
        (join(dest_direc, 'src'), glob(join(source_direc, '*.*[!c]'))))


py2exe_options = {
        'compressed': True,
        'optimize': 1, # 2 does not work.
        'dist_dir': join(dest_direc, 'dist'),
        'excludes': ['pydoc', 'doctest', 'pdb', 'inspect', 'pyreadline',
            'locale', 'optparse', 'pickle', 'calendar']
        }

scripts = [{'dest_base': 'MineGauler', # Name of exe
            'script': join(source_direc, name + '.pyw'),
            'icon_resources': [(1, join(im_direc, '3mine.ico'))]}]
if target in ['home', 'archive']:
    scripts.append({'dest_base': 'Probabilities', # Name of exe
                    'script': join(source_direc, 'probabilities.pyw')})

setup(
    windows=scripts,
    options={'py2exe': py2exe_options},
    data_files=data_files,
    # zipfile=join(dest_direc, 'dist', 'lib.zip'),
    name='MineGauler',
    version=version,
    author='Lewis Gaul',
    author_email='minegauler@gmail.com'
    )

if target != 'archive':
    with open(join(dest_direc, 'dist', 'files', 'data.txt'), 'w') as f:
        json.dump(highscores, f)

shutil.rmtree('build', ignore_errors=True)

shutil.make_archive(
    join(main_direc, '%sMineGauler%s'%(target, version)), 'zip', dest_direc)

# with winshell.shortcut(
#     join(winshell.desktop(), 'MineGauler.lnk')) as shortcut:
#     shortcut.working_directory = join(dest_direc, 'dist')
#     shortcut.path = join(shortcut.working_directory, 'MineGauler.exe')