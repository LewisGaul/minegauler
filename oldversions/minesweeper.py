"""Newer version available."""
##from minesweeper2 import *
##sys.exit()

"""
Contains class for minesweeper fields, which has a size attribute. The following
are equivalent: beginner/b/1/(8,8), intermediate/i/2/(16,16), expert/e/3/(16,30).
It has functions to create (manually and randomly) the grid of mines, and to
play the game by entering coordinates in the shell.
"""

import re
import time as tm

import numpy as np


default_mines = {(8,8):10, (16,16):40, (16,30):99, (30,16):99}


class Minefield(object):
    def __init__(self, shape=(16,30), mines_per_cell=1):
        if type(shape) is str:
            shape = shape.lower()
        if shape in ['b', 'beginner', 1]:
            self.shape = (8, 8)
        elif shape in ['i', 'intermediate', 2]:
            self.shape = (16, 16)
        elif shape in ['e', 'expert', 3]:
            self.shape = (16, 30)
        elif type(shape) is tuple and len(shape) == 2:
            self.shape = shape
        else:
            print "Invalid size, enter 2-tuple integers."
        self.size = self.shape[0]*self.shape[1]
        self.mines_per_cell = mines_per_cell

        self.mines_grid = np.zeros(self.shape, int)
        self.mine_coords = []

    def __str__(self):
        return ("The field has dimensions {} x {} with {n} mines:\n".format(*self.shape, n=len(self.mine_coords))
                + self.disp_grid(self.final_grid()))

    def __repr__(self):
        return "<{}x{} grid with {n} mines>".format(*self.shape, n=len(self.mine_coords))

    def disp_grid(self, array):
        replacements = [('-18', '@'), ('-27', '&'), ('-36', '*'), ('-9', '#'), ('\n  ', ' '), ('0', '.'), ('-1', '='), ('-8', 'X'), ('   ', ' '), ('  ', ' '), ('[ ', '[')]
        ret = str(array)
        for r in replacements:
            ret = ret.replace(*r)
        return ret

    def disp_zeros(self):
        print str(np.where(self.final_grid()==0, 0, 1)).replace('1', '.')

    def data(self):
        return str(self) + "\nIt has 3bv of {}.".format(self._3bv())
        
    def create(self, mines='default', proportion=4.5, overwrite=False):
        if not overwrite and self.mines_grid.any():
            return "Grid already contains mines and overwrite is set to False."
        if mines == 'default' and self.shape in default_mines:
            mines = default_mines[self.shape]
        elif mines not in range(1, self.size):
            mines = int(round(float(self.size)/proportion, 0))
            
        if self.mines_per_cell == 1:
            perm = np.ones(mines, int)
            perm.resize(self.size)
            self.mines_grid = np.random.permutation(perm).reshape(self.shape)
        else:
            self.mines_grid = np.zeros(self.shape, int)
            while self.mines_grid.sum() < mines:
                cell = np.random.randint(self.size)
                old_val = self.mines_grid.item(cell)
                if old_val < self.mines_per_cell:
                    self.mines_grid.itemset(cell, old_val + 1)
        
        self.mine_coords = map(tuple, np.transpose(np.nonzero(self.mines_grid>0)))

    def manual_create(self, mines='default', proportion=4.8, overwrite=False):
        if not self.mines_grid.any() or overwrite:
            self.mines_grid = np.zeros(self.shape, int)
        if mines == 'default':
            if self.shape in default_mines:
                mines = default_mines[self.shape]
            else:
                mines = int(round(self.size/proportion, 0))
        print ("Give coordinates of the mines in the format 'x, y', with 0<x<{}, "
               "0<y<{}.".format(*map(lambda x:x+1, self.shape)))
        while mines > self.mines_grid.sum():
            raw_coord = raw_input()
            first_char = raw_coord[0]
            coord = tuple(map(lambda x:int(x)-1, re.findall('\d+', raw_coord)))
            if len(coord) == 2 and self.mines_per_cell > self.mines_grid[coord] and (np.array(coord) < np.array(self.shape)).all() and (np.array(coord) >= 0).all():
                if first_char == '^':
                    self.mines_grid[coord] = max(0, self.mines_grid[coord] - 1)
                else:
                    self.mines_grid[coord] = self.mines_grid[coord] + 1
            else:
                print "Invalid entry."
                break
        self.mine_coords = map(tuple, np.transpose(np.nonzero(self.mines_grid>0)))
        
    def final_grid(self):
        final_grid = -9 * self.mines_grid
        for coord in np.transpose(np.nonzero(~(self.mines_grid>0))):
            entry = 0
            for k in self.neighbours(tuple(coord)):
                if self.mines_grid[k] > 0:
                    entry += self.mines_grid[k]
            final_grid[tuple(coord)] = entry
        return final_grid
    
    def neighbours(self, coord):
        i, j = coord
        x, y = self.shape
        square = np.concatenate(
            (np.array([[max(0,i-1)],[i],[min(x-1,i+1)]]).repeat(3, axis=0),
             np.array([[max(0,j-1),j,min(y-1,j+1)]]).repeat(3, axis=0).reshape(9, 1)), axis=1)
        neighbours = set(map(tuple, square.tolist()))
        neighbours.remove(coord)
        return neighbours

    def find_zero_patches(self):
        zero_coords = set(map(tuple, np.transpose(np.nonzero(self.final_grid()==0))))
        self.zero_coords = sorted(list(zero_coords))
        check = set()
        found_coords = set()
        patches = []
        while len(zero_coords.difference(found_coords)) > 0:
            cur_patch = set()
            check.add(list(zero_coords.difference(found_coords))[0])
            while len(check) > 0:
                found_coords.update(check)
                coord = check.pop()
                cur_patch.add(coord)
                cur_patch.update(self.neighbours(coord))
                check.update(self.neighbours(coord).intersection(
                    zero_coords.difference(found_coords)))
            patches.append(cur_patch)
        return patches
        
    def _3bv(self):
        clicks = len(self.find_zero_patches())
        exposed = set(self.zero_coords)
        for c in self.zero_coords:
            exposed.update(self.neighbours(c))
        clicks += self.size - len(self.mine_coords) - len(exposed)
        return clicks

    def play(self):
        grid = -np.ones(self.shape, int)
        print self.mines_grid.sum(), "mines to find."
        start = tm.time()
        while True:
            print self.disp_grid(grid)
            raw_coord = raw_input()
            first_char = raw_coord[0]
            coord = tuple(map(lambda x:int(x)-1, re.findall('\d+', raw_coord)))
            if (np.array(coord) >= np.array(self.shape)).all() and (np.array(coord) < 0).all():
                print "Invalid coordinate."
            elif len(coord) == 2:
                if first_char == '^':
                    if grid[coord] == -1:
                        grid[coord] -= 8
                    elif grid[coord] < -1:
                        if grid[coord] > -9*self.mines_per_cell:
                            grid[coord] -= 9
                        else:
                            grid[coord] = -1
                elif grid[coord] == -1:
                    if self.final_grid()[coord] < 0:
                        print "You lose!\n" + self.disp_grid(np.where(self.mines_grid > 0, -9*self.mines_grid, np.where((np.mod(grid, 9) == 0) * (grid != 0) * (self.mines_grid != 1), -8, grid)))
                        break
                    elif self.final_grid()[coord] == 0:
                        for patch in self.find_zero_patches():
                            if coord in patch:
                                for c in patch:
                                    grid[c] = self.final_grid()[c]
                                break
                    else:
                        grid[coord] = self.final_grid()[coord]
            if (np.where(grid < 0, -9, grid) == np.where(self.final_grid() < 0, -9, self.final_grid())).all():
                print "\n" + self.disp_grid(self.final_grid())
                print "You won in {:.2f} seconds!".format(tm.time() - start)
                break
        
            
if __name__ == '__main__':
    B = Minefield('b')
    B.create()
    B.play()
    I = Minefield('i')
    I.create()
    E = Minefield('e')
    E.create()
    
