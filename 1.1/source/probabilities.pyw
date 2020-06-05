"""Make the disconnected cells a group of their own."""

from Tkinter import *
from PIL import Image as PILImage
from math import log, exp, factorial as fac

from resources import *

__version__ = version

#Button state
INACTIVE = -1
NEUTRAL = 0
NUMBER = 1
COLOURED = 2


class Gui(object):
    def __init__(self, dims=(10, 10), button_size=25, density=99.0/480):
        self.dims = dims
        self.button_size = button_size
        self.density = density
        self.root = Tk()
        self.root.title('Create configuration')
        self.root.resizable(False, False) #Turn off option of resizing window
        self.nr_font = ('Tahoma', 10*self.button_size/17, 'bold')
        self.grid = -BIG*np.ones(self.dims, int)
        self.left_button_down, self.right_button_down = False, False
        self.mouse_down_coord, self.drag_flag = None, None
        self.combined_click = False
        self.make_menubar()
        self.make_panel()
        self.make_minefield()
        self.get_images()
        self.cfg = None
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
        # self.zoom_var = BooleanVar()
        # window_menu.add_checkbutton(label='Zoom', variable=self.zoom_var,
        #     command=self.set_zoom)
        window_menu.add_command(label='Density', command=self.set_density)
        self.infinite_var = BooleanVar()
        window_menu.add_checkbutton(label='Infinite',
            variable=self.infinite_var, command=self.show_probs)
        help_menu = Menu(self.menubar)
        self.menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='Help',
            command=lambda: self.show_text('probhelp', title='Help'),
            state='disabled')
        help_menu.add_command(label='About',
            command=lambda: self.show_text('probabout', 40, 5, 'About'),
            state='disabled')

    def make_panel(self):
        self.panel = Frame(self.root, pady=4, height=40)
        self.panel.pack(fill=BOTH)
        self.face_image = PhotoImage(name='face',
            file=join(im_direc, 'faces', 'ready1face.ppm'))
        face_frame = Frame(self.panel)
        # face_frame.place(x=10, rely=0.5, anchor=W)
        face_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.face_button = Button(face_frame, bd=4, image=self.face_image, takefocus=False, command=self.new)
        self.face_button.pack()
        self.done_button = Button(self.panel, bd=4, text="Done",
            font=('Times', 10, 'bold'), command=self.show_probs)
        # self.done_button.place(relx=1, x=-10, rely=0.5, anchor=E)

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
        right_num = 2 if platform == 'darwin' else 3
        b.bind('<Button-1>', self.left_press)
        b.bind('<ButtonRelease-1>', self.left_release)
        b.bind('<Button-%s>'%right_num, self.right_press)
        b.bind('<ButtonRelease-%s>'%right_num, self.right_release)
        b.bind('<B1-Motion>', self.motion)
        b.bind('<B%s-Motion>'%right_num, self.motion)

    def get_images(self):
        im_size = self.button_size - 6
        im_path = join(im_direc, 'flags')
        if not exists(join(im_path, '1flag%02d.ppm'%im_size)):
            im = PILImage.open(join(im_path, '1flag.png'))
            data = np.array(im)
            data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
                [240, 240, 237, 0])
            im = PILImage.fromarray(data, mode='RGBA').convert('RGB')
            im = im.resize(tuple([im_size]*2), PILImage.ANTIALIAS)
            im.save(join(im_path, '1flag%02d.ppm'%im_size))
            im.close()
        self.flag_image = PhotoImage(name='flag',
            file=join(im_path, '1flag%02d.ppm'%im_size))


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
            if b.state != INACTIVE:
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
                b.state = NUMBER
                nr = self.grid[b.coord] = max(0, self.grid[b.coord] + 1)
                text = nr if nr else ''
                colour = nr_colours[nr] if nr else 'black'
                b.config(bg='SystemButtonFace', text=text,
                    fg=colour, font=self.nr_font)
                self.show_probs()
            self.combined_click = False
        # if not b['text'] and b['relief'] == 'sunken':
        #     b.config(relief='raised', bd=3)

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
            if b.state in [NEUTRAL, COLOURED] and self.drag_flag != False:
                self.drag_flag = True
                b.config(bd=3, bg='SystemButtonFace',
                    text="")
                b.config(image=self.flag_image) # Avoid bug in macs
                b.state = INACTIVE
                self.grid[b.coord] = -10
            elif b.state == INACTIVE and self.drag_flag != True:
                self.drag_flag = False
                b.state = NEUTRAL
                b.config(image='')
                self.grid[b.coord] = -BIG
            elif b.state == NUMBER:
                self.drag_flag = None
                b.state = NEUTRAL
                b.config(bd=3, relief='raised', text="")
                self.grid[b.coord] = -BIG

    def right_release(self, event=None):
        self.right_button_down = False
        self.drag_flag = None
        if not self.left_button_down:
            self.mouse_down_coord = None
            self.combined_click = False
            self.show_probs()

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
                if (self.buttons[cur_coord].state != NUMBER and
                    self.drag_flag != None):
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


    def show_probs(self):
        # First reset buttons
        for b in [b for b in self.buttons.values() if b.state == COLOURED]:
            b.config(bd=3, bg='SystemButtonFace', text="")
            b.state = NEUTRAL
        if (self.grid < 1).all():
            return
        self.cfg = NrConfig(self.grid, density=self.density,
            infinite=self.infinite_var.get())
        # print self.cfg
        # self.cfg.print_info()
        probs = self.cfg.probs
        for coord, b in [item for item in self.buttons.items()
            if probs.item(item[0]) >= 0]:
            prob = round(probs.item(coord), 5)
            text = int(prob) if prob in [0, 1] else "%.2f"%round(prob, 2)
            if prob >= self.density:
                ratio = (prob - self.density)/(1 - self.density)
                colour = blend_colours(ratio)
            else:
                ratio = (self.density - prob)/self.density
                colour = blend_colours(ratio, high_colour=(0, 255, 0))
            b.state = COLOURED
            b.config(bd=2, bg=colour, text=text, fg='black',
                font=('Times', int(0.2*self.button_size+3.7), 'normal'))

    def new(self, event=None):
        for button in self.buttons.values():
            button.config(bd=3, relief='raised', bg='SystemButtonFace',
                text='', fg='black', font=self.nr_font, image='')
            button.state = NEUTRAL
        self.grid = -BIG*np.ones(self.dims, int)

    def set_size(self):
        def reshape(event):
            prev_dims = self.dims
            self.dims = rows.get(), cols.get()
            # self.grid.resize(self.dims)
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
                # self.grid.itemset(coord, -BIG)
                # Pack buttons if they have already been created.
                if coord in self.button_frames:
                    frame = self.button_frames[coord]
                    frame.grid_propagate(False)
                    frame.grid(row=coord[0], column=coord[1])
                    self.buttons[coord] = frame.children.values()[0]
                else:
                    self.make_button(coord)
            self.new()
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
        if self.button_size == 25:
            self.zoom_var.set(False)
        else:
            self.zoom_var.set(True)
        def get_zoom(event=None):
            old_button_size = self.button_size
            if event == None:
                self.button_size = 25
            else:
                try:
                    self.button_size = max(10,
                        min(40, int(event.widget.get())))
                except ValueError:
                    self.button_size = 25
            if self.button_size == 25:
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

    def set_density(self):
        def update(event):
            self.density = float(density.get())
            window.destroy()
            self.show_probs()
        window = Toplevel(self.root)
        window.title('Density')
        Message(window, width=150,
            text="Enter new mine density and press enter.").pack()
        density = StringVar()
        density.set(self.density)
        entry = Entry(window, textvariable=density, width=10)
        entry.pack()
        entry.bind('<Return>', update)
        entry.focus_set()


    def show_text(self, filename, width=80, height=24, title=None):
        window = Toplevel(self.root)
        if not title:
            title = filename.capitalize()
        window.title(title)
        scrollbar = Scrollbar(window)
        scrollbar.pack(side='right', fill=Y)
        text = Text(window, width=width, height=height, wrap=WORD,
            yscrollcommand=scrollbar.set)
        text.pack()
        scrollbar.config(command=text.yview)
        if exists(join(data_direc, filename + '.txt')):
            with open(join(data_direc, filename + '.txt'), 'r') as f:
                text.insert(END, f.read())
        text.config(state='disabled')



class NrConfig(object):
    def __init__(self, grid, density=0.2, mines=None, infinite=False):
        self.grid = grid
        self.dims = grid.shape
        self.size = self.dims[0]*self.dims[1]
        self.all_coords = [(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]
        self.flagged_coords = [c for c in self.all_coords
            if self.grid.item(c) == -10]
        if mines:
            self.mines = mines - len(self.flagged_coords)
        else:
            self.mines = (int(round(self.size*density, 0)) -
                len(self.flagged_coords))
        self.density = float(self.mines + len(self.flagged_coords))/self.size
        self.nr_coords = []
        self.numbers = dict()
        self.other_coords = list({c for c in self.all_coords if
            self.grid.item(c) == -BIG} - set(self.nr_coords))
        self.groups = []
        self.configs = []
        self.probs = -np.ones(self.dims)
        self.get_numbers()
        self.get_groups()
        grps, nrs = EquivGroup.copy(self.groups, self.numbers)
        base_config = MineConfig(grps, nrs)
        # groups = base_config.groups # Copied groups
        # grp = min(groups) # Choose group with smallest max number
        if self.groups:
            self.configs = self.get_configs(0, base_config)
            self.get_probs(infinite)
        else:
            self.all_probs = self.density*np.ones(self.dims)

    def __str__(self):
        grid = 100*self.probs.round(3)
        for coord, n in self.numbers.items():
            grid.itemset(coord, int(n))
        return str(grid).replace(' 0', ' .').replace('. ', '  ')

    def get_numbers(self):
        coords = set()
        for coord, nr in [(c, self.grid.item(c)) for c in self.all_coords
            if self.grid.item(c) > 0]:
            neighbours = get_neighbours(coord, self.dims)
            nr -= len(set(self.flagged_coords) & neighbours)
            empty_neighbours = {c for c in neighbours
                 if self.grid.item(c) < -10}
            # Coords next to a number.
            coords |= empty_neighbours
            if nr > len(empty_neighbours):
                # Handle properly...
                print "Error: number {} in cell {} is too high.".format(
                    nr, coord)
                return
            # Create Number instance and store in dictionary under coordinate.
            self.numbers[coord] = Number(nr, coord, empty_neighbours,
                self.dims)
        self.nr_coords = sorted(list(coords))

    def get_groups(self):
        coord_neighbours = dict()
        # Defined in get_neighbours method.
        for coord in self.nr_coords:
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

    def get_configs(self, index, cfg):
        configs = []
        grp = cfg.groups[index]
        min_mines = max(grp.get_min(), self.mines - cfg.sum() - len(self.other_coords))
        for i in range(min_mines, grp.get_max() + 1):
            # print "i =", i
            newcfg = cfg.copy()
            newgrp = newcfg.groups[index]
            newgrp.set_nr(i)
            newgrp.get_prob(self.density) # Remove and change...
            for n in newgrp.nr_neighbours:
                n.rem -= i
            neighbour_groups = [g for nr in newgrp.nr_neighbours
                for g in nr.groups if g.nr == None]
            if neighbour_groups:
                next_group = neighbour_groups[0]
            elif [g for g in newcfg.groups if g.nr == None]:
                next_group = [g for g in newcfg.groups if g.nr == None][0]
            else:
                next_group = None
            if next_group:
                next_index = newcfg.groups.index(next_group)
                configs += self.get_configs(next_index, newcfg)
            elif sum(newcfg.tup()) <= self.mines:
                newcfg.total = sum(newcfg.tup())
                size = self.size - len(self.flagged_coords)
                newcfg.get_probs(size, self.mines)
                configs.append(newcfg)
        return configs

    def get_probs(self, infinite):
        if infinite: # Infinite grid
            divisor = sum([c.inf_rel_prob for c in self.configs])
            for cfg in self.configs:
                cfg.inf_prob = cfg.inf_rel_prob / divisor
            for i, grp in enumerate(self.groups):
                grp.inf_prob = sum([int(c.groups[i])*c.inf_prob
                    for c in self.configs])
                for coord in grp.coords:
                    self.probs.itemset(coord, grp.inf_prob/len(grp))
        else: # Finite grid
            divisor = sum([c.rel_prob for c in self.configs])
            for cfg in self.configs:
                cfg.prob = cfg.rel_prob / divisor
            for i, grp in enumerate(self.groups):
                grp.prob = sum([int(c.groups[i])*c.prob for c in self.configs])
                for coord in grp.coords:
                    self.probs.itemset(coord, grp.prob/len(grp))
        self.probs = self.probs.round(7) # Avoid rounding errors!
        if (self.probs > 1).any():
            # Invalid configuration
            print "Invalid configuration gives probs:"
            print self.probs
            self.probs = None
            return
        self.expected = np.where(self.probs>=0, self.probs, 0).sum()
        if infinite:
            density = self.density
        else:
            rem_size = ((self.probs < 0) * (self.grid == -BIG)).sum()
            if not rem_size:
                self.all_probs = self.probs.copy()
                return
            rem_mines = self.mines - self.expected
            density = rem_mines/rem_size
        self.all_probs = np.where((self.probs<0) * (self.grid==-BIG),
            density, self.probs)
        # print self.all_probs
        # self.print_info()

    def print_info(self):
        # print "\n%d number group(s):"%len(self.numbers)
        # for n in self.numbers.values():
        #     print n

        print "\n%d equivalence group(s):"%len(self.groups)
        for g in self.groups:
            print g

        print "\n%d mine configuration(s):"%len(self.configs)
        for c in self.configs:
            print c#, c.prob

        print "\n", self, self.expected


class MineConfig(object):
    def __init__(self, groups, numbers):
        self.groups = groups
        self.numbers = numbers
        self.total = None

    def __str__(self):
        return str(self.tup())

    def __len__(self):
        return sum(map(len, self.groups))

    def sum(self):
        return sum([int(g) for g in self.groups if g.nr])

    def tup(self):
        return tuple([int(g) for g in self.groups])

    def get_probs(self, size, mines):
        self.inf_rel_prob = reduce(lambda x, g: x * g.rel_prob, self.groups, 1)
        combs = reduce(lambda x, g: x * g.combinations, self.groups, 1)
        n, k, m, r = size, mines, self.total, len(self)
        a = fac(n)/fac(n - r) # Clicked cells
        b = fac(k)/fac(k - m) # Cells with mines
        c = fac(n - k)/fac(n - k - r + m) # Cells without mines
        self.rel_prob = exp(log(combs) - log(a) + log(b) + log(c))

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
        self.combinations = None
        self.rel_prob = None
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
        self.combinations = (
            fac(len(self)) / float(fac(self.nr)*fac(len(self)-self.nr)))

    def get_prob(self, density):
        self.rel_prob = self.combinations * (density/(1 - density))**self.nr

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
            new_groups[-1].rel_prob = grp.rel_prob
        for grp in new_groups:
            for n in grp.nr_neighbours:
                n.groups.append(grp)
            # print grp.nr_neighbours
        return new_groups, new_numbers


if __name__ == '__main__':
    gui = Gui()
