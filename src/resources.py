"""Contains functions to be used by multiple scripts."""

import os
from os.path import join, dirname, isdir, basename
import time as tm

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

nr_colours = {
    1:  'blue',
    2:  '#%02x%02x%02x'%(  0,128,  0),
    3:  'red',
    4:  '#%02x%02x%02x'%(  0,  0,128),
    5:  '#%02x%02x%02x'%(128,  0,  0),
    6:  '#%02x%02x%02x'%(  0,128,128),
    7:  'black',
    8:  '#%02x%02x%02x'%(128,128,128),
    9:  '#%02x%02x%02x'%(192,192,  0),
    10: '#%02x%02x%02x'%(128,  0,128),
    11: '#%02x%02x%02x'%(192,128, 64),
    12: '#%02x%02x%02x'%( 64,192,192),
    13: '#%02x%02x%02x'%(192,128,192),
    14: '#%02x%02x%02x'%(128,192, 64),
    15: '#%02x%02x%02x'%(128, 64,192)
    }


def get_neighbours(coord, dims, dist=1, include=False):
    d = dist if dist % 1 == 0 else int(dist) + 1
    x, y = coord
    row = [u for u in range(x-d, x+1+d) if u in range(dims[0])]
    col = [v for v in range(y-d, y+1+d) if v in range(dims[1])]
    # Extra feature removed.
    if dist % 1 == 0:
        neighbours = {(u, v) for u in row for v in col}
    if not include:
        #The given coord is not included.
        neighbours.remove(coord)
    return neighbours

def where_coords(bool_array):
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
