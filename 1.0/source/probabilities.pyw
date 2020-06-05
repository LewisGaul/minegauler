from Tkinter import *
import os.path

import numpy as np
fac = np.math.factorial

from game import get_neighbours

BIG = 1000

#Button state
INACTIVE = -1
NEUTRAL = 0
ACTIVE = 1

version_direc = os.path.dirname(os.getcwd()) #Up a level
root_direc = os.path.dirname(version_direc)

nr_colours = dict([(1,'blue'                        ),
                   (2, '#%02x%02x%02x'%(  0,128,  0)),
                   (3, 'red'                        ),
                   (4, '#%02x%02x%02x'%(  0,  0,128)),
                   (5, '#%02x%02x%02x'%(128,  0,  0)),
                   (6, '#%02x%02x%02x'%(  0,128,128)),
                   (7, 'black'                      ),
                   (8, '#%02x%02x%02x'%(128,128,128))])

grid = np.array([[0, 0, 0, 0],
                 [0, 1, 2, 0],
                 [0, 0, 0, 0]])

class Gui(object):
    def __init__(self, dims=(5, 5), button_size=20):
        self.dims = dims
        self.button_size = button_size
        self.root = Tk()
        self.root.title('Create configuration')
        self.root.resizable(False, False) #Turn off option of resizing window
        self.nr_font = ('Tahoma', 10*self.button_size/17, 'bold')
        self.grid = -BIG*np.ones(self.dims, int)
        self.left_button_down, self.right_button_down = False, False
        self.mouse_down_coord, self.drag_X = None, None
        self.combined_click = False
        self.make_menubar()
        self.make_panel()
        self.make_minefield()
        self.configs = []
        mainloop()

    def __repr__(self):
        return "<Gui framework>".format()

    def make_menubar(self):
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.root.option_add('*tearOff', False)
        window_menu = Menu(self.menubar)
        self.menubar.add_cascade(label='Window', menu=window_menu)
        window_menu.add_command(label='Size', command=self.set_size)
        self.zoom_var = BooleanVar()
        window_menu.add_checkbutton(label='Zoom', variable=self.zoom_var,
            command=self.set_zoom)
        help_menu = Menu(self.menubar)
        self.menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='About',
            command=lambda: os.startfile(os.path.join(
                version_direc, 'about.txt')))

    def make_panel(self):
        self.panel = Frame(self.root, pady=4, height=40)
        self.panel.pack(fill=BOTH)
        self.face_image = PhotoImage(name='face',
            file=os.path.join(root_direc, 'images', 'faces', 'ready1face.ppm'))
        face_frame = Frame(self.panel)
        face_frame.place(x=10, rely=0.5, anchor=W)
        self.face_button = Button(face_frame, bd=4, image=self.face_image, takefocus=False, command=self.new)
        self.face_button.pack()
        self.done_button = Button(self.panel, bd=4, text="Done",
            font=('Times', 10, 'bold'), command=self.get_probs)
        self.done_button.place(relx=1, x=-10, rely=0.5, anchor=E)

    def make_minefield(self):
        self.mainframe = Frame(self.root, bd=10, relief='ridge')
        self.button_frames = dict()
        self.buttons = dict()
        for coord in [(u, v) for u in range(self.dims[0])
            for v in range(self.dims[1])]:
            self.make_button(coord)
        self.mainframe.pack()

    def make_button(self, coord):
        self.button_frames[coord] = f = Frame(self.mainframe,
            width=self.button_size, height=self.button_size)
        f.rowconfigure(0, weight=1) #enables button to fill frame...
        f.columnconfigure(0, weight=1)
        f.grid_propagate(False) #disables resizing of frame
        f.grid(row=coord[0], column=coord[1])
        self.buttons[coord] = b = Label(f, bd=3, relief='raised',
            font=self.nr_font)
        b.grid(sticky='nsew')
        b.coord = coord
        b.state = NEUTRAL
        b.bind('<Button-1>', self.left_press)
        b.bind('<ButtonRelease-1>', self.left_release)
        b.bind('<Button-3>', self.right_press)
        b.bind('<ButtonRelease-3>', self.right_release)
        b.bind('<B1-Motion>', self.motion)
        b.bind('<B3-Motion>', self.motion)

    def left_press(self, event=None, coord=None):
        if event:
            b = event.widget
        else:
            b = self.buttons[coord]
        self.left_button_down = True
        if self.right_button_down:
            self.both_press()
        else:
            self.mouse_down_coord = b.coord
            if b.state == NEUTRAL:
                b.config(bd=1, relief='sunken')

    def left_release(self, event=None):
        self.left_button_down = False
        if self.mouse_down_coord == None:
            return
        b = self.buttons[self.mouse_down_coord]
        if not self.right_button_down:
            self.mouse_down_coord = None
            if (not self.combined_click and self.grid[b.coord] < 8 and
                b.state != INACTIVE):
                b.state = ACTIVE
                self.grid[b.coord] = max(1, self.grid[b.coord] + 1)
                nr = self.grid.item(b.coord)
                b.config(text=nr, fg=nr_colours[nr], font=self.nr_font)
            self.combined_click = False
        if not b['text'] and b['relief'] == 'sunken':
            b.config(relief='raised', bd=3)

    def right_press(self, event=None, coord=None):
        if event:
            b = event.widget
        else:
            b = self.buttons[coord]
        self.right_button_down = True
        if self.left_button_down:
            self.both_press()
        else:
            self.mouse_down_coord = b.coord
            if b.state == NEUTRAL and self.drag_X != False:
                self.drag_X = True
                b.config(text='X', fg='black')
                b.state = INACTIVE
                self.grid[b.coord] = -1
            elif b.state == INACTIVE and self.drag_X != True:
                self.drag_X = False
                b.state = NEUTRAL
                b.config(bd=3, relief='raised', text='')
                self.grid[b.coord]
            elif b.state == ACTIVE:
                self.drag_X = None
                b.state = NEUTRAL
                b.config(bd=3, relief='raised', text='')
                self.grid[b.coord] = -BIG

    def right_release(self, event=None):
        self.right_button_down = False
        self.drag_X = None
        if not self.left_button_down:
            self.mouse_down_coord = None
            self.combined_click = False

    def both_press(self):
        self.combined_click = True

    def motion(self, event):
        clicked_coord = event.widget.coord
        cur_coord = (clicked_coord[0] + event.y/self.button_size, clicked_coord[1] + event.x/self.button_size)
        if (cur_coord in
            [(u, v) for u in range(self.dims[0])
                for v in range(self.dims[1])] and
            cur_coord != self.mouse_down_coord):
            if self.left_button_down and not self.right_button_down: #left
                if self.mouse_down_coord:
                    old_button = self.buttons[self.mouse_down_coord]
                    new_button = self.buttons[cur_coord]
                    if old_button.state == NEUTRAL:
                        old_button.config(bd=3, relief='raised')
                self.left_press(coord=cur_coord)
            elif self.right_button_down and not self.left_button_down: #right
                if (self.buttons[cur_coord].state != ACTIVE and
                    self.drag_X != None):
                    self.right_press(coord=cur_coord)
            elif self.left_button_down and self.right_button_down: #both
                if not self.mouse_down_coord:
                    self.mouse_down_coord = cur_coord
                    self.both_press()
                    return
                self.mouse_down_coord = cur_coord

        elif cur_coord != self.mouse_down_coord and self.mouse_down_coord:
            if self.left_button_down and not self.right_button_down: #left
                button = self.buttons[self.mouse_down_coord]
                if button.state == NEUTRAL:
                    button.config(bd=3, relief='raised')
            elif self.left_button_down and self.right_button_down: #both
                pass
            self.mouse_down_coord = None


    def get_probs(self):
        cfg = NrConfig(self.grid)
        self.configs.append(cfg)
        # cfg.print_info()
        # self.new()
        for coord in [c for c in cfg.all_coords if cfg.probs.item(c) != 0]:
            self.buttons[coord].config(bd=2, fg='black',
                font=('Times', 8, 'normal'),
                text=int(100*round(cfg.probs.item(coord), 2)))

    def new(self, event=None):
        for button in self.buttons.values():
            button.config(bd=3, relief='raised', fg='black',
                font=self.nr_font, text='')
            button.state = NEUTRAL
        self.grid = -BIG*np.ones(self.dims, int)

    def set_size(self):
        def reshape(event):
            prev_dims = self.dims
            self.dims = rows.get(), cols.get()
            self.grid.resize(self.dims)
            # This runs if one of the dimensions was previously larger.
            for coord in [(u, v) for u in range(prev_dims[0])
                for v in range(prev_dims[1]) if u >= self.dims[0] or
                    v >= self.dims[1]]:
                self.button_frames[coord].grid_forget()
                self.buttons.pop(coord)
            # This runs if one of the dimensions of the new shape is
            # larger than the previous.
            for coord in [(u, v) for u in range(self.dims[0])
                for v in range(self.dims[1]) if u >= prev_dims[0] or
                v >= prev_dims[1]]:
                self.grid.itemset(coord, -BIG)
                # Pack buttons if they have already been created.
                if coord in self.button_frames:
                    frame = self.button_frames[coord]
                    frame.grid_propagate(False)
                    frame.grid(row=coord[0], column=coord[1])
                    self.buttons[coord] = frame.children.values()[0]
                else:
                    self.make_button(coord)
            window.destroy()

        window = Toplevel(self.root)
        window.title('Size')
        Message(window, width=150,
            text="Enter number of rows and columns and press enter.").pack()
        frame = Frame(window)
        frame.pack(side='left')
        rows = IntVar()
        rows.set(self.dims[0])
        cols = IntVar()
        cols.set(self.dims[1])
        Label(frame, text='Rows').grid(row=1, column=0)
        Label(frame, text='Columns').grid(row=2, column=0)
        rows_entry = Entry(frame, textvariable=rows, width=10)
        columns_entry = Entry(frame, textvariable=cols, width=10)
        rows_entry.grid(row=1, column=1)
        columns_entry.grid(row=2, column=1)
        rows_entry.icursor(END)
        rows_entry.bind('<Return>', reshape)
        columns_entry.bind('<Return>', reshape)
        rows_entry.focus_set()

    def set_zoom(self):
        if self.button_size == 20:
            self.zoom_var.set(False)
        else:
            self.zoom_var.set(True)
        def get_zoom(event=None):
            old_button_size = self.button_size
            if event == None:
                self.button_size = 20
            else:
                try:
                    self.button_size = max(10,
                        min(40, int(event.widget.get())))
                except ValueError:
                    self.button_size = 20
            if self.button_size == 20:
                self.zoom_var.set(False)
            else:
                self.zoom_var.set(True)
            if old_button_size != self.button_size:
                self.nr_font = (self.nr_font[0], 10*self.button_size/17,
                    self.nr_font[2])
                for frame in self.button_frames.values():
                    frame.config(height=self.button_size,
                        width=self.button_size)
                for button in self.buttons.values():
                    button.config(font=self.nr_font)
            window.destroy()
        window = Toplevel(self.root)
        window.title('Zoom')
        Message(window, width=150, text="Enter desired button size in pixels\
            or click 'Default'.").pack()
        zoom_entry = Entry(window, width=5)
        zoom_entry.insert(0, self.button_size)
        zoom_entry.pack(side='left', padx=30)
        zoom_entry.bind('<Return>', get_zoom)
        zoom_entry.focus_set()
        Button(window, text='Default', command=get_zoom).pack(side='left')


class NrConfig(object):
    def __init__(self, grid):
        self.grid = grid
        self.dims = grid.shape
        self.all_coords = [(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]
        self.numbers = dict()
        self.groups = []
        self.configs = []
        self.probs = np.zeros(self.dims)
        self.get_numbers()
        self.get_groups()
        self.get_configs()
        self.get_probs()

    def __str__(self):
        grid = 100*self.probs.round(3)
        for coord, n in self.numbers.items():
            grid.itemset(coord, int(n))
        return str(grid).replace(' 0', ' .').replace('. ', '  ')

    def get_numbers(self):
        for coord, nr in [(c, self.grid.item(c)) for c in self.all_coords
            if self.grid[c] > 0]:
            empty_neighbours = {c for c in get_neighbours(
                coord, self.dims) if self.grid[c] == -BIG}
            if nr > len(empty_neighbours):
                # Handle properly...
                print "Error: number {} in cell {} is too high.".format(
                    nr, coord)
                return
            # Create Number instance and store in dictionary under coordinate.
            self.numbers[coord] = Number(nr, coord, empty_neighbours,
                self.dims)

    def get_groups(self):
        coord_neighbours = dict()
        for coord in [c for c in self.all_coords if self.grid[c] == -BIG]:
            # Must be a set so that order doesn't matter!
            coord_neighbours[coord] = {self.numbers[c] for c in
                get_neighbours(coord, self.dims) if c in self.numbers}
        while coord_neighbours:
            coord, neighbours = coord_neighbours.items()[0]
            equiv_coords = [c for c, ns in coord_neighbours.items()
                if ns == neighbours]
            for c in equiv_coords:
                del(coord_neighbours[c])
            if neighbours:
                grp = EquivGroup(equiv_coords, neighbours, self.dims)
                self.groups.append(grp)
            for n in neighbours:
                n.groups.append(grp)
        # Sort the groups by coordinate (top, left). Could be improved.
        self.groups.sort(key=lambda x: min(x.coords))

    def get_configs(self):
        def set_group(index, cfg):
            configs = []
            grp = cfg.groups[index]
            # print "\nIndex:", index
            # print grp
            # print grp.nr_neighbours
            # for n in grp.nr_neighbours:
            #     print n.groups
            for i in range(grp.get_min(), grp.get_max() + 1):
                # print "i =", i
                newcfg = cfg.copy()
                newgrp = newcfg.groups[index]
                newgrp.set_nr(i)
                for n in newgrp.nr_neighbours:
                    n.rem -= i
                neighbour_groups = [g for nr in newgrp.nr_neighbours
                    for g in nr.groups if g.nr == None]
                # print neighbour_groups
                if neighbour_groups:
                    next_group = neighbour_groups[0]
                elif [g for g in newcfg.groups if g.nr == None]:
                    next_group = [g for g in newcfg.groups if g.nr == None][0]
                else:
                    next_group = None
                if next_group:
                    next_index = newcfg.groups.index(next_group)
                    # print next_group, next_index
                    configs += set_group(next_index, newcfg)
                else:
                    newcfg.total = sum(newcfg.tup())
                    configs.append(newcfg)
            # print "\nIndex2:", index, configs
            return configs
        grps, nrs = EquivGroup.copy(self.groups, self.numbers)
        base_config = MineConfig(grps, nrs)
        groups = base_config.groups # Copied groups
        grp = min(groups) # Choose group with smallest max number
        self.configs = set_group(groups.index(grp), base_config)

    def get_probs(self):
        for cfg in self.configs:
            cfg.rel_prob = reduce(lambda x, g: x * g.rel_prob, cfg.groups, 1)
        divisor = sum([c.rel_prob for c in self.configs])
        for cfg in self.configs:
            cfg.prob = cfg.rel_prob / divisor
        for i, grp in enumerate(self.groups):
            grp.prob = sum([int(c.groups[i])*c.prob for c in self.configs])
            for coord in grp.coords:
                self.probs.itemset(coord, grp.prob/len(grp))
        self.expected = self.probs.sum()

    def print_info(self):
        # print "\n%d number group(s):"%len(self.numbers)
        # for n in self.numbers.values():
        #     print n

        print "\n%d equivalence group(s):"%len(self.groups)
        for g in self.groups:
            print g

        print "\n%d mine configuration(s):"%len(self.configs)
        for c in self.configs:
            print c, c.prob

        print "\n", self, self.expected


class MineConfig(object):
    def __init__(self, groups, numbers):
        self.groups = groups
        self.numbers = numbers
        self.total = None

    def __str__(self):
        return str(self.tup())

    def tup(self):
        return tuple([int(g) for g in self.groups])

    def copy(self):
        grps, nrs = EquivGroup.copy(self.groups, self.numbers)
        return MineConfig(grps, nrs)


class Number(object):
    """Contains information about the group of cells around a number."""
    def __init__(self, nr, coord, neighbours, dims):
        """Takes a number of mines, and a set of coordinates."""
        self.nr = nr
        self.coord = coord
        self.neighbours = neighbours
        self.groups = []
        self.dims = dims
        self.rem = nr

    def __repr__(self):
        return "<Number {}, ({}) with {} empty neighbours>".format(
            int(self), self.rem, len(self.neighbours)-int(self)+self.rem)

    def __str__(self):
        grid = np.zeros(self.dims, int)
        grid[self.coord] = int(self)
        for coord in self.neighbours:
            grid[coord] = 9
        return str(grid).replace('0', '.').replace('9', '#')

    def __int__(self):
        return self.nr
    def __sub__(self, other):
        return int(self) - int(other)


class EquivGroup(object):
    """
    Contains information about a group of cells which are effectively
    equivalent."""
    def __init__(self, coords, nr_neighbours, dims):
        self.nr = None
        self.coords = coords
        self.nr_neighbours = nr_neighbours
        self.dims = dims
        self.get_max()
        # self.get_min()

    def __repr__(self):
        ret = "<Equivalence group of {} cells including {}>".format(
            len(self.coords), self.coords[0])
        if self.nr != None:
            ret = ret[:-1] + ", containing {} mines>".format(int(self))
        return ret

    def __str__(self):
        grid = np.zeros(self.dims, int)
        for coord in self.coords:
            grid[coord] = 9
        for number in self.nr_neighbours:
            grid[number.coord] = int(number)
        ret = str(grid).replace('0', '.').replace('9', '#')
        if self.nr != None:
            ret += " {} mine(s)".format(int(self))
        return ret

    def __int__(self):
        return int(self.nr)
    def __lt__(self, other):
        nr1 = int(self) if self.nr else self.max_mines
        if type(other) is EquivGroup and not other.nr:
            nr2 = other.max_mines
        else:
            nr2 = int(other)
        return nr1 < nr2
    def __gt__(self, other):
        nr1 = int(self) if self.nr else self.max_mines
        if type(other) is EquivGroup and not other.nr:
            nr2 = other.max_mines
        else:
            nr2 = int(other)
        return nr1 > nr2
    def __len__(self):
        return len(self.coords)

    def get_max(self):
        if self.nr != None:
            self.max_mines = int(self)
        elif self.nr_neighbours:
            self.max_mines = min(len(self.coords),
                min([n.rem for n in self.nr_neighbours]))
        else: # No neighbours
            self.max_mines = len(self.coords)
        return self.max_mines

    def get_min(self):
        if self.nr:
            self.min_mines = int(self)
        else:
            self.min_mines = 0
            for n in self.nr_neighbours:
                max_others = sum([g.get_max() for g in n.groups if g != self])
                self.min_mines = max(self.min_mines, int(n) - max_others)
        # print "--", self.min_mines, self.nr_neighbours
        # grps = list(self.nr_neighbours)[0].groups
        # print [(g.get_max(), g) for g in grps if g != self]
        return self.min_mines

    def set_nr(self, nr):
        if nr == None:
            return
        self.nr = nr
        self.combinations = (fac(len(self)) /
            float(fac(self.nr)*fac(len(self)-self.nr)))
        self.rel_prob = self.combinations / 4**self.nr

    @staticmethod
    def copy(groups, numbers):
        """
        Copies a list of groups, making a deep copy of the number
        neighbours."""
        new_numbers = dict()
        for n in numbers.values():
            new_numbers[n.coord] = Number(n.nr, n.coord, n.neighbours, n.dims)
            new_numbers[n.coord].rem = n.rem
        new_groups = []
        for grp in groups:
            neighbours = {new_numbers[n.coord] for n in grp.nr_neighbours}
            new_groups.append(EquivGroup(grp.coords, neighbours, grp.dims))
            new_groups[-1].set_nr(grp.nr)
        for grp in new_groups:
            for n in grp.nr_neighbours:
                n.groups.append(grp)
            # print grp.nr_neighbours
        return new_groups, new_numbers


if __name__ == '__main__':
    gui = Gui()
    # case1 = NrConfig(grid)
