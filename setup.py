from distutils.core import setup
import py2exe, sys, os
from os.path import join, isdir, dirname
from glob import glob
import shutil
import json
import winshell

import numpy # So that all 'dll's are found.

# Determine which highscores and scripts to include.
target = raw_input(
    "Who is this for?\n" +
    "1) Home use (default)\n" +
    "2) New user\n" +
    "3) Other user\n" +
    "4) Light\n" +
    "5) Archive\n"
    )

src_direc = 'src' if target == '4' else 'src2'
sys.path.append(src_direc)
from constants import *

# Destination directory.
destn = join('bin', str(VERSION))
if isdir(destn):
    shutil.rmtree(destn, ignore_errors=False)
if not isdir(destn):
    os.mkdir(destn)
desktop = winshell.desktop()

sys.argv.append('py2exe') #no need to type in command line

if target == '2':
    target = ''
    # with open(join(data_direc, 'data.txt'), 'r') as f:
    #     highscores = get_highscores(json.load(f), 1, 'Siwel G')
elif target == '3':
    target = raw_input("Input user's name: ")
    # with open(join(data_direc, 'data.txt'), 'r') as f:
    #     highscores = get_highscores(json.load(f), name=target)
elif target == '4':
    target = 'light'
elif target == '5':
    target = 'archive'
else:
    target = 'home'
    # with open(join(direcs['data'], 'data.txt'), 'r') as f:
    #     highscores = get_highscores(json.load(f))


data_files = [
    ('images', [join('images', 'icon.ico')]),
    (join('images', 'faces'), glob(join('images', 'faces', '*.ppm'))),
    (join('boards', 'sample'), glob(join('boards', 'sample', '*.mgb'))),
    ('files', glob(join('files', '*.txt'))),
    ('..', [
        join('files', 'README.txt'),
        'CHANGELOG.txt'
        ])
    ]

if target == 'light':
    data_files += [
        ('images', map(lambda x: join('images', x + '.png'), [
            'mine1',
            'flag1',
            'cross1',
            'btn_up',
            'btn_down',
            'btn_down_red'
            ])),
        ]
else:
    data_files += [
        ('images', glob(join('images', '*.png')))
        ]
if target == 'archive':
    data_files += [
        (join(destn, 'dist', 'src'), glob(join(src_direc, '*.*[!c]')))
        ]


py2exe_options = {
    'compressed': True,
    'optimize': 1, # 2 does not work.
    'dist_dir': join(destn, 'dist'),
    'excludes': ['pydoc', 'doctest', 'pdb', 'inspect', 'pyreadline',
        'locale', 'optparse', 'pickle', 'calendar']
    }

scripts = [{
    'dest_base': 'MineGauler', #name of exe
    'script': join(src_direc, 'main.pyw'),
    'icon_resources': [(1, join('images', 'icon.ico'))]
    }]
if target in ['home', 'archive']:
    scripts.append({
        'dest_base': 'Probabilities', #name of exe
        'script': join(src_direc, 'probabilities.pyw')
        })

setup(
    windows=scripts,
    options={'py2exe': py2exe_options},
    data_files=data_files,
    # zipfile=join(dest_direc, 'dist', 'lib.zip'),
    name='MineGauler',
    version=VERSION,
    author='Lewis H. Gaul',
    author_email='minegauler@gmail.com',
    url='github.com/LewisGaul'
    )

# if target not in ['light', 'archive']:
#     with open(join(destn, 'dist', 'files', 'data.txt'), 'w') as f:
#         json.dump(highscores, f)

shutil.rmtree('build', ignore_errors=True)

shutil.make_archive(join('bin', '%sMineGauler%s'%(target, VERSION)),
    'zip', destn)


# with winshell.shortcut(
#     join(winshell.desktop(), 'MineGauler.lnk')) as shortcut:
#     shortcut.working_directory = join(dest_direc, 'dist')
#     shortcut.path = join(shortcut.working_directory, 'MineGauler.exe')
