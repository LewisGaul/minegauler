"""Contains utilities to be used by multiple scripts."""

import os
from os.path import join, dirname, isdir, basename, realpath
import time as tm

import numpy as np

from constants import *


direcs = dict()
if IN_EXE:
    direcs['main'] = main_direc = os.getcwd()
    direcs['images'] = join(main_direc, 'images')
    direcs['data'] = file_direc = join(main_direc, 'files')
else:
    direcs['main'] = main_direc = dirname(dirname(realpath(__file__)))
    direcs['data'] = join(main_direc, 'data')
    # Image directory path depends on if we are in version currently under
    # development.
    if basename(main_direc) == 'minegauler' or True:
        direcs['images'] = join(main_direc, 'images')
    else:
        direcs['images'] = join(dirname(main_direc), 'images')
direcs['files'] = join(main_direc, 'files')
direcs['boards'] = join(main_direc, 'boards')
if not isdir(direcs['boards']):
    os.mkdir(direcs['boards'])

def get_nbrs(coord, dims, include=False):
    # Also belongs in classes...
    x, y = coord
    row = [u for u in range(x-1, x+2) if u in range(dims[0])]
    col = [v for v in range(y-1, y+2) if v in range(dims[1])]
    nbrs = {(u, v) for u in row for v in col}
    if not include:
        #The given coord is not included.
        nbrs.remove(coord)
    return nbrs

def where_coords(bool_array):
    # Attach to minefield class?
    coords_array = np.transpose(np.nonzero(bool_array))
    coords_list = []
    for coord in coords_array.tolist():
        coords_list.append(tuple(map(int, coord)))
    return coords_list

def blend_colours(ratio, high_colour=(255, 0, 0), low_colour=(255, 255, 64),
    fmt='hex'):
    colour = []
    for i in range(3):
        c1, c2 = low_colour[i], high_colour[i]
        colour.append(int(c1 + ratio*(c2 - c1)))
    colour = tuple(colour)
    if fmt.lower() == 'rgb':
        return colour
    elif fmt == 'hex':
        return '#%02x%02x%02x' % colour

enchs = lambda h, k: int(
    130*h['date']/float(h['time']) % 100000 +
    100*float(h['3bv/s']) - 16*h['3bv'] +
    reduce(lambda x, y: 3*x + 7*ord(y), h['name'], 0) +
    reduce(lambda x, y: x + 4*ord(y), k, 0)
    )
