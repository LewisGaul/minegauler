"""Contains utilities to be used by multiple scripts."""

import os
from os.path import join, dirname, isdir, basename
import time as tm

import numpy as np

from constants import *


direcs = dict()
if IN_EXE:
    direcs['main'] = main_direc = os.getcwd()
    direcs['images'] = join(main_direc, 'images')
    direcs['data'] = file_direc = join(main_direc, 'files')
else:
    direcs['main'] = main_direc = dirname(os.getcwd())
    direcs['data'] = join(main_direc, 'data')
    # Image directory path depends on if we are in version currently under
    # development.
    if basename(main_direc) == 'minegauler':
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
    format='hex'):
    colour = []
    for i in range(3):
        c1, c2 = low_colour[i], high_colour[i]
        colour.append(int(c1 + ratio*(c2 - c1)))
    colour = tuple(colour)
    if format in ['rgb', 'RGB']:
        return colour
    elif format == 'hex':
        return '#%02x%02x%02x' % colour
