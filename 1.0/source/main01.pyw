"""
To add:
Improve layout and useability of custom, highscores...
Add 'completed grid' option.
-Add 'official' option which disables FirstAuto etc.
Add 'overlap' layout option.
Sort option for numbers to display distance TO a mine.
-Collect more information in highscores/collect statistics.
"""
__version__ = '1.0'


from Tkinter import *
import os
import os.path as osp
from shutil import copy2 as copy_file
from glob import glob
from PIL import Image
import json
from imp import is_frozen

from game import *
from probabilities import NrConfig

#Button state
INACTIVE = -1
ACTIVE = 0
FLAGGED = 1
HIT = 2

#Drag select flagging type
UNFLAG = -1
FLAG = 1

if hasattr(sys, 'frozen') or is_frozen('__main__'): # In exe
    # print ".exe"
    main_direc = os.getcwd()
    # main_direc = osp.join(os.getcwd(), 'dist')
    im_direc = osp.join(main_direc, 'images')
else:
    main_direc = osp.dirname(os.getcwd()) #Up a level
    # print ".py"
    im_direc = osp.join(osp.dirname(main_direc), 'images')
data_direc = osp.join(main_direc, 'files')

default_settings = {'diff': 'b',
                    'dims': (8, 8),
                    'mines': 10,
                    'first_success': True,
                    'lives': 1,
                    'per_cell': 1,
                    'detection': 1,
                    'drag_select': False,
                    'distance_to': False,
                    'button_size': 16,
                    'name': ''}

highscore_headings = ['Name', 'type', '3bv', 'other', 'Date']

nr_mines = {'b':{0.5: 10, 1: 10, 1.5:  8, 1.8:  7, 2:  6,
    2.2:  5, 2.5:  5, 2.8:  4, 3:  4},
            'i':{0.5: 40, 1: 40, 1.5: 30, 1.8: 25,
    2: 25, 2.2: 20, 2.5: 18, 2.8: 16, 3: 16},
            'e':{0.5: 99, 1: 99, 1.5: 80, 1.8: 65,
    2: 60, 2.2: 50, 2.5: 45, 2.8: 40, 3: 40},
            'm':{0.5:200, 1:200, 1.5:170, 1.8:160,
    2:150, 2.2:135, 2.5:110, 2.8: 100, 3: 100}}
diff_dims = {'b':(8,8), 'i':(16,16), 'e':(16,30), 'm':(30, 30)}
dims_diff = {(8,8):'b', (16,16):'i', (16,30):'e', (30, 30):'m'}
diff_names = [('b', 'Beginner'), ('i', 'Intermediate'), ('e', 'Expert'),
    ('m', 'Master'), ('c', 'Custom')]
detection_options = dict([(str(i), i) for i in [0.5, 1, 1.5, 1.8, 2, 2.2, 2.5, 2.8, 3]])
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
bg_colours = dict([('',     (240, 240, 237)),
                   ('red',  (255,   0,   0)),
                   ('blue', (128, 128, 255))])
nr_font = ('Tahoma', 9, 'bold')

encode_highscore = lambda h: (
    int(10*h['date']/float(h['time'])) +
    int(100*float(h['3bv/s'])) + h['3bv'] -
    sum([c[0]*c[1] for c in h['coords']]) if h.has_key('coords') else 0 +
    reduce(lambda x, y: x + ord(y), h['name'], 0) + 3*h['lives'] +
    50*h['detection'] + 7*h['per cell'] + 19*int(h['drag']) +
    12*int(h['distance to']))


class Gui(object):
    def __init__(self, settings=dict(), **kwargs):
        self.settings = default_settings.copy() #To be overwritten
        for k, v in settings.items():
            self.settings[k] = v
        for k, v in kwargs.items():
            self.settings[k] = v
        for k, v in self.settings.items():
            setattr(self, k, v)
        # Check if custom.
        if ('dims' in kwargs and 'mines' in kwargs and
            ('diff' not in kwargs or self.diff not in diff_dims)):
            if self.dims in dims_diff:
                diff = dims_diff[self.dims]
                if nr_mines[diff][self.detection] != self.mines:
                    diff = 'c'
            else:
                diff = 'c'
            self.diff = self.settings['diff'] = diff
        elif self.diff in diff_dims: # If difficulty is not custom
            self.dims = self.settings['dims'] = diff_dims[self.diff]
            self.mines = nr_mines[self.diff][self.detection]
            self.settings['mines'] = self.mines

        data_path = osp.join(data_direc, 'data.txt')
        datacopy_path = osp.join(data_direc, 'datacopy.txt')
        # If datacopy file is larger assume an error in saving the
        # data, and copy the file across.
        print "Data file is {:.1f}MB in size.".format(
            osp.getsize(data_path)*1e-6)
        if (osp.exists(datacopy_path) and
            osp.getsize(data_path) < osp.getsize(datacopy_path)):
            print "Updating data file."
            copy_file(datacopy_path, data_path)
        try:
            with open(data_path, 'r') as f:
                # Removes any data entries without a correct key.
                self.all_data = [h for h in json.load(f) if
                    not h.has_key('key') or h['key'] == encode_highscore(h)]
                # self.all_data = json.load(f)
            # for d in [h for h in self.all_data]:
            #     d['key'] = encode_highscore(d)
            # for highscore in [h for h in self.all_data
            #     if not h.has_key('key') or encode_highscore(h) != h['key']]:
            #     delete = raw_input((
            #         "Corrupted data entry under name '{}' of time {}, " +
            #         "enter 'y' for delete. ").format(
            #             highscore['name'], highscore['time']))
            #     if delete == 'y':
            #         self.all_data.remove(highscore)
        except IOError:
            self.all_data = []
        except ValueError:
            copy_file(data_path,
                osp.join(data_direc, 'data_recovery{}.txt'.format(
                    tm.asctime().replace(':', ''))))
            self.all_data = []

        self.game = Game(self.settings, field=not(self.first_success))
        self.get_highscores()

        self.active_windows = dict()
        self.root = self.focus = self.active_windows['root'] = Tk()
        self.root.title('MineGauler' + __version__)
        self.root.protocol('WM_DELETE_WINDOW', lambda: self.close_root())
        # Turn off option of resizing window.
        self.root.resizable(False, False)
        # Set size of root window.
        self.root.geometry(
            '{}x{}'.format(self.dims[1]*self.button_size + 20,
                self.dims[0]*self.button_size + 82))

        self.make_menubar()
        self.diff_var.set(self.diff)
        if self.button_size != 16:
            self.zoom_var.set(True)
        self.first_success_var.set(self.first_success)
        self.lives_var.set(self.lives)
        self.per_cell_var.set(self.per_cell)
        self.detection_var.set(self.detection)
        self.drag_select_var.set(self.drag_select)
        self.distance_to_var.set(self.distance_to)
        self.nr_font = (nr_font[0], 10*self.button_size/17, nr_font[2])
        self.message_font = ('Times', 10, 'bold')
        self.make_panel()
        self.mines_var.set("%03d" % self.mines)
        self.make_minefield()
        self.get_images()
        self.make_name_entry()

        self.left_button_down, self.right_button_down = False, False
        self.mouse_down_coord = None
        self.combined_click = False

        mainloop()

    def __repr__(self):
        return None

    def make_menubar(self):
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.root.option_add('*tearOff', False)

        game_menu = Menu(self.menubar)
        self.menubar.add_cascade(label='Game', menu=game_menu)

        game_menu.add_command(label='New', command=self.new, accelerator="F2")
        self.root.bind_all('<F2>', self.new)
        game_menu.add_command(label='Replay', command=self.replay,
            accelerator="F3")
        self.root.bind_all('<F3>', self.replay)
        self.create_var = BooleanVar()
        game_menu.add_checkbutton(label='Create', variable=self.create_var,
            command=self.begin_creation, state='disabled')
        game_menu.add_command(label='Current info', command=self.show_info)
        game_menu.add_command(label='Probabilities', command=self.show_probs)
        game_menu.add_command(label='Highscores', command=self.show_highscores)
        game_menu.add_command(label='Statistics', command=None,
            state='disabled')

        game_menu.add_separator()
        self.diff_var = StringVar()
        for i in diff_names:
            game_menu.add_radiobutton(label=i[1], value=i[0],
                variable=self.diff_var, command=self.set_difficulty)

        game_menu.add_separator()
        self.zoom_var = BooleanVar()
        game_menu.add_checkbutton(label='Zoom', variable=self.zoom_var,
            command=self.set_zoom)
        self.timer_hide_var = BooleanVar()
        game_menu.add_checkbutton(label='Hide timer',
            variable=self.timer_hide_var, command=self.toggle_timer)
        game_menu.add_command(label='Reset to default',
            command=self.reset_settings)

        game_menu.add_separator()
        game_menu.add_command(label='Exit', command=self.root.destroy)


        options_menu = Menu(self.menubar)
        self.menubar.add_cascade(label='Options', menu=options_menu)

        self.first_success_var = BooleanVar()
        options_menu.add_checkbutton(label='FirstAuto',
            variable=self.first_success_var, command=self.update_settings)

        self.lives_var = IntVar()
        lives_menu = Menu(options_menu)
        options_menu.add_cascade(label='Lives', menu=lives_menu)
        for i in [1, 2, 3]:
            lives_menu.add_radiobutton(label=i, value=i,
                variable=self.lives_var, command=self.update_settings)
        lives_menu.add_radiobutton(label='Other', value=-1,
            variable=self.lives_var, command=self.set_lives)

        per_cell_menu = Menu(options_menu)
        self.per_cell_var = IntVar()
        options_menu.add_cascade(label='Max per cell', menu=per_cell_menu)
        for i, j in [(1, 1), (2, 2), ('Many', 10)]:
            per_cell_menu.add_radiobutton(label=i, value=j,
                variable=self.per_cell_var, command=self.update_settings)

        detection_menu = Menu(options_menu)
        self.detection_var = StringVar()
        options_menu.add_cascade(label='Detection', menu=detection_menu)
        #Add detection options.
        for i in sorted(list(detection_options)):
            detection_menu.add_radiobutton(label=i, value=i,
                variable=self.detection_var, command=self.update_settings)

        self.drag_select_var = BooleanVar()
        options_menu.add_checkbutton(label='Drag select',
            variable=self.drag_select_var, command=self.update_settings)

        options_menu.add_separator()
        self.distance_to_var = BooleanVar()
        options_menu.add_checkbutton(label='Distance to',
            variable=self.distance_to_var, command=self.update_settings,
            state='disabled')


        help_menu = Menu(self.menubar)
        self.menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='Basic rules', command=None,
            state='disabled')
        help_menu.add_command(label='Additional features',
            command=lambda: os.startfile(
                osp.join(data_direc, 'features.txt')))
        help_menu.add_separator()
        help_menu.add_command(label='About', command=
            lambda: os.startfile(osp.join(data_direc, 'about.txt')))

    def make_panel(self):
        self.panel = Frame(self.root, pady=4, height=40)
        self.panel.pack(fill=BOTH)

        self.mines_var = StringVar()
        self.mines_label = Label(self.panel, bg='black', fg='red', bd=5,
            relief='sunken', font=('Verdana',11,'bold'),
            textvariable=self.mines_var)
        self.mines_label.place(x=7, rely=0.5, anchor=W)

        self.face_images = dict()
        #Collect all faces that are in the folder and store in dictionary under filename.
        for path in glob(osp.join(im_direc, 'faces', '*.ppm')):
            im_name = osp.splitext(osp.split(path)[1])[0]
            self.face_images[im_name] = PhotoImage(name=im_name,
                file=osp.join(im_direc, 'faces', im_name + '.ppm'))
        face_frame = Frame(self.panel)
        face_frame.place(relx=0.5, rely=0.5, anchor=CENTER)
        n = min(self.lives, 3)
        self.face_button = Button(face_frame, bd=4,
            image=self.face_images['ready%sface'%n], takefocus=False,
            command=self.new)
        self.face_button.pack()

        self.timer = Timer(self.panel)
        self.timer.label.place(relx=1, x=-7, rely=0.5, anchor=E)

        for widget in [self.panel, self.mines_label, self.timer.label]:
            widget.bindtags(('panel',) + widget.bindtags())
        self.panel.bind_class('panel', '<Button-1>', lambda x: self.face_button.config(relief='sunken'))
        def panel_click(event):
            self.face_button.config(relief='raised')
            if event.x > 0 and event.x < event.widget.winfo_width() and event.y > 0 and event.y < 40:
                self.face_button.invoke()
        self.panel.bind_class('panel', '<ButtonRelease-1>', panel_click)

        #Not displayed unless in create mode.
        self.done_button = Button(self.panel, bd=4, text="Done", font=('Times', 10, 'bold'), command=self.finalise_creation)

    def make_minefield(self):
        self.width = self.dims[1]*self.button_size + 20
        self.height = self.dims[0]*self.button_size + 20
        self.mainframe = Frame(self.root, height=self.height, width=self.width)
        self.mainframe.pack()
        # Frame containing buttons and border.
        self.zoomframe = Frame(self.mainframe,
            height=100*self.button_size + 20,
            width=200*self.button_size + 20, bd=10)
        self.zoomframe.place(x=0, y=0, anchor=NW)
        # Frame placed underneath buttons for border.
        self.mainborder = Frame(self.zoomframe,
            height=self.height,
            width=self.width, bd=10, relief='ridge')
        self.mainborder.place(x=0, y=0, bordermode='outside')
        self.button_frames = dict()
        self.buttons = dict()
        for coord in [(u, v) for u in range(self.dims[0])
            for v in range(self.dims[1])]:
            self.make_button(coord)

    def make_button(self, coord):
        self.button_frames[coord] = f = Frame(self.zoomframe,
            width=self.button_size, height=self.button_size)
        f.rowconfigure(0, weight=1) # Enables button to fill frame
        f.columnconfigure(0, weight=1)
        f.grid_propagate(False) # Disables resizing of frame
        # Placed on top of mainborder frame, using relative positioning
        # so that they autoadjust on zoom.
        f.place(relx=float(coord[1])/200,
            rely=float(coord[0])/100)
        self.buttons[coord] = b = Label(f, bd=3, relief='raised',
            font=self.nr_font)
        b.grid(sticky='nsew')
        b.coord = coord
        b.state = ACTIVE
        b.bind('<Button-1>', self.left_press)
        b.bind('<ButtonRelease-1>', self.left_release)
        b.bind('<Button-3>', self.right_press)
        b.bind('<ButtonRelease-3>', self.right_release)
        b.bind('<Double-Button-1>', self.double_left_press)
        b.bind('<B1-Motion>', self.motion)
        b.bind('<B3-Motion>', self.motion)

    def submit_name_entry(self, event=None):
        self.name_entry.config(state=DISABLED)
        self.name = self.name_entry.get()[:20]
        self.focus = self.root
        if not self.game.state == WON:
            self.get_highscores()
        #print self.name
    def make_name_entry(self):
        def double_left_press(event):
            self.name_entry.config(state='normal') # NORMAL is in use
            self.focus = self.name_entry
            self.focus.focus_set()
            self.name_entry.select_range(0, END)
        self.name_entry = Entry(self.root, bd=2, width=self.width,
            font=self.message_font, justify=CENTER, disabledforeground='black')
        if self.name:
            self.name_entry.insert(0, self.name)
            self.name_entry.config(state=DISABLED)
        else:
            self.focus = self.name_entry
        self.name_entry.pack()
        self.name_entry.bind("<Return>", self.submit_name_entry)
        self.name_entry.bind("<Double-Button-1>", double_left_press)
        self.focus.focus_set()

    def get_images(self):
        #If the .ppm files for the current size do not exist, create them from the .png file.
        im_size = self.button_size - 2
        im_path = osp.join(im_direc, 'mines')
        for n in [i for i in range(1, 11) if not osp.exists(
            osp.join(im_path, '%smine%s.ppm'%(i, im_size)))]:
            for colour in bg_colours:
                #'Image' is from PIL, used to convert/resize/recolour.
                im = Image.open(osp.join(im_path, '%smine.png'%n))
                data = np.array(im)
                data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
                    list(bg_colours[colour]) + [0])
                im = Image.fromarray(data, mode='RGBA').convert('RGB')
                im = im.resize(tuple([im_size]*2), Image.ANTIALIAS)
                im.save(osp.join(im_path,
                    '%s%smine%02d.ppm'%(colour, n, im_size)))
                im.close()
        self.mine_images = dict()
        for n in range(1, 11):
            for c in bg_colours:
                im_name = '%s%smine' % (c, n)
                if not c:
                    key = n
                else:
                    key = (c, n)
                self.mine_images[key] = PhotoImage(name=im_name,
                    file=osp.join(
                        im_path, '%s%smine%02d.ppm'%(c, n, im_size)))

        im_size = self.button_size - 6
        im_path = osp.join(im_direc, 'flags')
        for n in [i for i in range(1, 4) if not osp.isfile(
            osp.join(im_path, '%sflag%s.ppm'%(i, im_size)))]:
            im = Image.open(osp.join(im_path, '%sflag.png'%n))
            data = np.array(im)
            data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
                list(bg_colours['']) + [0])
            im = Image.fromarray(data, mode='RGBA').convert('RGB')
            im = im.resize(tuple([im_size]*2), Image.ANTIALIAS)
            im.save(osp.join(im_path, '%sflag%02d.ppm'%(n, im_size)))
            im.close()
        self.flag_images = dict()
        for n in range(1, 4):
            im_name = '%sflag' % n
            self.flag_images[n] = PhotoImage(name=im_name,
                file=osp.join(im_path, '%sflag%02d.ppm'%(n, im_size)))


    def left_press(self, event=None, coord=None):
        if self.game.state in [LOST, WON, INACTIVE]:
            return
        self.submit_name_entry()
        if event:
            b = event.widget
        else:
            b = self.buttons[coord]
        self.left_button_down = True

        if self.right_button_down:
            self.both_press()
        else:
            self.mouse_down_coord = b.coord
            if self.drag_select:
                if b.state == ACTIVE:
                    self.click_button(b)
                if self.game.state == ACTIVE:
                    n = min(self.game.lives_remaining, 3)
                    self.face_button.config(image=self.face_images['active%sface'%n])
            else:
                if b.state == ACTIVE:
                    b.config(bd=1, relief='sunken')
                    n = min(self.game.lives_remaining, 3)
                    self.face_button.config(image=self.face_images['active%sface'%n])

    def left_release(self, event=None):
        self.left_button_down = False
        if self.game.state in [LOST, WON, INACTIVE] or not self.mouse_down_coord:
            return
        b = self.buttons[self.mouse_down_coord]
        if self.right_button_down:
            self.both_release()
        else:
            self.mouse_down_coord = None
            if b.state == ACTIVE and not self.combined_click and not self.drag_select:
                self.click_button(b)
            if self.game.state == ACTIVE:
                n = min(self.game.lives_remaining, 3)
                self.face_button.config(image=self.face_images['ready%sface'%n])
            self.combined_click = False

    def right_press(self, event=None, coord=None):
        if self.game.state in [LOST, WON, INACTIVE]:
            return
        self.submit_name_entry()
        if event: b = event.widget
        else:     b = self.buttons[coord]
        self.right_button_down = True

        if self.left_button_down:
            self.both_press()
        else:
            self.mouse_down_coord = b.coord
            if self.drag_select:
                if b.state == ACTIVE:
                    self.drag_flag = FLAG
                elif b.state == FLAGGED and self.per_cell == 1:
                    self.drag_flag = UNFLAG
                else:
                    self.drag_flag = None
            else: self.drag_flag = None
            if b.state == ACTIVE:
                b.config(image=self.flag_images[1])
                b.state = FLAGGED
                self.game.grid[b.coord] = -10
            elif b.state == FLAGGED:
                n = -self.game.grid[b.coord]/10
                if n == min(3, self.per_cell):
                    b.config(image='')
                    b.state = ACTIVE
                    self.game.grid[b.coord] = -BIG
                else:
                    b.config(image=self.flag_images[n+1])
                    self.game.grid[b.coord] -= 10
            self.set_mines_counter()

    def right_release(self, event=None):
        self.right_button_down = False
        if self.game.state in [LOST, WON, INACTIVE] or not self.mouse_down_coord:
            return

        if self.left_button_down:
            self.both_release()
        else:
            self.mouse_down_coord = None
            self.combined_click = False

    def double_left_press(self, event):
        if self.game.state in [LOST, WON, INACTIVE]:
            return

        b = event.widget
        if not self.right_button_down and self.per_cell > 2 and b.state == FLAGGED:
            b.config(image='')
            b.state = ACTIVE
            self.game.grid[b.coord] = -BIG
            self.set_mines_counter()

    def both_press(self):
        self.combined_click = True
        neighbours = get_neighbours(self.mouse_down_coord, self.dims, self.detection, True)
        for coord in {c for c in neighbours if self.buttons[c].state == ACTIVE}:
            self.buttons[coord].config(bd=1, relief='sunken')
        n = min(self.game.lives_remaining, 3)
        self.face_button.config(image=self.face_images['active%sface'%n])

    def both_release(self):
        #Either the left or right button has been released.
        b = self.buttons[self.mouse_down_coord]
        neighbours = get_neighbours(b.coord, self.dims, self.detection, True)

        grid_nr = self.game.grid[b.coord]
        if grid_nr >= 0:
            neighbouring_mines = 0
            for coord in {c for c in neighbours if self.buttons[c].state in [FLAGGED, HIT]}:
                neighbouring_mines -= self.game.grid[coord]/10
                if neighbouring_mines > grid_nr:
                    break

            if neighbouring_mines == grid_nr:
                for coord in {c for c in neighbours if self.buttons[c].state == ACTIVE}:
                    self.click_button(self.buttons[coord], False)
                self.check_completion()
            else:
                for coord in {c for c in neighbours if self.buttons[c].state == ACTIVE}:
                    self.buttons[coord].config(bd=3, relief='raised')

        else:
            for coord in {c for c in neighbours if self.buttons[c].state == ACTIVE}:
                self.buttons[coord].config(bd=3, relief='raised')

        if self.game.state in [READY, ACTIVE] and not (self.left_button_down and self.drag_select):
            n = min(self.game.lives_remaining, 3)
            self.face_button.config(image=self.face_images['ready%sface'%n])

    def motion(self, event):
        if self.game.state not in [READY, ACTIVE]:
            return

        clicked_coord = event.widget.coord
        cur_coord = (clicked_coord[0] + event.y/self.button_size,
            clicked_coord[1] + event.x/self.button_size)
        if cur_coord in [(u, v) for u in range(self.dims[0]) for v in range(self.dims[1])] and cur_coord != self.mouse_down_coord:
            if (self.left_button_down and not self.right_button_down
                and not self.combined_click): #left
                if self.mouse_down_coord and not self.combined_click:
                    old_button = self.buttons[self.mouse_down_coord]
                    new_button = self.buttons[cur_coord]
                    if not self.drag_select:
                        if old_button.state == ACTIVE:
                            old_button.config(bd=3, relief='raised')
                        if new_button.state != ACTIVE:
                            n = min(self.game.lives_remaining, 3)
                            self.face_button.config(image=self.face_images['ready%sface'%n])
                self.left_press(coord=cur_coord)

            elif self.right_button_down and not self.left_button_down: #right
                self.mouse_down_coord = cur_coord
                if self.drag_select:
                    b = self.buttons[self.mouse_down_coord]
                    if self.drag_flag == FLAG and b.state == ACTIVE:
                        b.config(image=self.flag_images[1])
                        b.state = FLAGGED
                        self.game.grid[b.coord] = max(self.game.grid[b.coord] - 10, -10)
                    elif self.drag_flag == UNFLAG and b.state == FLAGGED:
                        b.config(image='')
                        b.state = ACTIVE
                        self.game.grid[b.coord] = -BIG
                    self.set_mines_counter()

            elif self.left_button_down and self.right_button_down: #both
                if not self.mouse_down_coord:
                    self.mouse_down_coord = cur_coord
                    self.both_press()
                    return
                old_neighbours = get_neighbours(self.mouse_down_coord, self.dims, self.detection, True) if self.mouse_down_coord else set()
                new_neighbours = get_neighbours(cur_coord, self.dims, self.detection, True)
                for coord in {c for c in new_neighbours if self.buttons[c].state == ACTIVE} - old_neighbours:
                    self.buttons[coord].config(bd=1, relief='sunken')
                for coord in {c for c in old_neighbours if self.buttons[c].state == ACTIVE} - new_neighbours:
                    self.buttons[coord].config(bd=3, relief='raised')
            self.mouse_down_coord = cur_coord

        elif cur_coord != self.mouse_down_coord and self.mouse_down_coord:
            if self.left_button_down and not self.right_button_down: #left
                button = self.buttons[self.mouse_down_coord]
                if not self.drag_select and button.state == ACTIVE:
                    button.config(bd=3, relief='raised')

            elif self.left_button_down and self.right_button_down: #both
                old_neighbours = get_neighbours(self.mouse_down_coord, self.dims, self.detection, True)
                for coord in {c for c in old_neighbours if self.buttons[c].state == ACTIVE}:
                    self.buttons[coord].config(bd=3, relief='raised')

            n = min(self.game.lives_remaining, 3)
            self.face_button.config(image=self.face_images['ready%sface'%n])
            self.mouse_down_coord = None


    def click_button(self, button, check_complete=True):
        if self.game.state == READY:
            if self.first_success and not self.game.minefield.origin:
                if self.distance_to:
                    while self.game.minefield.completed_grid.item(button.coord) < 1:
                        self.game.minefield.generate()
                        if self.diff == 'c' and (self.game.minefield.completed_grid < 1).all():
                            print "Unable to find opening - change the settings."
                            break
                else:
                    self.game.minefield.generate(open_coord=button.coord)
            self.game.state = ACTIVE
            self.game.start_time = tm.time()
            self.timer.update(self.game.start_time)

        cell_nr = self.game.minefield.completed_grid[button.coord]
        if self.distance_to:
            pass
        else:
            if cell_nr == 0: # opening hit
                for opening in self.game.minefield.openings:
                    if button.coord in opening:
                        break #work with this set of coords
                for coord in [c for c in opening if self.buttons[c].state == ACTIVE]:
                    b = self.buttons[coord]
                    if b.state == ACTIVE:
                        nr = self.game.minefield.completed_grid[coord]
                        self.game.grid.itemset(coord, nr)
                        b.state = INACTIVE
                        if nr == 0:
                            b.config(bd=1, relief='sunken')
                        else:
                            try:
                                colour = nr_colours[nr]
                            except KeyError:
                                colour = 'black'
                            b.config(bd=1, relief='sunken', text=nr, fg=colour, font=self.nr_font)

            elif cell_nr > 0: # normal success
                self.game.grid.itemset(button.coord, cell_nr)
                button.state = INACTIVE
                try:
                    colour = nr_colours[cell_nr]
                except KeyError:
                    colour = 'black'
                button.config(bd=1, relief='sunken', text=cell_nr, fg=colour, font=self.nr_font)

            else: # mine hit
                button.state = HIT
                self.game.lives_remaining -= 1
                n = -cell_nr/10 # Number of mines in the cell
                if self.game.lives_remaining > 0: # Life lost, game continues
                    colour = '#%02x%02x%02x' % bg_colours['blue']
                    button.config(bd=1, relief='sunken', bg=colour,
                        image=self.mine_images[('blue', n)])
                    n = min(3, self.game.lives_remaining)
                    self.face_button.config(
                        image=self.face_images['ready%sface'%n])
                    self.game.grid[button.coord] = cell_nr
                    self.set_mines_counter()
                else: # game over
                    self.game.finish_time = tm.time()
                    self.game.state = LOST
                    colour = '#%02x%02x%02x' % bg_colours['red']
                    button.config(bd=1, relief='sunken', bg=colour,
                        image=self.mine_images[('red', n)])
                    self.face_button.config(image=self.face_images['lost1face'])
                    for coord, b in self.buttons.items():
                        grid_nr = self.game.grid.item(coord)
                        nr = self.game.minefield.completed_grid.item(coord)
                        if b.state == FLAGGED and grid_nr != nr:
                            b.state = INACTIVE
                            b.config(text='X', image='', font=self.nr_font)
                        elif b.state == ACTIVE and nr < -9:
                            b.state = INACTIVE
                            b.config(bd=1, relief='sunken', image=self.mine_images[-nr/10])
                    self.finalise_game()
                    return

        if check_complete:
            self.check_completion()

    def check_completion(self):
        grid2 = self.game.minefield.completed_grid
        if ( np.where(self.game.grid<-9, -10, self.game.grid) ==
            np.where(grid2 < -9, -10, grid2) ).all():
            self.game.finish_time = tm.time()
            self.game.state = WON
            n = min(self.game.lives_remaining, 3)
            self.face_button.config(image=self.face_images['won%sface'%n])
            self.mines_var.set("000")
            for coord, button in [(c, b) for c, b in self.buttons.items() if b.state in [ACTIVE, FLAGGED]]:
                n = -grid2.item(coord)/10
                button.config(image=self.flag_images[n])
                button.state = FLAGGED
            self.finalise_game()

    def finalise_game(self):
        self.left_button_down, self.right_button_down = False, False
        self.mouse_down_coord = None
        self.combined_click = False
        self.timer.start_time = None
        self.game.time_passed = self.game.finish_time - self.game.start_time
        if self.game.state == WON:
            self.game.bbbv_s = self.game.minefield.bbbv/self.game.time_passed
            self.game.prop_complete = 1
        else: #Game lost
            lost_field = Minefield(self.settings, create=False)
            lost_field.mine_coords = self.game.minefield.mine_coords
            lost_field.completed_grid = np.where(self.game.grid<0,
                self.game.minefield.completed_grid, 1)
            lost_field.get_openings()
            lost_field.get_3bv()
            rem_opening_coords = [c for opening in lost_field.openings
                for c in opening]
            completed_3bv = len(
                {c for c in get_nonzero_coords(self.game.grid >= 0)
                    if c not in rem_opening_coords})
            self.game.rem_3bv = lost_field.bbbv - completed_3bv
            bbbv = self.game.minefield.bbbv # Shorten
            self.game.prop_complete = float(bbbv-self.game.rem_3bv)/bbbv
            self.game.bbbv_s = self.game.prop_complete*bbbv/self.game.time_passed
        self.timer.var.set("%03d" % (min(self.game.time_passed + 1, 999)))
        self.timer.label.config(fg='red')
        nr_flagged_cells = ((self.game.grid!=-BIG) * (self.game.grid<0)).sum()
        self.game.flagging = float(nr_flagged_cells)/len(
            set(self.game.minefield.mine_coords))
        if not (self.game.minefield.origin or self.game.time_passed < 0.4 or
            self.diff == 'c' or self.lives > 3):
            self.save_game_data()

    def save_game_data(self):
        data = {
            'name':         self.name,
            'level':        self.game.diff,
            'lives':        self.game.lives,
            'per cell':     self.game.per_cell,
            'detection':    self.game.detection,
            'drag':         self.game.drag_select,
            'distance to':  self.game.distance_to,
            'time':         '%.2f' % (self.game.time_passed+0.01),
            '3bv':          self.game.minefield.bbbv,
            '3bv/s':        '%.2f' % self.game.bbbv_s,
            'proportion':   round(self.game.prop_complete, 4),
            'flagging':     self.game.flagging,
            'date':         self.game.finish_time,
            'lives rem':    self.game.lives_remaining,
            'first success':self.game.first_success,
            'zoom':         self.game.button_size}
        self.all_data.append(data)
        self.get_highscores()
        if data in [h for L in self.highscores.values() for h in L]:
            if self.lives == 1:
                data['coords'] = self.game.minefield.mine_coords
                # Include more game data.
            self.show_highscores(default=True)
        elif not self.name and self.game.state == WON:
            self.show_highscores(default=True)
        data['key'] = encode_highscore(data)
        # with open(osp.join(data_direc, 'datacopy.txt'), 'w') as f:
        #     json.dump(self.all_data, f)

    def get_highscores(self):
        # Collect all data entries for complete games with the same settings.
        self.relevant_data = [h for h in self.all_data
            if h['proportion'] == 1 and reduce(
                lambda x, k: x & (h[k[0]]==self.game.settings[k[1]]),
                [('level', 'diff'), ('lives', 'lives'),
                ('per cell', 'per_cell'), ('detection', 'detection'),
                ('drag', 'drag_select'), ('distance to', 'distance_to')
                ], True)]
        data = [h for h in self.relevant_data if h['name'] == self.name]
        self.highscores = dict()
        self.highscores['time'] = sorted(
            data, key=lambda x: float(x['time']))[:5]
        self.highscores['3bv'] = sorted(data, key=lambda x: float(x['3bv/s']),
            reverse=True)[:5]

    def set_mines_counter(self):
        grid = np.where(self.game.grid==-BIG, 0, self.game.grid)
        nr_remaining = self.game.minefield.mines - np.where(grid<-9, -grid/10, 0).sum()
        self.mines_var.set("%03d" % (abs(nr_remaining)))
        if nr_remaining < 0:
            self.mines_label.config(bg='red', fg='black')
        else:
            self.mines_label.config(bg='black', fg='red')

    def update_settings(self, run=False, new=False):
        if self.game.state != ACTIVE or run:
            self.first_success = self.first_success_var.get()
            self.lives = self.lives_var.get() if self.lives_var.get() > 0 else self.lives
            self.per_cell = self.per_cell_var.get()
            self.detection = detection_options[self.detection_var.get()]
            if self.diff != 'c':
                self.mines = nr_mines[self.diff][self.detection]
            self.drag_select = self.drag_select_var.get()
            self.distance_to = self.distance_to_var.get()
            for s in default_settings.keys():
                self.settings[s] = getattr(self, s)
            if run or self.game.state == READY:
                self.get_highscores()
                self.game.lives_remaining = self.lives
                n = min(3, self.lives)
                self.face_button.config(image=self.face_images['ready%sface'%n])
                #Create new game with these settings if no game origin.
                if new or self.game.minefield.origin == NORMAL:
                    self.game = Game(self.settings, not(self.first_success))
                else:
                    self.game.change_settings(self.settings)
            if not self.game.state == WON:
                self.set_mines_counter()

    def close_root(self):
        self.game.state = INACTIVE
        self.update_settings()
        self.root.destroy()
        with open(osp.join(data_direc, 'settings.txt'), 'w') as f:
            f.write(str(self.settings))
            print "Saved settings."
        with open(osp.join(data_direc, 'data.txt'), 'w') as f:
            json.dump(self.all_data, f)
            print "Saved game data."

    def close_window(self, window):
        self.active_windows[window].destroy()
        self.active_windows.pop(window)
        self.focus = self.root
        self.focus.focus_set()
        if window == 'highscores':
            with open(osp.join(data_direc, 'datacopy.txt'), 'w') as f:
                json.dump(self.all_data, f)


    def new(self, event=None, new=True):
        self.submit_name_entry()
        for button in [b for b in self.buttons.values() if b.state != ACTIVE]:
            button.config(bd=3, relief='raised', fg='black',
                bg='SystemButtonFace', font=self.nr_font, text='', image='')
            button.state = ACTIVE
        self.update_settings(run=True, new=new)
        self.timer.start_time = None
        self.timer.var.set('000')
        if self.timer_hide_var.get():
            self.timer.label.config(fg='black')
        self.game.lives_remaining = self.lives

    def replay(self, event=None):
        self.submit_name_entry()
        if self.game.state == READY and self.game.minefield.origin == NORMAL:
            return
        self.game = Game(self.settings, field=self.game.minefield)
        self.new(new=False)

    def begin_creation(self, reset=True):
        if self.create_var.get(): #Only implement if create_var is true.
            field = Minefield(self.settings, create=True)
            self.game = Game(self.settings, field) #Overwrite previous game
            self.mines = 0
            if self.game.state != READY:
                for button in [b for b in self.buttons.values() if b.state != ACTIVE]:
                    button.config(bd=3, relief='raised', fg='black', bg='SystemButtonFace', font=nr_font, text='', image='')
                    button.state = ACTIVE
            self.update_settings(run=True)
            self.timer.start_time = None #Stop timer
            self.timer.var.set("000")
            self.set_mines_counter()
            self.timer.label.place_forget()
            self.done_button.place(relx=1, x=-7, rely=0.5, anchor=E)
        else:
            self.new()
            self.done_button.place_forget()
            self.timer.label.place(relx=1, x=-7, rely=0.5, anchor=E)

    def finalise_creation(self):
        pass

    def show_info(self):
        self.submit_name_entry()
        if (self.focus.bindtags()[1] == 'Entry' or
            'info' in self.active_windows):
            self.focus.focus_set()
            return
        self.focus = window = self.active_windows['info'] = Toplevel(self.root)
        window.title('Info')
        window.protocol('WM_DELETE_WINDOW', lambda: self.close_window('info'))
        info = (
            "This {d[0]} x {d[1]} grid has {} mines with "
            "a max of {} per cell.\n"
            "Detection level: {},  Drag select: {},  Lives remaining: {}"
            ).format(self.mines, self.per_cell, self.detection,
                self.drag_select, self.game.lives_remaining, d=self.dims)
        time = self.game.time_passed
        if self.game.state == WON:
            info += (
                "\n\nIt has 3bv of {}.\n\n"
                "You completed it in {:.2f} seconds, with 3bv/s of {:.2f}."
                ).format(self.game.minefield.bbbv, time+0.01, self.game.bbbv_s)
        elif self.game.state == LOST:
            info += (
                "\n\nIt has 3bv of {}.\n\n"
                "You lost after {:.2f} seconds, completing {:.1f}%. The grid\n"
                "has a remaining 3bv of {} with predicted completion time\n"
                "of {:.1f} seconds with a continued 3bv/s of {:.2f}."
                ).format(self.game.minefield.bbbv, time+0.01,
                    100*self.game.prop_complete, self.game.rem_3bv,
                    time/self.game.prop_complete, self.game.bbbv_s)
        Label(window, text=info, font=('Times', 10, 'bold')).pack()

    def show_probs(self):
        grid = np.where(self.game.grid==-BIG, -1, self.game.grid)
        print str(grid).replace('-1', ' #').replace('0', '.')
        print NrConfig(self.game.grid)

    def show_highscores(self, default=False, flagging=None, htype='time'):
        self.submit_name_entry()
        if self.focus.bindtags()[1] == 'Entry':
            self.focus.focus_set()
            return
        if 'highscores' in self.active_windows:
            window = self.focus = self.active_windows['highscores']
        else:
            window = self.focus = Toplevel(self.root)
            self.active_windows['highscores'] = window
            window.title('Highscores')
            window.resizable(False, False)
            window.protocol('WM_DELETE_WINDOW',
                lambda: self.close_window('highscores'))

        if (self.game.state == WON and self.game.finish_time ==
            self.relevant_data[-1]['date']):
            data = self.relevant_data[-1]
        else:
            data = None
        if ((data and default and data in self.highscores['time']) or
            (not default and flagging == None and htype == 'time')):
            htype = 'time'
            if self.name:
                highscores = self.highscores['time']
            else:
                highscores = sorted(self.relevant_data,
                    key=lambda x: float(x['time']))
        elif ((data and default and data in self.highscores['3bv']) or
            (not default and flagging == None and htype == '3bv/s')):
            htype = '3bv/s'
            if self.name:
                highscores = self.highscores['3bv']
            else:
                highscores = sorted(self.relevant_data,
                    key=lambda x: float(x['3bv/s']), reverse=True)
        else: # flagging is not None
            highscores = [h for h in self.relevant_data
                if bool(h['flagging']) == flagging]
            if self.name:
                highscores = [h for h in highscores if h['name'] == self.name]
            highscores = sorted(highscores, key=lambda x: float(x[htype]))
            if htype == '3bv/s':
                highscores.reverse()
        if self.name:
            highscores = highscores[:5]
        else:
            names = ['']
            highscores2 = []
            for h in highscores:
                if h['name'] not in names or h == data and not data['name']:
                    names.append(h['name'])
                    highscores2.append(h)
            highscores = highscores2[:10]
        headings = highscore_headings[:]
        headings[1] = htype.capitalize()
        headings[3] = '3bv/s' if headings[1] != '3bv/s' else 'Time'
        if self.name:
            headings.remove('Name')
        if self.game.state == WON:
            settings = self.game.settings
        else:
            settings = self.settings
        if settings['lives'] > 1:
            headings.insert(-1, 'Lives\nleft')
        # If the current highscore is the all-time best, display a message.
        if (data and
            data == min(self.relevant_data, key=lambda x: float(x['time'])) and
            self.game.lives == 1):
            Label(window, padx=10, pady=10, bg='yellow', text=(
                "Congratulations, you set a new\n" +
                "all-time MineGauler time record\n" +
                "for these settings!!"),
                font=('Times', 12, 'bold')).pack()
        # Create an introductory message to summarise the settings.
        flag_phrase = '(non-flagging) ' if flagging == False else (
            '(flagging) ' if flagging == True else '')
        name_phrase = self.name + "'s " if self.name else ''
        intro = (
            "{}{} {} highscores {}with settings:\n" +
            "Max per cell = {}, Detection = {}, Drag = {}\n").format(
                name_phrase, dict(diff_names)[settings['diff']], htype,
                flag_phrase, self.game.per_cell, self.game.detection,
                bool(self.game.drag_select))
        if (self.game.state == WON and self.game.lives > 1 or
            self.game.state != WON and self.lives > 1):
            intro = intro[:-1] + ", Lives = {}\n".format(self.game.lives)
        Label(window, text=intro, font=('times', 12, 'normal')).pack()
        # Create a frame to contain the highscores grid.
        grid_frame = Frame(window)
        grid_frame.pack(anchor=W)
        # Display the headings.
        for i, h in enumerate(headings):
            Label(grid_frame, text=h, font=('Times', 12, 'normal')).grid(
                row=0, column=i+1)
        def set_name(event):
            data['name'] = event.widget.get()[:20]
            data['key'] = encode_highscore(data)
            # row = event.widget.grid_info()['row']
            # event.widget.destroy()
            # Label(window, text=data['name'], font=('times', 11, 'bold')).grid(row=row, column=1)
            self.focus = window
            with open(osp.join(data_direc, 'datacopy.txt'), 'w') as f:
                json.dump(self.all_data, f)
            copy_file(osp.join(data_direc, 'datacopy.txt'),
                osp.join(data_direc, 'data.txt'))
            for w in window.children.values():
                w.destroy()
            self.show_highscores(default=True)
        row = 1
        for d in highscores:
            font = ('Times', 11, 'bold') if d == data else ('Times', 11, 'normal')
            Label(grid_frame, text=row, font=font, padx=10).grid(row=row, column=0)
            col = 1
            for i in headings:
                if i in ['Date', 'Lives\nleft']:
                    break
                if i == 'Name' and not d['name'] and d == data:
                    self.focus = e = Entry(grid_frame)
                    self.focus.focus_set()
                    e.grid(row=row, column=col)
                    e.bind('<Return>', set_name)
                else:
                    Label(grid_frame, text=d[i.lower()], font=font).grid(
                        row=row, column=col)
                col += 1
            if 'Lives\nleft' in headings:
                Label(grid_frame, text=d['lives rem'], font=font).grid(
                        row=row, column=col)
                col += 1
            Label(grid_frame, text=tm.strftime(
                '%d %b %Y %H:%M', tm.gmtime(d['date'])), font=font).grid(
                    row=row, column=col)
            row += 1
        lower_frame = Frame(window)
        lower_frame.pack()
        def change_flagging():
            for w in window.children.values():
                w.destroy()
            flagging = eval(flagging_var.get())
            self.show_highscores(flagging=flagging, htype=htype)
        flagging_var = StringVar()
        flagging_var.set(str(flagging))
        for i in [('All', 'None'), ('Flagged', 'True'),
            ('Non-flagged', 'False')]:
            Radiobutton(lower_frame, text=i[0], font=('times', 10, 'bold'),
                value=i[1], variable=flagging_var,
                command=change_flagging).pack(side='left')
        def change_type():
            for w in window.children.values():
                w.destroy()
                t = 'time' if htype == '3bv/s' else '3bv/s'
            self.show_highscores(flagging=flagging, htype=t)
        Button(lower_frame, padx=10, bd=3, text='Time / 3bv/s',
            font=('times', 10, 'bold'), command=change_type).pack(side='top')


    def set_difficulty(self):
        self.submit_name_entry()
        def validate(event, defocus=False):
            try:
                x = max(0, rows.get())
            except ValueError:
                x = -1
            try:
                y = max(0, cols.get())
            except ValueError:
                y = -1
            dims = (x, y)
            try:
                z = max(0, mines.get())
            except ValueError:
                z = -1
            valid = True
            if not (0 < x <= 100):
                if not defocus or self.root.focus_get() != rows_entry:
                    invalid_message[1].grid(row=1, column=2)
                    invalid_message[1].after(2000, invalid_message[1].grid_forget)
                if x > 100:
                    rows.set(100)
                else:
                    valid = False
            if not (0 < y <= 100):
                if not defocus or self.root.focus_get() != columns_entry:
                    invalid_message[2].grid(row=2, column=2)
                    invalid_message[2].after(2000, invalid_message[2].grid_forget)
                if y > 100:
                    cols.set(100)
                else:
                    valid = False
            if not defocus and valid and not (0 < z < x*y*self.per_cell):
                valid = False
                invalid_message[3].grid(row=3, column=2)
                invalid_message[3].after(2000, invalid_message[3].grid_forget)
                if z and x and y and z > x*y*self.per_cell:
                    mines.set(x*y*self.per_cell/2)
            return valid

        def get_shape(event):
            if not validate(event):
                return
            self.dims = rows.get(), cols.get()
            self.mines = mines.get()
            #Check if this is actually custom.
            if self.dims in dims_diff:
                diff = dims_diff[self.dims]
                if nr_mines[diff][self.detection] != self.mines:
                    diff = 'c'
            else:
                diff = 'c'
            self.diff = self.settings['diff'] = diff
            self.diff_var.set(diff)
            reshape()
            self.close_window('custom')

        def reshape():
            self.width = self.dims[1]*self.button_size + 20
            self.height = self.dims[0]*self.button_size + 20
            # Make root window the right size.
            self.root.geometry(
                '{}x{}'.format(self.width, self.height + 62))
            # Make the frames the right size.
            self.mainframe.config(height=self.height,
                width=self.width)
            self.mainborder.config(height=self.height, width=self.width)
            # Remove buttons that would lie over the border.
            for coord in (
                set([(x, self.dims[1]) for x in range(self.dims[0]+1)]) |
                set([(self.dims[0], y) for y in range(self.dims[1])])):
                if coord in self.button_frames:
                    self.button_frames[coord].place_forget()
            prev_dims = self.game.grid.shape
            # This runs if one of the dimensions was previously larger.
            for coord in [(u, v) for u in range(prev_dims[0])
                for v in range(prev_dims[1]) if u >= self.dims[0] or
                    v >= self.dims[1]]:
                #self.button_frames[coord].place_forget()
                self.buttons.pop(coord)
            # This runs if one of the dimensions of the new shape is
            # larger than the previous.
            for coord in [(u, v) for u in range(self.dims[0])
                for v in range(self.dims[1]) if u >= prev_dims[0] or
                    v >= prev_dims[1]]:
                # Pack buttons if they have already been created.
                if coord in self.button_frames:
                    self.button_frames[coord].grid_propagate(False)
                    self.button_frames[coord].place(relx=float(coord[1])/200,
                        rely=float(coord[0])/100)
                    self.buttons[coord] = self.button_frames[coord].children.values()[0]
                else:
                    self.make_button(coord)
            self.new()

        if self.diff_var.get() == 'c':
            self.diff_var.set(self.diff)
            # Do nothing if window requiring an entry is already open.
            if (self.focus.bindtags()[1] == 'Entry' or
                'custom' in self.active_windows):
                self.focus.focus_set()
                return
            def get_mines(event):
                if not validate(event, defocus=True):
                    return

                dims = x, y = rows.get(), cols.get()
                if dims in dims_diff:
                    mines.set(nr_mines[dims_diff[dims]][self.detection])
                else:
                    if self.root.focus_get() != rows_entry and (not x or x < 1 or x > 100):
                        invalid_message[1].grid(row=1, column=2)
                        invalid_message[1].after(2000, invalid_message[1].grid_forget)
                        if x and x > 100:
                            rows.set(100)
                        else:
                            invalid = True
                    if self.root.focus_get() != columns_entry and (
                        not y or y < 1 or y > 200):
                        invalid_message[2].grid(row=2, column=2)
                        invalid_message[2].after(2000, invalid_message[2].grid_forget)
                        if y and y > 200:
                            cols.set(200)
                        else:
                            invalid = True
                    #Formula for getting reasonable number of mines.
                    d = float(self.detection_var.get()) - 1
                    mines.set(max(1, int((0.09*d**3 - 0.25*d**2 - 0.15*d + 1)*
                        (dims[0]*dims[1]*0.2))))
            #self.game.state = INACTIVE
            window = self.active_windows['custom'] = Toplevel(self.root)
            window.minsize(200, 50)
            window.title('Custom')
            window.protocol('WM_DELETE_WINDOW',
                lambda: self.close_window('custom'))
            Label(window, text="Enter a number for each of\n"+
                               "the following then press enter.").pack()
            frame = Frame(window)
            frame.pack(side='left')
            rows = IntVar()
            rows.set(self.dims[0])
            cols = IntVar()
            cols.set(self.dims[1])
            mines = IntVar()
            mines.set(self.mines)
            Label(frame, text='Rows').grid(row=1, column=0)
            Label(frame, text='Columns').grid(row=2, column=0)
            Label(frame, text='Mines').grid(row=3, column=0)
            self.focus = rows_entry = Entry(frame, textvariable=rows, width=10)
            columns_entry = Entry(frame, textvariable=cols, width=10)
            mines_entry = Entry(frame, textvariable=mines, width=10)
            rows_entry.grid(row=1, column=1)
            columns_entry.grid(row=2, column=1)
            mines_entry.grid(row=3, column=1)
            rows_entry.icursor(END)
            rows_entry.bind('<FocusOut>', get_mines)
            columns_entry.bind('<FocusOut>', get_mines)
            rows_entry.bind('<Return>', get_shape)
            columns_entry.bind('<Return>', get_shape)
            mines_entry.bind('<Return>', get_shape)
            invalid_message = dict([(i+1, Message(frame, text='Invalid entry',
                font=self.message_font, width=100)) for i in range(3)])
            self.focus.focus_set()
        else:
            self.diff = self.diff_var.get()
            self.dims = diff_dims[self.diff]
            self.mines = nr_mines[self.diff][self.detection]
            reshape()

    def set_zoom(self):
        self.submit_name_entry()
        if self.button_size == 16:
            self.zoom_var.set(False)
        else:
            self.zoom_var.set(True)
        if self.focus.bindtags()[1] == 'Entry':
            self.focus.focus_set()
            return
        def get_zoom(event=None):
            old_button_size = self.button_size
            if event == None:
                self.button_size = 16
            else:
                try:
                    self.button_size = max(10, min(100, int(event.widget.get())))
                except ValueError:
                    self.button_size = 16
            if self.game.state == ACTIVE:
                # Make sure game gets correct button size
                self.game.button_size = None
            if self.button_size == 16:
                self.zoom_var.set(False)
            else:
                self.zoom_var.set(True)
            if old_button_size != self.button_size:
                self.nr_font = (self.nr_font[0], 10*self.button_size/17,
                    self.nr_font[2])
                self.width = self.dims[1]*self.button_size + 20
                self.height = self.dims[0]*self.button_size + 20
                #Make root window the right size.
                self.root.geometry(
                    '{}x{}'.format(self.width, self.height + 62))
                #Make the frames the right size.
                self.mainframe.config(height=self.height, width=self.width)
                self.mainborder.config(height=self.height, width=self.width)
                self.zoomframe.config(height=100*self.button_size + 20,
                    width=200*self.button_size + 20)
                for coord, frame in self.button_frames.items():
                    #Update frame sizes.
                    frame.config(height=self.button_size,
                        width=self.button_size)
                for button in [b for b in self.buttons.values() if b.state == INACTIVE]:
                    button.config(font=self.nr_font)
                self.get_images()
            self.close_window('zoom')
        window = self.active_windows['zoom'] = Toplevel(self.root)
        window.title('Zoom')
        window.protocol('WM_DELETE_WINDOW', lambda: self.close_window('zoom'))
        Message(window, width=150, text="Enter desired button size in pixels or click 'Default'.").pack()
        self.focus = zoom_entry = Entry(window, width=5)
        zoom_entry.insert(0, self.button_size)
        zoom_entry.pack(side='left', padx=30)
        zoom_entry.bind('<Return>', get_zoom)
        zoom_entry.focus_set()
        Button(window, text='Default', command=get_zoom).pack(side='left')

    def toggle_timer(self):
        if self.timer_hide_var.get() and self.game.state in [READY, ACTIVE, INACTIVE]:
            self.timer.label.config(fg='black')
        else: self.timer.label.config(fg='red')

    def reset_settings(self):
        for k, v in default_settings.items():
            setattr(self, k, v)
        self.settings = default_settings.copy()
        self.timer_hide_var.set(False)
        self.timer.label.config(fg='red')
        self.first_success_var.set(self.first_success)
        self.lives_var.set(self.lives if self.lives in [1, 2, 3] else -1)
        self.drag_select_var.set(self.drag_select)
        self.per_cell_var.set(self.per_cell)
        self.diff_var.set(self.diff)
        self.detection_var.set(self.detection)
        for frame in self.button_frames.values():
            frame.config(height=self.button_size, width=self.button_size)
        self.nr_font = nr_font
        self.set_difficulty() #Also runs self.new()

    def set_lives(self):
        self.submit_name_entry()
        self.lives_var.set(self.lives if self.lives in [1, 2, 3] else -1)
        if self.game.state == ACTIVE:
            self.lives_var.set(self.lives if self.lives in [1, 2, 3] else -1)
            return #Only run if not in game
        if self.focus.bindtags()[1] == 'Entry':
            self.focus.focus_set()
            return
        def get_lives(event):
            lives = event.widget.get()
            if not lives:
                self.lives = 1
            elif not lives.isdigit() or int(lives) < 1:
                invalid_message.pack(side='top')
                invalid_message.after(2000, invalid_message.forget)
                return
            else:
                self.lives = int(lives)
            self.game.lives_remaining = self.lives
            self.lives_var.set(self.lives if self.lives in [1, 2, 3] else -1)
            self.close_window('lives')
            if (self.game.grid == -BIG).all():
                self.game.state = READY
                n = min(3, self.game.lives_remaining)
                self.face_button.config(image=self.face_images['ready%sface'%n])

        self.game.state = INACTIVE
        window = self.active_windows['lives'] = Toplevel(self.root)
        window.title('Lives')
        window.protocol('WM_DELETE_WINDOW', lambda: self.close_window('lives'))
        Message(window, text="Enter a number of lives and press enter.",
            width=100).pack()
        self.focus = lives_entry = Entry(window, width=10)
        lives_entry.insert(0, self.lives)
        lives_entry.pack(side='top')
        lives_entry.bind('<Return>', get_lives)
        invalid_message = Message(window, text="Invalid entry.",
            font=self.message_font, width=100)
        self.focus.focus_set()



    def done_action(self):
        "Only used when creating game."
        create_var.set('False')
        self.game_origin = 'created'
        self.mines_grid = np.where(self.grid < -1, -self.grid/9, 0)
        self.mine_coords = map(tuple, np.transpose(np.nonzero(self.mines_grid>0)))
        self.mines = self.mines_grid.sum()
        self.get_final_grid()
        self.get_openings()
        ##DispThread(threading.active_count(), self, (self.completed_grid,)).start()
        prettify_grid(self.completed_grid, 1)
        replay()
        done_button.forget()
        new_button_frame.pack(side='left')
        self.timer.label.pack(side='left')
        first_success_var.set(False)
        diff = shape_difficulty[self.shape] if self.shape in shape_difficulty else 'c'
        if diff != 'c' and detection_mines[(diff, self.detection)] == self.mines:
            self.diff = diff
            self.diff_var.set(diff)



class Timer(object):
    def __init__(self, parent):
        self.parent = parent
        self.var = StringVar()
        self.var.set("000")
        self.label = Label(parent, bg='black', fg='red', bd=5, relief='sunken', font=('Verdana',11,'bold'), textvariable=self.var)
        self.start_time = None

    def __repr__(self):
        return "<Timer object>"

    def update(self, start_time=None):
        if start_time: self.start_time = start_time
        if self.start_time:
            elapsed = tm.time() - self.start_time
            self.var.set("%03d" % (min(elapsed + 1, 999)))
            self.parent.after(100, self.update)



if __name__ == '__main__':
    try:
        with open(osp.join(data_direc, 'settings.txt'), 'r') as f:
            settings = eval(f.read())
        print "Imported settings."
        #print "Imported settings: ", settings
    except:
        settings = default_settings
    gui = Gui(settings) # Initialise the GUI.