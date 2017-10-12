
import sys


__version__ = '2.0'
IN_EXE = hasattr(sys, 'frozen')
if IN_EXE:
    img_direc = r'images/'
else:
    img_direc = r'../images/'

diff_settings = {
    'b': ( 8,  8,  10),
    'i': (16, 16,  40),
    'e': (30, 16,  99),
    'm': (30, 30, 200),
    'c': None
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
