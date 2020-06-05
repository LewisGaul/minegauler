from distutils.core import setup
import py2exe, sys, os
from os.path import join, isdir, dirname
from glob import glob
import shutil
import json
import winshell

import numpy # So that all '.dll's are found.

from main01 import encode_highscore, __name__ as name, __version__ as version


sys.argv.append('py2exe') # No need to type in command line.

desktop = winshell.desktop()
version_direc = dirname(os.getcwd())
dest_direc = join(version_direc, 'Package')
if isdir(dest_direc):
    shutil.rmtree(dest_direc, ignore_errors=True)
if not isdir(dest_direc):
    os.mkdir(dest_direc)
    os.mkdir(join(dest_direc, 'dist'))

py2exe_options = {
        'compressed': True,
        'optimize': 1, # 2 does not work.
        'dist_dir': join(dest_direc, 'dist'),
        'excludes': [
            'pydoc',
            'doctest',
            'pdb',
            'inspect',
            'pyreadline',
            'locale',
            'optparse',
            'pickle',
            'calendar'
            ]
        }

data_files = []
for folder in ['mines', 'flags']:
    data_files.append((join('images', folder),
        glob(join(dirname(version_direc), 'images', folder, '*.png'))))
data_files.append((join('images', 'faces'),
        glob(join(dirname(version_direc), 'images', 'faces', '*.ppm'))))
data_files.append(('files', map(lambda x: join(version_direc, 'files', x),
    ['features.txt', 'about.txt']))) # Include 'data.txt' for all highscores.
data_files.append((dest_direc, [join(version_direc, 'files', 'README.txt')]))

setup(
    windows=[{'dest_base': 'MineGauler',
              'script': '%s.pyw'%name
            }],
    options={'py2exe': py2exe_options},
    data_files=data_files,
    # zipfile=join(dest_direc, 'dist', 'lib.zip'),
    version=version,
    name='MineGauler'
    )

with open(join(version_direc, 'files', 'data.txt'), 'r') as f:
    all_data = [h for h in json.load(f) if h['proportion'] == 1 and
        h['name'] == 'Siwel G']
high_data = []
settings = []
all_data.sort(key=lambda x: float(x['time']))
for d in all_data:
    s = (d['name'], d['level'], d['lives'], d['per cell'], d['detection'],
        d['drag'], ['distance to'])
    if s not in settings:
        settings.append(s)
        high_data.append(d)
# for d in high_data:
#     all_data.remove(d)
# settings = []
# all_data.sort(key=lambda x: float(x['3bv/s']), reverse=True)
# for d in all_data:
#     s = (d['name'], d['level'], d['lives'], d['per cell'], d['detection'],
#         d['drag'], ['distance to'], bool(d['flagging']))
#     if s not in settings:
#         settings.append(s)
#         high_data.append(d)
with open(join(dest_direc, 'dist', 'files', 'data.txt'), 'w') as f:
    json.dump(high_data, f)

shutil.rmtree('build', ignore_errors=True)

shutil.make_archive(
    join(version_direc, 'MineGauler%s'%version), 'zip', dest_direc)

with winshell.shortcut(
    join(winshell.desktop(), 'MineGauler.lnk')) as shortcut:
    shortcut.working_directory = join(dest_direc, 'dist')
    shortcut.path = join(shortcut.working_directory, 'MineGauler.exe')