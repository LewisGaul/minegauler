"""Newer version available."""
#from minesweeper3 import *
#sys.exit()

"""
Contains class for minesweeper fields, which has a size attribute. The following
are equivalent: beginner/b/1/(8,8), intermediate/i/2/(16,16), expert/e/3/(16,30).
It has functions to create (manually using Tkinter or randomly) the grid of mines,
and to play the game (again using Tkinter). There are also options to have a
maximum number of mines per cell greater than 1 and to have the numbers display
the number of mines in cells adjacent by more than one cell. Function _3bv() finds
the 3bv of the grid.
New:
The use of Tkinter and general improvements."""

import numpy as np
import time as tm
from Tkinter import *

default_mines = {(8,8):10, (16,16):40, (16,30):99, (30,16):99}
colours = dict([(1,'blue'), (2,'#%02x%02x%02x'%(0,150,0)), (3,'red'),
                (4,'#%02x%02x%02x'%(0,0,120)), (5,'brown'),
                (6,'turquoise'), (7,'black'),
                (8,'#%02x%02x%02x'%(120,120,120)), (9,'#%02x%02x%02x'%(238,173,14)),
                (10,'#%02x%02x%02x'%(200,0,200)), (11,'#%02x%02x%02x'%(255,128,0))])
cellfont = ('Times', 9, 'bold')
minesymbols = ["F", "B", "C", "D", "E", "G", "H", "J", "K", "M"]

class Minefield(object):
    def __init__(self, shape=(16,30), mines_per_cell=1, detection=1):
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
        self.detection = detection

        self.mines_grid = np.zeros(1)
        self.mine_coords = []
        self.final_grid = np.zeros(1)

    def __str__(self):
        return ("The field has dimensions {} x {} with {n} mines and 3bv of {b}:\n".format(*self.shape, n=self.mines_grid.sum(), b=self._3bv())
                + self.pretty_grid(self.final_grid))

    def __repr__(self):
        return "<{}x{} grid with {n} mines>".format(*self.shape, n=len(self.mine_coords))

    def pretty_grid(self, array):
        replacements = [('-18','@'), ('-27','%'), ('-36','&'), ('-45','$'), ('-9','#'), ('\n  ',' '), ('0','.'), ('-1','='), ('-8','X'), ('   ',' '), ('  ',' '), ('[ ','[')]
        ret = str(array)
        for r in replacements:
            ret = ret.replace(*r)
        return ret

    def disp_zeros(self):
        print str(np.where(self.final_grid()==0, 0, 1)).replace('1', '.')

    def disp_grid(self, array, mines=False, containingframe=None):
        if mines:
            array *= -9
        replacements = dict([(-18,':'), (-27,'%'), (-36,'#'), (-45,'&'), (-54,'$'), (-9,'*'), (0,''), (-1,''), (-8,'X')])
        root = Tk() if not containingframe else containingframe
        frames = self.make_grid(root)
        cells = dict()
        for coord in sorted(list(frames)):
            text = replacements[array[coord]] if array[coord] in replacements else str(array[coord])
            colour = colours[array[coord]] if array[coord] in colours else 'black'
            b = Button(frames[coord], bd=2.4, text=text, font=cellfont, fg=colour)
            cells[coord] = b
            #Make the button fill the frame (stick to all sides).
            b.grid(sticky='NSEW')
            if array[coord] >= 0:
                b['relief'] = 'sunken'
                b['bd'] = 0.5
        if containingframe:
            return root, cells
        mainloop()

    def make_grid(self, rootframe):
        frames = dict()
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                coord = (i, j)
                f = Frame(rootframe, width=16, height=16)
                frames[coord] = f
                f.rowconfigure(0, weight=1) #enables button to fill frame...
                f.columnconfigure(0, weight=1) 
                f.grid_propagate(False) #disables resizing of frame
                f.grid(row=i+1, column=j)
        return frames
        
    def create(self, mines='default', overwrite=False, prop=0.21):
        if not overwrite and self.mines_grid.size != 1:
            return "Grid already created and overwrite is set to False."
        if mines == 'default' and self.shape in default_mines:
            mines = default_mines[self.shape]
        elif mines not in range(1, self.size):
            mines = int(round(float(self.size)*prop, 0))
            
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
        self.get_final_grid()

    def manual_create(self, mines='default', overwrite=False, prop=0.21):
        if not self.mines_grid.any() or overwrite:
            self.mines_grid = np.zeros(self.shape, int)
        if mines == 'default':
            if self.shape in default_mines:
                mines = default_mines[self.shape]
            else:
                mines = int(round(self.size*prop, 0))

        grid = -np.ones(self.shape, int)
        
        def quitfunc():
            self.mines_grid = np.zeros(1)
            root.destroy()
        
        def clearfunc():
            self.mines_grid *= 0
            grid = -np.ones(self.shape, int)
            for b in buttons.values():
                reset_button(b)
                buttonnums[b].set("")
                minesnum.set("000")

        def leftclick(coord):
            def action():
                b = buttons[coord]
                #Should work on the mine the mouse ends over.
                if grid[coord] >= -1:
                    b['relief'] = 'sunken'
                    b['bd'] = 0.5
                    grid[coord] += 1
                    if grid[coord] > 0:
                        buttonnums[b].set(str(grid[coord]))
                        try:
                            b['fg'] = colours[grid[coord]]
                        except KeyError:
                            b['fg'] = 'black'
            return action

        def rightclick(coord):
            def action(event):
                b = buttons[coord]
                #Needs to only be implemented if mouse not moved away.
                if grid[coord] == -1:
                    buttonnums[b].set("F")
                    self.mines_grid[coord] = 1
                    grid[coord] = -9
                else:
                    buttonnums[b].set("")
                    self.mines_grid[coord] = 0
                    grid[coord] = -1
                minesnum.set("%03d" % self.mines_grid.sum())
            return action

        topfont = ('Times', 10, 'bold')
        root = Tk()
        root.title("MineGauler")
        topframe = Frame(root)
        topframe.pack(side='top', pady=2)
        Button(topframe, bd=4, text="Done", font=topfont, command=root.destroy).grid(row=0, column=1, padx=5)
        Button(topframe, bd=4, text="Clear", font=topfont, command=clearfunc).grid(row=0, column=2, padx=5)
        Button(topframe, bd=4, text="Quit", font=topfont, command=quitfunc).grid(row=0, column=3, padx=5)
        minesnum = StringVar()
        minesnum.set("000")
        Label(topframe, bd=1, fg='red', bg='black', textvariable=minesnum, font=('Verdana', 12, 'bold'), padx=6).grid(row=0, column=0)

        mainframe = Frame(root)
        mainframe.pack(side='top')
        frames = self.make_grid(mainframe)
        buttons = dict()
        buttonnums = dict()
        for coord in sorted(list(frames)):
            bnum = StringVar()
            b = Button(frames[coord], bd=2.4, takefocus=0, textvariable=bnum, font=cellfont, command=leftclick(coord))
            buttons[coord] = b
            #Make the button fill the frame (stick to all sides).
            b.grid(sticky='NSEW')
            #Add the action when right click occurs.
            b.bind('<ButtonRelease-3>', rightclick(coord))
            #Store the bnum variable in a dictionary with the button instance as the key.
            buttonnums[b] = bnum

        mainloop()
        
        self.mine_coords = map(tuple, np.transpose(np.nonzero(self.mines_grid>0)))
        self.get_final_grid()
        print self
        self.disp_grid(self.final_grid)
        
    def get_final_grid(self):
        if self.mines_grid.size == 1:
            return
        self.final_grid = -9 * self.mines_grid
        for coord in np.transpose(np.nonzero(-(self.mines_grid>0))):
            entry = 0
            for k in self.neighbours(tuple(coord), self.detection):
                if self.mines_grid[k] > 0:
                    entry += self.mines_grid[k]
            self.final_grid[tuple(coord)] = entry
        return self.final_grid
    
    def neighbours(self, coord, distance=1):
        i, j = coord
        x, y = self.shape
        #Create array of neighbouring coordinates.
        row = range(max(0,i-distance), min(x,i+1+distance))
        col = range(max(0,j-distance), min(y,j+1+distance))
        neighbours = set()
        for u in row:
            for v in col:
                neighbours.add((u, v))
        #The given coord is not included.
        neighbours.remove(coord)
        return neighbours

    def find_zero_patches(self):
        zero_coords = set(map(tuple, np.transpose(np.nonzero(self.final_grid==0))))
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
                cur_patch.update(self.neighbours(coord, self.detection))
                check.update(self.neighbours(coord).intersection(
                    zero_coords.difference(found_coords)))
            patches.append(cur_patch)
        self.zero_patches = patches
        return patches
        
    def _3bv(self):
        clicks = len(self.find_zero_patches())
        exposed = set(self.zero_coords)
        for c in self.zero_coords:
            exposed.update(self.neighbours(c))
        clicks += self.size - len(self.mine_coords) - len(exposed)
        return clicks

    def play(self, mines='default'):
        if self.mines_grid.size == 1:
            self.create(mines)

        self.find_zero_patches()
        
        grid = -np.ones(self.shape, int)

        def replay():
            root.destroy()
            self.play()
        def new():
            self.create(self.mines_grid.sum(), overwrite=1)
            replay()
        
        root = Tk()
        root.title('MineGauler0.0.2')
        topframe = Frame(root, pady=5)
        topframe.pack()
        minesleft = StringVar()
        minesleft.set("%03d" % self.mines_grid.sum())
        Label(topframe, padx=10, bg='black', fg='red', font=('Verdana',12,'bold'), textvariable=minesleft).grid(row=0, rowspan=2, column=0)
        f1 = Frame(topframe, padx=5, width=30, height=15)
        f1.grid(row=0, column=1)
        f1.grid_propagate(False)
        f1.rowconfigure(0, weight=1)
        f1.columnconfigure(0, weight=1)
        f2 = Frame(topframe, padx=5, width=30, height=15)
        f2.grid(row=1, column=1)
        f2.grid_propagate(False)
        f2.rowconfigure(0, weight=1)
        f2.columnconfigure(0, weight=1)
        Button(f1, text='r', command=replay).grid(sticky='nsew')
        Button(f2, text='n', command=new).grid(sticky='nsew')
        timeelapsed = StringVar()
        timeelapsed.set("000")
        Label(topframe, padx= 10, bg='black', fg='red', font=('Verdana',12,'bold'), textvariable=timeelapsed).grid(row=0, rowspan=2, column=2)

        def leftclick(coord):
            def action():
                if timeelapsed.get() == "000":
                    pass
                b = buttons[coord]
                #Should work on the mine the mouse ends over.
                if grid[coord] == -1:
                    if self.final_grid[coord] == 0:
                        for patch in self.zero_patches:
                            if coord in patch:
                                for c in patch:
                                    if grid[c] == -1:
                                        buttons[c]['relief'] = 'sunken'
                                        buttons[c]['bd'] = 0.5
                                        grid[c] = self.final_grid[c]
                                        if self.final_grid[c] > 0:
                                            buttonnums[buttons[c]].set(str(grid[c]))
                                            try:
                                                buttons[c]['fg'] = colours[grid[c]]
                                            except KeyError:
                                                buttons[c]['fg'] = 'black'
                                break
                    elif self.final_grid[coord] > 0:
                        b['relief'] = 'sunken'
                        b['bd'] = 0.5
                        grid[coord] = self.final_grid[coord]
                        buttonnums[b].set(str(grid[coord]))
                        try:
                            b['fg'] = colours[grid[coord]]
                        except KeyError:
                            b['fg'] = 'black'
                    else:
                        mainframe.destroy()
                        print "You lose!"
                        timeelapsed.set("%03.0f" % (tm.time() - start))
                        newmainframe, cells = self.disp_grid(self.final_grid, containingframe=Frame(root))
                        newmainframe.pack()
                        for c in cells:
                            if self.final_grid[c] < 0 or grid[c] < -1:
                                if self.final_grid[c] == grid[c]:
                                    cells[c]['text'] = minesymbols[-grid[c]/9 - 1]
                                elif grid[c] < -1:
                                    cells[c]['text'] = "X"
                                    reset_button(cells[c])
                            elif grid[c] == -1:
                                reset_button(cells[c])
                                cells[c]['text'] = ""
                        cells[coord]['text'] = 'O'
                    if (np.where(grid < 0, -9, grid) == np.where(self.final_grid < 0, -9, self.final_grid)).all():
                        print "You win!", self
                        timeelapsed.set("%03.0f" % (tm.time() - start))
                        mainframe.destroy()
                        newmainframe, cells = self.disp_grid(self.final_grid, containingframe=Frame(root))
                        newmainframe.pack()
                        for c in cells:
                            if self.final_grid[c] < 0:
                                cells[c]['text'] = minesymbols[-self.final_grid[c]/9 - 1]
            return action
        def rightclick(coord):
            def action(event):
                b = buttons[coord]
                #Needs to only be implemented if mouse not moved away.
                if grid[coord] == -1:
                    buttonnums[b].set("F")
                    grid[coord] = -9
                elif grid[coord] < -1:
                    if grid[coord] > -9*self.mines_per_cell:
                        buttonnums[b].set(minesymbols[-grid[coord]/9])
                        grid[coord] -= 9
                    else:
                        buttonnums[b].set("")
                        grid[coord] = -1
                minesleft.set("%03d" % (self.mines_grid.sum()
                                    + np.where(grid<-1, grid, 0).sum()/9))
            return action
        
        mainframe = Frame(root)
        mainframe.pack()
        frames = self.make_grid(mainframe)
        buttons = dict()
        buttonnums = dict()
        for coord in sorted(list(frames)):
            num = StringVar()
            b = Button(frames[coord], bd=2.4, textvariable=num, font=cellfont, command=leftclick(coord))
            buttonnums[b] = num
            buttons[coord] = b
            b.grid(sticky='nsew')
            b.bind('<ButtonRelease-3>', rightclick(coord))

        start = tm.time()
        mainloop()
        return


def reset_button(button):
    button['relief'] = 'raised'
    button['fg'] = 'black'
    button['bd'] = 2.4


if __name__ == '__main__':
    B = Minefield('b')
    B.create()
    I = Minefield('i')
    I.create()
    E = Minefield('e')
    E.create()
    I.play()


#My record of 68.7 seconds (142 3bv). Mine coordinates are below.
example = [(0, 0), (0, 11), (0, 12), (0, 14), (1, 3), (2, 3), (2, 4), (2, 8), (3, 2), (3, 3), (3, 5), (3, 15), (4, 5), (4, 7), (4, 9), (4, 11), (5, 2), (5, 6), (6, 10), (7, 8), (8, 3), (8, 10), (9, 2), (9, 12), (10, 4), (10, 7), (10, 13), (11, 2), (11, 4), (11, 7), (11, 8), (11, 9), (11, 13), (12, 9), (13, 3), (13, 7), (13, 10), (13, 15), (14, 3), (15, 7), (15, 10), (16, 0), (16, 2), (16, 9), (16, 11), (16, 13), (17, 0), (17, 7), (17, 9), (18, 1), (18, 5), (18, 9), (18, 10), (18, 13), (19, 10), (19, 15), (20, 3), (20, 6), (20, 7), (20, 15), (21, 3), (21, 5), (22, 2), (22, 6), (22, 8), (22, 12), (22, 13), (22, 14), (22, 15), (23, 0), (23, 1), (23, 8), (23, 9), (23, 12), (23, 14), (24, 3), (24, 4), (24, 10), (24, 11), (25, 0), (25, 1), (25, 3), (25, 7), (26, 8), (26, 9), (26, 11), (26, 12), (27, 9), (27, 14), (27, 15), (28, 8), (28, 9), (28, 10), (28, 11), (28, 14), (29, 6), (29, 7), (29, 10), (29, 14)]
