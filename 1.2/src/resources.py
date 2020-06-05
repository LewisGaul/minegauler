"""Contains functions and constants to be used by multiple scripts."""

from distutils.version import LooseVersion
import sys
import os
from os.path import join, dirname, exists, split, splitext, getsize, isdir
import time as tm
import json
from glob import glob

import numpy as np

version = '1.2.0'
platform = sys.platform
BIG = 1000

if hasattr(sys, 'frozen'): # In exe
    main_direc = os.getcwd()
    im_direc = join(main_direc, 'images')
    data_direc = file_direc = join(main_direc, 'files')
else: # In py
    main_direc = dirname(os.getcwd()) #Up a level
    im_direc = join(dirname(main_direc), 'images')
    file_direc = join(main_direc, 'files')
    data_direc = join(main_direc, 'data')
boards_direc = join(main_direc, 'boards')
if not isdir(boards_direc):
    os.mkdir(boards_direc)

nr_colours = dict([(1,'blue'                        ),
                   (2, '#%02x%02x%02x'%(  0,128,  0)),
                   (3, 'red'                        ),
                   (4, '#%02x%02x%02x'%(  0,  0,128)),
                   (5, '#%02x%02x%02x'%(128,  0,  0)),
                   (6, '#%02x%02x%02x'%(  0,128,128)),
                   (7, 'black'                      ),
                   (8, '#%02x%02x%02x'%(128,128,128)),
                   (9, '#%02x%02x%02x'%(192,192,  0)),
                   (10,'#%02x%02x%02x'%(128,  0,128)),
                   (11,'#%02x%02x%02x'%(192,128, 64)),
                   (12,'#%02x%02x%02x'%( 64,192,192)),
                   (13,'#%02x%02x%02x'%(192,128,192)),
                   (14,'#%02x%02x%02x'%(128,192, 64)),
                   (15,'#%02x%02x%02x'%(128, 64,192))])

encode_highscore = lambda h: int(
    (sum([c[0]*c[1]**2 for c in h['coords']]) if h.has_key('coords') else 0) +
    13*h['date']/float(h['time']) + 100*float(h['3bv/s']) + 16*h['3bv'] -
    reduce(lambda x, y: 3*x + 7*ord(y), h['name'], 0) + 3*h['lives'] +
    50*h['detection'] + 7*h['per_cell'] + 19*int(h['drag_select']) +
    12*int(h['distance_to']))

def get_nonzero_coords(grid):
    coords_array = np.transpose(np.nonzero(grid))
    coords_list = []
    for coord in coords_array.tolist():
        coords_list.append(tuple(map(int, coord)))
    return coords_list

def get_highscores(data, num=5, name=None):
    data = [h for h in data if h['name']]
    if name:
        data = [h for h in data if h['name'] == name]
    high_data = []
    settings = []
    data.sort(key=lambda x: float(x['time']))
    for d in data:
        s = (d['name'], d['diff'], d['lives'], d['per_cell'], d['detection'],
            d['drag_select'], ['distance_to'], bool(d['flagging']))
        if settings.count(s) < num:
            settings.append(s)
            high_data.append(d)
    settings = []
    data.sort(key=lambda x: float(x['3bv/s']), reverse=True)
    for d in data:
        s = (d['name'], d['diff'], d['lives'], d['per_cell'], d['detection'],
            d['drag_select'], ['distance_to'], bool(d['flagging']))
        if settings.count(s) < num:
            settings.append(s)
            if d not in high_data:
                high_data.append(d)
    return high_data

def get_neighbours(coord, dims, dist=1, include=False):
    d = dist if dist % 1 == 0 else int(dist) + 1
    x, y = coord
    row = [u for u in range(x-d, x+1+d) if u in range(dims[0])]
    col = [v for v in range(y-d, y+1+d) if v in range(dims[1])]
    if dist % 1 == 0:
        neighbours = {(u, v) for u in row for v in col}
    elif dist % 1 < 0.5:
        neighbours = {(u, v) for u in row for v in col
                      if abs(u-x) + abs(v-y) <= d}
    elif dist % 1 == 0.5:
        neighbours = {(u, v) for u in row for v in col
                      if abs(u-x) + abs(v-y) <= 2**(d-1)}
    else: #x.5 < dist < y.0
        neighbours = {(u, v) for u in row for v in col
                      if abs(u-x) + abs(v-y) < 2*d}
    if not include:
        #The given coord is not included.
        neighbours.remove(coord)
    return neighbours

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
