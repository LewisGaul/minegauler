#Make the disconnected cells a group of their own.

from Tkinter import *
from PIL import Image as ImagePIL, ImageTk
from math import log, exp, factorial as fac

from resources import *
from generate_probs import prob as get_unsafe_prob, combs as get_combs

__version__ = version

#Button states
FLAGGED = -400
UNCLICKED = -401
NUMBERED = -402
COLOURED = -403


class Gui(object):
    def __init__(self, dims=(10, 10), button_size=25, density=99.0/480):
        self.dims = dims
        self.button_size = button_size
        self.density = density
        self.root = Tk()
        self.root.title('Create configuration')
        self.root.resizable(False, False) #Turn off option of resizing window
        self.nr_font = ('Tahoma', 10*self.button_size/17, 'bold')
        self.grid = UNCLICKED*np.ones(self.dims, int)
        self.left_button_down = False
        self.right_button_down = False
        self.mouse_down_coord = None
        self.drag_flag = None
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
        b.state = UNCLICKED
        right_num = 3
        b.bind('<Button-1>', self.left_press)
        b.bind('<ButtonRelease-1>', self.left_release)
        b.bind('<Button-%s>'%right_num, self.right_press)
        b.bind('<ButtonRelease-%s>'%right_num, self.right_release)
        b.bind('<B1-Motion>', self.motion)
        b.bind('<B%s-Motion>'%right_num, self.motion)

    def get_images(self):
        im_size = self.button_size - 6
        im_path = join(im_direc, 'flags')
        im = ImagePIL.open(join(im_path, '1flag.png'))
        data = np.array(im)
        data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
            [240, 240, 237, 0])
        im = ImagePIL.fromarray(data, mode='RGBA').convert('RGB')
        im = im.resize(tuple([im_size]*2), ImagePIL.ANTIALIAS)
        self.flag_image = ImageTk.PhotoImage(im)


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
            if b.state != FLAGGED:
                b.config(bd=1, relief='sunken')

    def left_release(self, event=None):
        self.left_button_down = False
        if self.mouse_down_coord == None:
            return
        b = self.buttons[self.mouse_down_coord]
        if not self.right_button_down:
            self.mouse_down_coord = None
            if (not self.combined_click and self.grid[b.coord] < 8 and
                b.state != FLAGGED):
                b.state = NUMBERED
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
            if b.state in [UNCLICKED, COLOURED] and self.drag_flag != False:
                self.drag_flag = True
                b.config(bd=3, bg='SystemButtonFace', text="")
                b.config(image=self.flag_image) # Avoid bug in macs..?
                self.grid[b.coord] = b.state = FLAGGED
            elif b.state == FLAGGED and self.drag_flag != True:
                self.drag_flag = False
                b.config(image='')
                self.grid[b.coord] = b.state = UNCLICKED
            elif b.state == NUMBERED:
                self.drag_flag = None
                b.config(bd=3, relief='raised', text="")
                self.grid[b.coord] = b.state = UNCLICKED

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
                    if old_button.state == UNCLICKED:
                        old_button.config(bd=3, relief='raised')
                self.left_press(coord=cur_coord)
            elif self.right_button_down and not self.left_button_down: #right
                if (self.buttons[cur_coord].state != NUMBERED and
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
                if button.state == UNCLICKED:
                    button.config(bd=3, relief='raised')
            elif self.left_button_down and self.right_button_down: #both
                pass
            self.mouse_down_coord = None


    def show_probs(self):
        # First reset buttons
        for b in [b for b in self.buttons.values() if b.state == COLOURED]:
            b.config(bd=3, bg='SystemButtonFace', text="")
            b.state = UNCLICKED
        # if (self.grid < 1).all():
            # return
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
            button.state = UNCLICKED
        self.grid = UNCLICKED*np.ones(self.dims, int)

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
    def __init__(self, grid, density=0.2, mines=None, infinite=False,
        per_cell=1):
        self.grid = grid
        self.dims = grid.shape
        self.size = self.dims[0]*self.dims[1]
        self.per_cell = per_cell
        self.all_coords = [(i, j) for i in range(self.dims[0]) for j in range(self.dims[1])]
        self.flagged_cells = [c for c in self.all_coords if self.grid.item(c) == FLAGGED]
        if mines:
            self.mines = mines - len(self.flagged_cells)
        else:
            self.mines = (int(round(self.size*density, 0)) -
                len(self.flagged_cells))
        # Update density to avoid error.
        self.density = float(self.mines + len(self.flagged_cells))/self.size
        self.nr_coords = []
        self.numbers = dict()
        self.other_cells = list({c for c in self.all_coords if
            self.grid.item(c) == UNCLICKED} - set(self.nr_coords))
        self.groups = []
        self.configs = []
        self.probs = -np.ones(self.dims)
        self.last_time = tm.time()
        self.get_numbers()
        # print 1, tm.time() - self.last_time
        self.get_groups()
        # print 2, tm.time() - self.last_time
        if self.groups:
            self.get_configs()
            # print 3, tm.time() - self.last_time
            self.get_probs(infinite)
            # print 4, tm.time() - self.last_time
        else:
            self.all_probs = self.density*np.ones(self.dims)

    def __repr__(self):
        return "<Board with {} groups>".format(len(self.groups))

    def __str__(self):
        return

    def get_numbers(self):
        """
        Put the displayed numbers into dictionary with coordinate as key.
        """
        coords = set()
        for coord, nr in [(c, self.grid.item(c)) for c in self.all_coords if self.grid.item(c) > 0]:
            nbrs = get_neighbours(coord, self.dims)
            # Adjust to number of remaining neighbours that could contain mines.
            nr -= len(set(self.flagged_cells) & nbrs)
            empty_nbrs = {c for c in nbrs if self.grid.item(c) == UNCLICKED}
            # Coords next to a number. The need for this should be removed..?
            coords |= empty_nbrs
            if nr > len(empty_nbrs):
                raise ValueError("Error: number {} in cell {} is too high.".format(
                    nr, coord))
            self.numbers[coord] = {'nr':nr, 'spaces':empty_nbrs, 'groups':[]}
        # Bad name? This is all coords that are spaces next to a number...
        self.nr_coords = sorted(list(coords))

    def get_groups(self):
        """
        Find the equivalence groups and store EquivGroup objects in a list."""
        space_nbrs = dict()
        for coord, nr_info in self.numbers.items():
            for space in nr_info.pop('spaces'):
                space_nbrs[space] = space_nbrs.setdefault(space, [])
                space_nbrs[space] += [coord]
                space_nbrs[space].sort() # Allow for comparison
        # Convert lists to tuples which are hashable. Could be sped up?
        for nr_nbrs_tup in set(map(tuple, space_nbrs.values())):
            equiv_spaces = [sp for (sp, nbrs) in space_nbrs.items() if tuple(nbrs) == nr_nbrs_tup]
            grp = {'cells':equiv_spaces, 'nrs':list(nr_nbrs_tup)}
            grp['max'] = min(len(equiv_spaces),
                  min(map(lambda x: self.numbers[x]['nr'], nr_nbrs_tup)))
            self.groups.append(grp)
        # Sort the groups by coordinate (top, left). Could be improved.
        self.groups.sort(key=lambda g: min(g['cells']))
        for i, g in enumerate(self.groups):
            for nr in g['nrs']:
                self.numbers[nr]['groups'].append(i)

    def get_configs(self):
        cfgs = [len(self.groups)*[0]]
        for i, g in enumerate(self.groups):
            # print cfgs
            subcfgs = cfgs[:]
            cfgs = []
            for cfg in subcfgs:
                g_min = 0
                g_max = g['max']
                # new_nrs = [n.copy() for n in nrs]
                for coord in g['nrs']:
                    nr = self.numbers[coord]
                    prev_grps = nr['groups'][:nr['groups'].index(i)]
                    next_grps = nr['groups'][nr['groups'].index(i)+1:]
                    new_nr = (nr['nr'] -
                        reduce(lambda x, j: x + cfg[j], prev_grps, 0))
                    g_max = min(g_max, new_nr)
                    space = reduce(
                        lambda x, y:
                            x + self.per_cell*len(self.groups[y]['cells']),
                        next_grps, 0)
                    g_min = max(g_min, new_nr - space)
                for j in range(g_min, g_max + 1):
                    new_cfg = cfg[:]
                    new_cfg[i] = j
                    cfgs.append(new_cfg)
        self.configs = sorted(map(tuple, cfgs))

    def get_probs(self, infinite):
        cfg_probs = []
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
            n = np.count_nonzero(self.grid==UNCLICKED)
            k = self.mines
            S = sum([len(g['cells']) for g in self.groups])
            # a = fac(n)/fac(n - s) # Total cells contribution
            for cfg in self.configs:
                M = sum(cfg) # Mines in cfg
                combs = 1
                for i, mi in enumerate(cfg):
                    g_size = len(self.groups[i]['cells'])
                    combs *= get_combs(g_size, mi, self.per_cell)/fac(mi)
                    # print get_combs(g_size, mi, self.per_cell), fac(mi)
                    # combs *= fac(g_size) / (fac(m) * fac(g_size - mi))
                if M > self.per_cell * k: # Not enough space
                    cfg_probs.append(0)
                    continue
                # a = fac(M)
                b = fac(k)/fac(k - M) # Cells with mines contribution
                c = fac(n - k)/fac(n - k - S + M) # Cells without mines
                # print n, k, S, M, combs
                cfg_probs.append(exp(log(combs) + log(b) + log(c)))
            cfg_probs = map(lambda x: x/sum(cfg_probs), cfg_probs)
            # print cfg_probs
            for i, g in enumerate(self.groups):
                g_size = len(g['cells'])
                probs = 8*[0]
                unsafe_prob = 0
                for j in range(8):
                    probs[j] = sum(
                        [cfg_probs[a] for a, c in enumerate(self.configs)
                         if c[i]==j])
                    # print prob_j, get_unsafe_prob(g_size, j)
                    unsafe_prob += probs[j] * get_unsafe_prob(g_size, j, self.per_cell)
                g['probs'] = tuple(probs)
                g['exp'] = reduce(lambda n, x: n + x[0]*x[1], enumerate(g['probs']), 0)
                for coord in g['cells']:
                    # self.probs.itemset(coord, g['exp']/len(g['cells']))
                    self.probs.itemset(coord, unsafe_prob)
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
            rem_size = ((self.probs < 0) * (self.grid == UNCLICKED)).sum()
            if not rem_size:
                self.all_probs = self.probs.copy()
                return
            rem_mines = self.mines - self.expected
            density = rem_mines/rem_size
        self.all_probs = np.where((self.probs<0) * (self.grid==UNCLICKED),
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

        # print "\n", self, self.expected



if __name__ == '__main__':
    gui = Gui()
    c = NrConfig(gui.grid)
    nrs = c.numbers
    grps = c.groups
##    cfgs = c.configs


    if 0:
        subcfgs = [len(self.groups)*[0]]
        while subcfgs:
            cfg = subcfgs.pop()
            # Default, overwritten below.
            keep_cfg = True
            for i, g in enumerate(grps):
                new_max = g['max'] - cfg[i]
                for coord in g['nrs']:
                    nr = self.numbers[coord]
                    new_nr = (nr['nr'] -
                        reduce(lambda x, j: x + cfg[j], nr['groups'], 0))
                    new_max = min(new_max, new_nr)
                # If more mines can be placed carry on.
                if new_max > 0:
                    keep_cfg = False
                    new_cfg = cfg[:]
                    new_cfg[i] += 1
                    subcfgs.append(new_cfg)
                # Check numbers are actually satisfied.
                elif new_nr > 0:
                    keep_cfg = False
            if keep_cfg:
                self.configs.append(tuple(cfg))
        self.configs = sorted(set(self.configs))

    # for c1 in cfgs:
    #     print c1





























