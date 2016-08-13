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

src_direc = 'src' if target == 'light' else 'src2'
sys.path.append(src_direc)
from constants import *

# Destination directory.
destn = join('bin', str(VERSION) + target)
if isdir(destn):
    shutil.rmtree(destn, ignore_errors=False)
if not isdir(destn):
    os.mkdir(destn)
desktop = winshell.desktop()

sys.argv.append('py2exe') #no need to type in command line

def get_data_files(folder, files, pattern=None):
    if not type(files) is list:
        pattern = files
    if pattern:
        files = glob(join(folder, pattern))
    else:
        files = map(lambda f: join(folder, f), files)
    return (folder, files)

data_files = [
    ('..', [join('files', 'README.txt'), 'CHANGELOG.txt']),
    get_data_files(join('boards', 'sample'), '*.mgb'),
    get_data_files('images', 'icon.ico'),
    get_data_files('files', '*.txt')
    ]


if target == 'light': #sort out
    data_files.append(get_data_files(join('images', 'faces'), [
        'active1face.ppm',
        'ready1face.ppm',
        'won1face.ppm',
        'lost1face.ppm'
        ]))
    for i in glob(join('images', 'buttons', '*')):
        data_files.append(get_data_files(i, [
            'btn_down.png',
            'btn_up.png',
            'btn_down_red.png'
            ]))
    for i in glob(join('images', 'numbers', '*')):
        data_files.append(get_data_files(i,
            map(lambda n: 'num%s.png'%n, range(1, 9))))
    for i in glob(join('images', 'images', '*')):
        data_files.append(get_data_files(i, '*1.png'))
else:
    data_files.append(get_data_files(join('images', 'faces'), '*.ppm'))
    for i in ['buttons', 'images', 'numbers']:
        for j in glob(join('images', i, '*')):
            data_files.append(get_data_files(j, '*.png'))
if target == 'archive':
    data_files.append(
        (join(destn, 'dist', 'src'), glob(join(src_direc, '*.*[!c]'))))


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
    url=r'github.com/LewisGaul',
    author_email=r'minegauler@gmail.com'
    )

# if target not in ['light', 'archive']:
#     with open(join(destn, 'dist', 'files', 'data.txt'), 'w') as f:
#         json.dump(highscores, f)

shutil.rmtree('build', ignore_errors=True)

shutil.make_archive(join('bin', '%sMineGauler%s'%(target, VERSION)),
    'zip', destn)


if target != 'light':
    with winshell.shortcut(
        join(winshell.desktop(), 'MineGauler.lnk')) as shortcut:
        shortcut.working_directory = join(os.getcwd(), destn, 'dist')
        shortcut.path = join(shortcut.working_directory, 'MineGauler.exe')
