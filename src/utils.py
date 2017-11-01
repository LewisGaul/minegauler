
import sys
from os.path import join, dirname, abspath


__version__ = '2.0.1'
IN_EXE = hasattr(sys, 'frozen')
src_direc = dirname(abspath(__file__))
if IN_EXE:
    base_direc = src_direc
else:
    base_direc = dirname(src_direc)
img_direc = join(base_direc, 'images')
file_direc = join(base_direc, 'files')

diff_values = {
    'b': ( 8,  8,  10),
    'i': (16, 16,  40),
    'e': (30, 16,  99),
    'm': (30, 30, 200),
    'c': None
}
default_settings = {
    'x_size': 8,
    'y_size': 8,
    'nr_mines': 10,
    'diff': 'b',
    'first_success': True,
    'per_cell': 1,
    # 'radius': 1,    # Implement later
    'drag_select': False,
    'btn_size': 16, #pixels
    'name': '',
    'styles': {
        'buttons': 'Standard',
        'numbers': 'Standard',
        'markers': 'Standard'
        }
}

def prettify_grid(grid, repr_map=dict(), cell_size=1):
    ret = ''
    for row in grid:
        for i in row:
            cell = '{:>%d}' % cell_size
            ret += cell.format(
                repr_map[i] if i in repr_map else str(i)[:cell_size])
            ret += ' '
        ret = ret[:-1] # Remove trailing space
        ret += '\n'
    ret = ret[:-1] # Remove trailing newline
    return ret

def get_nbrs(x, y, x_size, y_size):
    nbrs = []
    for i in range(max(0,x-1), min(x_size,x+2)):
        for j in range(max(0,y-1), min(y_size,y+2)):
            nbrs.append((i, j))
    return nbrs

def calc_3bvps(h):
    # Round up to 2 d.p. (converting time to seconds)
    return (1e5 * h['3bv'] // h['time']) / 100 + 0.01
