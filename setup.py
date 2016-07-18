from distutils.core import setup
import py2exe, sys, os
from os.path import join, isdir, dirname
from glob import glob
import shutil
import json
import winshell

import numpy # So that all 'dll's are found.

src_direc = join(os.getcwd(), 'src')
sys.path.append(src_direc)
os.chdir(src_direc)
from utils import *

direcs['src'] = src_direc
direcs['destn'] = join(direcs['main'], 'bin')
if isdir(direcs['destn']):
    shutil.rmtree(direcs['destn'], ignore_errors=False)
if not isdir(direcs['destn']):
    os.mkdir(direcs['destn'])
desktop = winshell.desktop()

sys.argv.append('py2exe') #no need to type in command line

# Determine which highscores and scripts to include.
target = raw_input(
    "Who is this for?\n" +
    "1) Home use (default)\n" +
    "2) New user\n" +
    "3) Other user\n" +
    "4) Light\n" +
    "5) Archive\n"
    )

if target == '2':
    target = ''
    with open(join(data_direc, 'data.txt'), 'r') as f:
        highscores = get_highscores(json.load(f), 1, 'Siwel G')
elif target == '3':
    target = raw_input("Input user's name: ")
    with open(join(data_direc, 'data.txt'), 'r') as f:
        highscores = get_highscores(json.load(f), name=target)
elif target == '4':
    target = 'light'
elif target == '5':
    target = 'archive'
else:
    target = 'home'
    with open(join(data_direc, 'data.txt'), 'r') as f:
        highscores = get_highscores(json.load(f))
######
print "Running "
target = 'light'


data_files = [
    ('images', map(lambda x: join(direcs['images'], x), [
        'cross1.png',
        'flag1.png',
        'mine1.png',
        'icon.ico'
        ])),
    (join('images', 'faces'), map(
        lambda x: join(direcs['images'], 'faces', x), [
        'active1face.ppm',
        'ready1face.ppm',
        'lost1face.ppm',
        'won1face.ppm'
        ])),
    (join(direcs['boards'], 'sample'),
        glob(join(direcs['boards'], 'sample', '*.mgb'))),
    ('files', glob(join(direcs['files'], '*.txt'))),
    (direcs['destn'], [
        join(direcs['files'], 'README.txt'),
        join(direcs['main'], 'CHANGELOG.txt')
        ])
    ]

if target == 'archive':
    data_files.append(
        (join(direcs['destn'], 'dist', 'files'), [join(data_direc, 'data.txt')]))
    # Add source code files (not .pyc files).
    # This should go in the setup function.
    data_files.append(
        (join(direcs['destn'], 'src'), glob(join(source_direc, '*.*[!c]'))))


py2exe_options = {
    'compressed': True,
    'optimize': 1, # 2 does not work.
    'dist_dir': join(direcs['destn'], 'dist'),
    'excludes': ['pydoc', 'doctest', 'pdb', 'inspect', 'pyreadline',
        'locale', 'optparse', 'pickle', 'calendar']
    }

scripts = [{
    'dest_base': 'MineGauler', #name of exe
    'script': join(direcs['src'], 'main.pyw'),
    'icon_resources': [(1, join(direcs['images'], 'icon.ico'))]
    }]
if target in ['home', 'archive']:
    scripts.append({
        'dest_base': 'Probabilities', # Name of exe
        'script': join(direcs['src'], 'probabilities.pyw')
        })

setup(
    windows=scripts,
    options={'py2exe': py2exe_options},
    data_files=data_files,
    # zipfile=join(dest_direc, 'dist', 'lib.zip'),
    name='MineGauler',
    version=VERSION,
    author='Lewis H. Gaul',
    author_email='minegauler@gmail.com'
    )

if target != 'archive':
    with open(join(direcs['destn'], 'dist', 'files', 'data.txt'), 'w') as f:
        json.dump(highscores, f)

shutil.rmtree(join(direcs['main'], 'build', ignore_errors=True)

shutil.make_archive(join(direcs['main'], '%sMineGauler%s'%(target, VERSION)),
    'zip', direcs['destn'])

# with winshell.shortcut(
#     join(winshell.desktop(), 'MineGauler.lnk')) as shortcut:
#     shortcut.working_directory = join(dest_direc, 'dist')
#     shortcut.path = join(shortcut.working_directory, 'MineGauler.exe')