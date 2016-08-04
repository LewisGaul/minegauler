
import os
from os.path import join, split, splitext, exists
import Tkinter as tk
import tkFileDialog, tkMessageBox
from PIL import Image as PILImage, ImageTk
import time as tm
from glob import glob

import numpy as np

from constants import * #version, platform etc.
from utils import direcs

diff_dims = {
    'b':(8,8), 'i':(16,16), 'e':(16,30), 'm':(30, 30),
    (8,8):'b', (16,16):'i', (16,30):'e', (30, 30):'m'
    }
diff_names = [
    ('b', 'Beginner'),
    ('i', 'Intermediate'),
    ('e', 'Expert'),
    ('m', 'Master'),
    ('c', 'Custom')
    ]
nr_font = ('Tahoma', 9, 'bold')
msg_font = ('Times', 10, 'bold')


class BasicGui(tk.Tk, object):
    def __init__(self, **kwargs):
        # Defaults which may be overwritten below.
        self.settings = {
            'diff': 'b',
            'per_cell': 1,
            'detection': 1,
            'drag_select': False,
            'distance_to': False,
            'button_size': 16, #pixels
            'first_success': True,
            'style': 'original'
            }
        # Force standard settings (basic version).
        kwargs['per_cell'] = 1
        kwargs['detection'] = 1
        # Overwrite with any given settings.
        for k, v in kwargs.items():
            self.settings[k] = v
        # Store each setting as an attribute of the class.
        for k, v in self.settings.items():
            setattr(self, k, v)
        # Prioritise the difficulty given.
        if self.diff in ['b', 'i', 'e', 'm']:
            self.dims = self.settings['dims'] = diff_dims[self.diff]
            self.mines = nr_mines[self.diff][self.detection]
            self.settings['mines'] = self.mines

        self.all_coords = [(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]

        # Dictionary to keep track of which windows are open.
        self.active_windows = dict()
        # Initialise the root window.
        super(BasicGui, self).__init__()
        self.focus = self.active_windows['root'] = self
        self.focus.focus_set()
        if IN_EXE:
            self.title('MineGauler')
        else:
            self.title('MineGauler' + VERSION)
        self.iconbitmap(default=join(direcs['images'], 'icon.ico'))
        self.protocol('WM_DELETE_WINDOW', self.close_root)
        # Set default to be that menus cannot be 'torn off'.
        self.option_add('*tearOff', False)
        self.nr_font = (nr_font[0], 10*self.button_size/17, nr_font[2])
        self.msg_font = msg_font

        # Set variables.
        self.diff_var = tk.StringVar()
        self.diff_var.set(self.diff)
        self.zoom_var = tk.BooleanVar()
        if self.button_size != 16:
            self.zoom_var.set(True)
        self.drag_select_var = tk.BooleanVar()
        self.drag_select_var.set(self.drag_select)

        # t = tm.time()
        self.get_images()
        # print "Time to get images was {:.2f}s.".format(tm.time() - t)
        # Make main body of GUI.
        self.make_panel()
        self.make_minefield()
        self.make_menubar()

        # Turn off option of resizing window.
        self.resizable(False, False)
        self.block_windows = False

        # Keep track of mouse clicks.
        self.left_button_down = False
        self.right_button_down = False
        self.mouse_coord = None
        self.is_both_click = False
        self.drag_flag = None

    def __repr__(self):
        return "<Basic minesweeper GUI>"

    def get_size(self):
        return self.dims[0]*self.dims[1]

    @staticmethod
    def get_tk_colour(tup):
        return '#%02x%02x%02x'%tup[:3]

    @staticmethod
    def add_to_bindtags(widgets, tag):
        if type(widgets) is list:
            for w in widgets:
                w.bindtags((tag,) + w.bindtags())
        else: #assume a single widget is passed in
            w = widgets
            w.bindtags((tag,) + w.bindtags())

    def mouse_in_widget(self, widget):
        mousex = self.winfo_pointerx() - widget.winfo_rootx()
        mousey = self.winfo_pointery() - widget.winfo_rooty()
        width = widget.winfo_width()
        height = widget.winfo_height()
        if (mousex > 0 and mousex < width and
            mousey > 0 and mousey < height):
            return True
        else:
            return False

    def get_nbrs(self, coord, include=False):
        # Also belongs in minefield class...
        dist = self.detection
        d = dist if dist % 1 == 0 else int(dist) + 1
        x, y = coord
        row = [u for u in range(x-d, x+1+d) if u in range(self.dims[0])]
        col = [v for v in range(y-d, y+1+d) if v in range(self.dims[1])]
        # Extra feature removed.
        if dist % 1 == 0:
            nbrs = {(u, v) for u in row for v in col}
        if not include:
            #The given coord is not included.
            nbrs.remove(coord)
        return nbrs

    # Make the GUI.
    def make_panel(self):
        self.panel = tk.Frame(self, height=40, pady=4)
        self.panel.pack(fill='both')
        # Make the gridded widgets fill the panel.
        self.panel.columnconfigure(1, weight=1)
        self.face_images = dict()
        # Collect all faces that are in the folder and store in dictionary
        # under filename.
        for path in glob(join(direcs['images'], 'faces', '*.ppm')):
            im_name = splitext(split(path)[1])[0]
            self.face_images[im_name] = tk.PhotoImage(name=im_name,
                file=join(direcs['images'], 'faces', im_name + '.ppm'))
        face_frame = tk.Frame(self.panel)
        face_frame.grid(column=1, padx=4)
        # Create face button which will refresh the board.
        self.face_button = tk.Button(face_frame, bd=4, takefocus=False,
            image=self.face_images['ready1face'], command=self.start_new_game)
        self.face_button.pack()

        # Add bindtag to panel.
        self.add_to_bindtags(self.panel, 'panel')
        # Bind to mouse click and release on panel.
        self.panel.bind_class('panel', '<Button-1>',
            lambda x: self.face_button.config(relief='sunken'))
        def panel_click(event):
            self.face_button.config(relief='raised')
            if self.mouse_in_widget(self.panel):
                self.face_button.invoke()
        self.panel.bind_class('panel', '<ButtonRelease-1>', panel_click)

    def set_cell_image(self, coord, image, tag=True):
        x = (coord[1] + 0.49) * self.button_size
        y = (coord[0] + 0.49) * self.button_size
        tag = 'overlay' if tag else ''
        return self.board.create_image(x, y, image=image, tag=tag)

    def make_minefield(self):
        btn_size = self.button_size
        self.mainframe = tk.Frame(self, bd=10, relief='ridge')
        self.mainframe.pack()
        self.board = tk.Canvas(self.mainframe, height=self.dims[0]*btn_size,
            width=self.dims[1]*btn_size, highlightthickness=0)
        self.board.pack()
        # Place the background button image in blocks of 8x8, allowing for
        # large board size without packing more.
        for i in range(0, 500, 8):
            for j in range(0, 1000, 8):
                center = (i + 3.5, j + 3.5)
                self.set_cell_image(center, self.bg_image, tag=False)
        self.buttons = dict()
        for coord in self.all_coords:
            self.buttons[coord] = Cell(coord, self)
        self.set_button_bindings()

    def set_button_bindings(self):
        self.board.bind('<Button-1>', self.detect_left_press)
        self.board.bind('<ButtonRelease-1>', self.detect_left_release)
        self.board.bind('<Button-%s>'%RIGHT_BTN_NUM, self.detect_right_press)
        self.board.bind('<ButtonRelease-%s>'%RIGHT_BTN_NUM,
            self.detect_right_release)
        self.board.bind('<B1-Motion>', self.detect_motion)
        self.board.bind('<B%s-Motion>'%RIGHT_BTN_NUM, self.detect_motion)
        self.board.bind('<Control-1>', self.detect_ctrl_left_press)

    def unset_button_bindings(self):
        self.board.unbind('<Button-1>')
        self.board.unbind('<ButtonRelease-1>')
        self.board.unbind('<Button-%s>'%RIGHT_BTN_NUM)
        self.board.unbind('<ButtonRelease-%s>'%RIGHT_BTN_NUM)
        self.board.unbind('<B1-Motion>')
        self.board.unbind('<B%s-Motion>'%RIGHT_BTN_NUM)
        self.board.unbind('<Control-1>')

    def make_menubar(self):
        self.menubar = MenuBar(self)
        self.config(menu=self.menubar)
        self.menubar.add_item('game', 'command', 'New',
            command=self.start_new_game, accelerator='F2')
        self.bind('<F2>', self.start_new_game)
        self.menubar.add_item('game', 'separator')
        for i in diff_names:
            self.menubar.add_item('game', 'radiobutton', i[1], value=i[0],
                command=self.set_difficulty, variable=self.diff_var)
        self.menubar.add_item('game', 'separator')
        self.menubar.add_item('game', 'checkbutton', 'Zoom',
            command=self.get_zoom, variable=self.zoom_var)
        self.menubar.add_item('game', 'separator')
        self.menubar.add_item('game', 'command', 'Exit', command=self.destroy)

        self.menubar.add_item('opts', 'checkbutton', 'Drag-select',
            variable=self.drag_select_var, command=self.update_settings)

        show_about = lambda: self.show_text('about', 40, 5)
        self.menubar.add_item('help', 'command', 'About', accelerator='F1',
            command=show_about)
        self.bind_all('<F1>', show_about)

    @staticmethod
    def get_photoimage(filename, size, bg=None):
        im = PILImage.open(join(direcs['images'], filename))
        if bg is None:
            bg = ''
        else:
            col = bg_colours[bg]
            data = np.array(im)
            # Set background colour.
            data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
                list(col) + [0])
            # Remove alpha (transparency) channel.
            im = PILImage.fromarray(data, mode='RGBA').convert('RGB')
        im = im.resize((size, size), PILImage.ANTIALIAS)
        return ImageTk.PhotoImage(im, name=filename + bg)

    def get_images(self):
        direc = join('styles', self.style)
        # Create the PhotoImages from the png files.
        self.bg_image = self.get_photoimage(join(direc, '64btns.png'),
            8*self.button_size)
        self.bg_images = dict() #backgrounds
        self.bg_images['up'] = self.get_photoimage(join(direc, 'btn_up.png'),
            self.button_size)
        self.bg_images['down'] = self.get_photoimage(
            join(direc, 'btn_down.png'), self.button_size)
        self.bg_images['red'] = self.get_photoimage(
            join(direc, 'btn_down_red.png'), self.button_size)

        self.mine_images = dict() #mines
        size = self.button_size - 2
        for c in bg_colours:
            if not c:
                key = 1
            else:
                key = '%s1' % c
            self.mine_images[key] = self.get_photoimage('mine1.png', size, c)

        self.flag_images = dict() #flags
        self.cross_images = dict() #wrong flags
        size = self.button_size - 6
        self.flag_images[1] = self.get_photoimage('flag1.png', size, bg='')
        self.cross_images[1] = self.get_photoimage('cross1.png', size, bg='')

    # Button actions.
    def get_mouse_coord(self, event):
        return tuple(
            map(lambda p: getattr(event, p)/self.button_size, ['y', 'x']))

    def detect_left_press(self, event=None):
        self.left_button_down = True
        if self.right_button_down:
            self.both_press(self.mouse_coord)
        else:
            self.mouse_coord = self.get_mouse_coord(event)
            self.left_press(self.mouse_coord)

    def detect_left_release(self, event=None):
        self.left_button_down = False
        if not self.mouse_coord:
            self.is_both_click = False
            return
        if self.right_button_down:
            self.both_release(self.mouse_coord)
        elif self.is_both_click:
            self.is_both_click = False
            self.mouse_coord = None
        else:
            self.left_release(self.mouse_coord)
            self.mouse_coord = None

    def detect_right_press(self, event=None):
        self.right_button_down = True
        if self.left_button_down:
            self.both_press(self.mouse_coord)
        else:
            self.mouse_coord = self.get_mouse_coord(event)
            self.right_press(self.mouse_coord)

    def detect_right_release(self, event=None):
        self.right_button_down = False
        if not self.mouse_coord:
            self.is_both_click = False
            return
        if self.left_button_down:
            self.both_release(self.mouse_coord)
        elif self.is_both_click:
            self.is_both_click = False
            self.mouse_coord = None
        else:
            self.right_release(self.mouse_coord)
            self.mouse_coord = None

    def detect_motion(self, event):
        if self.get_mouse_coord(event) in self.all_coords:
            cur_coord = self.get_mouse_coord(event)
        else:
            cur_coord = None
        if cur_coord == self.mouse_coord: #no movement across buttons
            return
        if cur_coord is None:
            self.face_button.config(image=self.face_images['ready1face'])
        if self.left_button_down:
            if self.right_button_down: #both
                self.both_motion(cur_coord, self.mouse_coord)
            elif not self.is_both_click or self.drag_select: #left
                self.left_motion(cur_coord, self.mouse_coord)
        elif not self.is_both_click: #right
            self.right_motion(cur_coord, self.mouse_coord)
        self.mouse_coord = cur_coord

    def detect_ctrl_left_press(self, event=None):
        coord = self.get_mouse_coord(event)
        if not self.right_button_down:
            self.ctrl_left_press(coord)

    def left_press(self, coord):
        pass

    def left_release(self, coord, check_complete=True):
        pass

    def left_motion(self, coord, prev_coord):
        pass

    def right_press(self, coord):
        pass

    def right_release(self, coord):
        pass

    def right_motion(self, coord, prev_coord):
        pass

    def both_press(self, coord):
        self.is_both_click = True

    def both_release(self, coord):
        # Either the left or right button has been released.
        pass

    def both_motion(self, coord, prev_coord):
        pass

    def ctrl_left_press(self, coord):
        pass

    # GUI and game methods.
    def refresh_board(self, event=None):
        self.board.delete('overlay')
        for btn in [b for b in self.buttons.values() if b.state != UNCLICKED]:
            btn.refresh(del_imgs=False)
        self.update_settings()
        self.set_button_bindings()
        self.left_button_down = self.right_button_down = False
        self.mouse_coord = None
        self.is_both_click = False

    def close_root(self):
        self.destroy()

    def track_window(self, win):
        title = win.title()
        self.active_windows[title] = win
        win.protocol('WM_DELETE_WINDOW', lambda: self.close_window(title))
        self.block_windows = True

    def close_window(self, name):
        """Keep track of the windows which are open, and set the focus as
        appropriate."""
        self.active_windows[name].destroy()
        self.active_windows.pop(name)
        self.block_windows = False
        self.focus = self
        self.focus.focus_set()

    # Game menu methods.
    def start_new_game(self, event=None):
        self.refresh_board()

    def set_difficulty(self):
        if self.diff_var.get() in diff_dims: #standard board
            self.diff = self.diff_var.get()
            self.mines = nr_mines[self.diff][self.detection]
            self.reshape(diff_dims[self.diff])
            self.start_new_game()
        else: #custom, open popup window
            # Don't change the radiobutton until custom is confirmed.
            self.diff_var.set(self.diff)
            self.get_custom()

    def get_custom(self):
        def size_slide(num):
            rows = row_slider.get()
            cols = col_slider.get()
            row_entry.delete(0, 'end')
            col_entry.delete(0, 'end')
            row_entry.insert(0, rows)
            col_entry.insert(0, cols)
            old_max = mine_slider['to']
            new_max = rows * cols / 2
            mine_slider.set(new_max * float(mine_slider.get()) / old_max)
            mine_slider.config(to=new_max)
        def mines_slide(num):
            mine_entry.delete(0, 'end')
            mine_entry.insert(0, num)
        def focus_out():
            pass

        def set_custom(event=None):
            rows = row_entry.get()
            cols = col_entry.get()
            mines = mine_entry.get()
            # Check for invalid entries.
            if (rows not in map(str, range(2, 51)) or
                cols not in map(str, range(2, 101))):
                return
            else:
                rows = int(rows)
                cols = int(cols)
            if mines not in map(str, range(1, rows*cols)): #also invalid
                return
            mines = int(mines)
            dims = (rows, cols)
            self.close_window(title)
            self.mines = mines
            self.reshape(dims)
            # Needed here - after window is closed.
            self.start_new_game()

        if self.block_windows:
            self.focus.focus_set()
            return
        title = 'Custom'
        win = Window(self, title)
        tk.Message(win.mainframe, width=200, text=(
            "Select the desired number of rows, columns and mines. "
            "The number of mines must be less than the size of the board, "
            "and the size of the board must be less than 50x100."
            )).pack(pady=10)
        entry_frame = tk.Frame(win.mainframe)
        entry_frame.pack()
        row_slider = tk.Scale(entry_frame, from_=2, to=50, length=140,
            orient='horizontal', showvalue=False, takefocus=False,
            command=size_slide)
        col_slider = tk.Scale(entry_frame, from_=2, to=100, length=140,
            orient='horizontal', showvalue=False, takefocus=False,
            command=size_slide)
        mine_slider = tk.Scale(entry_frame, from_=1, to=self.get_size()/2,
            length=140, orient='horizontal', showvalue=False, takefocus=False,
            command=mines_slide)
        row_entry = tk.Entry(entry_frame, width=4, justify='right')
        col_entry = tk.Entry(entry_frame, width=4, justify='right')
        mine_entry = tk.Entry(entry_frame, width=4, justify='right')
        tk.Label(entry_frame, text='Rows').grid(row=1, column=1)
        row_slider.grid(row=1, column=2)
        row_entry.grid(row=1, column=3)
        tk.Label(entry_frame, text='Columns').grid(row=2, column=1)
        col_slider.grid(row=2, column=2)
        col_entry.grid(row=2, column=3)
        tk.Label(entry_frame, text='Mines').grid(row=3, column=1)
        mine_slider.grid(row=3, column=2)
        mine_entry.grid(row=3, column=3)
        row_slider.set(self.dims[0])
        row_entry.insert(0, self.dims[0])
        col_slider.set(self.dims[1])
        col_entry.insert(0, self.dims[1])
        mine_slider.set(self.mines)
        mine_entry.insert(0, self.mines)

        win.make_btn('OK', set_custom)
        win.make_btn('Cancel', lambda: self.close_window(title))
        self.add_to_bindtags([win, row_entry, col_entry, mine_entry], 'custom')
        self.bind_class('custom', '<Return>', set_custom)
        self.focus = row_entry
        self.focus.focus_set()

    def reshape(self, dims):
        old_dims = self.dims
        # This runs if one of the dimensions was previously larger.
        extras = [c for c in self.all_coords if c[0] >= dims[0] or
            c[1] >= dims[1]]
        for coord in extras:
            self.buttons.pop(coord)
        self.all_coords = [(i, j) for i in range(dims[0])
            for j in range(dims[1])]
        # size = 8 * self.button_size
        # for i in range(0, dims[0], 8):
        #     for j in range(0, dims[1], 8):
        #         if (i, j) not in self.buttons:
        #             center = (i + 3.5, j + 3.5)
        #             self.set_cell_image(center, self.bg_image, tag=False)
        new = [c for c in self.all_coords if c[0] >= old_dims[0] or
            c[1] >= old_dims[1]]
        for coord in new:
            self.buttons[coord] = Cell(coord, self)
        self.board.config(height=self.button_size*dims[0],
            width=self.button_size*dims[1])
        self.dims = dims
        # Check if this is custom.
        if (dims in diff_dims and
            self.mines == nr_mines[diff_dims[dims]][self.detection]):
            self.diff = diff_dims[dims]
            self.diff_var.set(self.diff)
        else:
            self.diff = 'c'
            self.diff_var.set('c')
        self.refresh_board()

    def get_zoom(self):
        def slide(num):
            # Slider is moved, change text entry.
            zoom_entry.delete(0, 'end')
            zoom_entry.insert(0, num)

        def set_zoom(event=None):
            text = zoom_entry.get()
            if event == 'default':
                text = '100'
            if text not in map(str, range(60, 501)): #invalid
                return
            old_button_size = self.button_size
            self.button_size = int(round(int(text)*16.0/100, 0))
            self.settings['button_size'] = self.button_size
            if self.button_size == 16:
                self.zoom_var.set(False)
            else:
                self.zoom_var.set(True)
            if old_button_size != self.button_size:
                self.board.config(height=self.button_size*self.dims[0],
                    width=self.button_size*self.dims[1])
                self.board.delete('all')
                self.get_images()
                for i in range(0, 500, 8):
                    for j in range(0, 1000, 8):
                        center = (i + 3.5, j + 3.5)
                        self.set_cell_image(center, self.bg_image, tag=False)
                self.nr_font = (self.nr_font[0], 10*self.button_size/17,
                    self.nr_font[2])
            self.close_window(title)
            self.start_new_game()

        # Ensure tick on radiobutton is correct.
        if self.button_size == 16:
            self.zoom_var.set(False)
        else:
            self.zoom_var.set(True)
        if self.block_windows:
            self.focus.focus_set()
            return
        title = 'Zoom'
        win = Window(self, title)
        tk.Message(win.mainframe, width=180, text=(
            "Select the desired increase in button size compared to the "
            "default, which should be an integer from 60 to 500."
            )).pack(pady=10)
        zoom = int(round(100*self.button_size/16.0, 0))
        slider = tk.Scale(win.mainframe, from_=60, to=200, length=140,
            orient='horizontal', showvalue=False, command=slide)
        zoom_entry = tk.Entry(win.mainframe, width=4, justify='right')
        tk.Label(win.mainframe, text='%  ').pack(side='right')
        zoom_entry.pack(side='right')
        slider.pack(side='right', padx=10)
        slider.set(zoom)
        zoom_entry.insert(0, zoom)

        win.make_btn('Default', lambda: set_zoom('default'))
        win.make_btn('OK', set_zoom)
        win.make_btn('Cancel', lambda: self.close_window(title))
        self.add_to_bindtags([win, slider, zoom_entry], 'zoom')
        self.bind_class('zoom','<Return>', set_zoom)
        self.focus = zoom_entry
        self.focus.focus_set()

    # Options menu methods.
    def update_settings(self):
        self.drag_select = self.drag_select_var.get()

    # Help menu methods.
    def show_text(self, filename, width=80, height=24):
        if self.block_windows:
            self.focus.focus_set()
            return
        # Use Scrolledtext widget?
        title = filename.capitalize()
        win = Window(self, title)
        scrollbar = tk.Scrollbar(win.mainframe)
        scrollbar.pack(side='right', fill='y')
        text = tk.Text(win.mainframe, width=width, height=height, wrap='word',
            yscrollcommand=scrollbar.set)
        text.pack()
        scrollbar.config(command=text.yview)
        if exists(join(direcs['files'], filename + '.txt')):
            with open(join(direcs['files'], filename + '.txt'), 'r') as f:
                text.insert('end', f.read())
        text.config(state='disabled')
        win.make_btn('OK', lambda: self.close_window(title))
        self.focus = text
        self.focus.focus_set()



class TestGui(BasicGui):
    def __init__(self, **kwargs):
        super(TestGui, self).__init__(**kwargs)

    # Button actions.
    def left_press(self, coord):
        super(TestGui, self).left_press(coord)
        b = self.buttons[coord]
        if self.drag_select:
            if b.state == UNCLICKED:
                self.click(coord)
        else:
            if b.state == UNCLICKED:
                b.bg = self.set_cell_image(coord, self.bg_images['down'])

    def left_release(self, coord):
        super(TestGui, self).left_release(coord)
        b = self.buttons[coord]
        if b.state == UNCLICKED: #catches the case drag_select is on
            self.click(coord)

    def left_motion(self, coord, prev_coord):
        super(TestGui, self).left_motion(coord, prev_coord)
        if prev_coord and self.buttons[prev_coord].state == UNCLICKED:
            self.buttons[prev_coord].refresh()
        if coord:
            self.left_press(coord)

    def right_press(self, coord):
        super(TestGui, self).right_press(coord)
        b = self.buttons[coord]

        # Check whether drag-clicking should flag or unflag if drag is on.
        if self.drag_select:
            if b.state == UNCLICKED:
                self.drag_flag = FLAG
            elif b.state == FLAGGED and self.per_cell == 1:
                self.drag_flag = UNFLAG
            else:
                self.drag_flag = None
        else:
            self.drag_flag = None

        if b.state == UNCLICKED:
            b.fg = self.set_cell_image(coord, self.flag_images[1])
            b.state = FLAGGED
            b.num_of_flags = 1
        elif b.state == FLAGGED:
            self.board.delete(b.fg)
            b.fg = None
            b.state = UNCLICKED
            b.num_of_flags = 0

    def right_motion(self, coord, prev_coord):
        super(TestGui, self).right_motion(coord, prev_coord)
        # Do nothing if leaving the board.
        if not coord:
            return
        b = self.buttons[coord]
        # If the window was left, stop drag flagging. Could be altered to allow
        # cursor to go over the frame.
        # if not prev_coord:
        #     self.drag_flag = None
        # Flag or unflag as appropriate.
        if self.drag_flag == FLAG and b.state == UNCLICKED:
            b.fg = self.set_cell_image(coord, self.flag_images[1])
            b.state = FLAGGED
            b.num_of_flags = 1
        elif self.drag_flag == UNFLAG and b.state == FLAGGED:
            b.refresh()
            b.state = UNCLICKED
            b.num_of_flags = 0

    def both_press(self, coord):
        super(TestGui, self).both_press(coord)
        # Buttons which neighbour the current selected button.
        new_nbrs = self.get_nbrs(coord, include=True)
        # Only consider unclicked cells.
        new_nbrs = {c for c in new_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Sink the new neighbouring buttons.
        for c in new_nbrs:
            self.buttons[c].bg = self.set_cell_image(c,
                self.bg_images['down'])

    def both_release(self, coord):
        super(TestGui, self).both_release(coord)
        # Buttons which neighbour the previously selected button.
        old_nbrs = self.get_nbrs(coord, include=True)
        # Only worry about unclicked cells.
        old_nbrs = {c for c in old_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Raise the old neighbouring buttons.
        for c in old_nbrs:
            self.buttons[c].refresh()

    def both_motion(self, coord, prev_coord):
        super(TestGui, self).both_motion(coord, prev_coord)
        if prev_coord:
            # Buttons which neighbour the previously selected button.
            old_nbrs = self.get_nbrs(prev_coord, include=True)
            # Only worry about unclicked cells.
            old_nbrs = {c for c in old_nbrs
                if self.buttons[c].state == UNCLICKED}
            # Raise the old neighbouring buttons.
            for c in old_nbrs:
                self.buttons[c].refresh()
        if coord:
            self.both_press(coord)

    def click(self, coord):
        b = self.buttons[coord]
        b.bg = self.set_cell_image(coord, self.bg_images['down'])
        b.fg = self.set_cell_image(coord, self.mine_images[1])
        b.state = CLICKED



class MenuBar(tk.Menu, object):
    def __init__(self, parent):
        super(MenuBar, self).__init__(parent)
        self.parent = parent
        self.game_menu = tk.Menu(self)
        self.opts_menu = tk.Menu(self)
        self.help_menu = tk.Menu(self)
        self.add_cascade(label='Game', menu=self.game_menu)
        self.add_cascade(label='Options', menu=self.opts_menu)
        self.add_cascade(label='Help', menu=self.help_menu)
        self.game_items = []
        self.opts_items = []
        self.help_items = []

    def add_item(self, menu_, typ, label=None, index='end', **kwargs):
        items = getattr(self, menu_ + '_items')
        menu_ = getattr(self, menu_ + '_menu')
        if type(index) is int and index < 0:
            index += len(items)
        menu_.insert(index, typ, label=label, **kwargs)
        if index == 'end':
            items.append(label)
        else:
            items.insert(index, label)

    def del_item(self, menu, index):
        menu = getattr(self, menu + '_menu')
        items = getattr(self, menu + '_items')
        menu.delete(index)
        if index == 'end':
            items.pop(index)



class Cell(object):
    def __init__(self, coord, root):
        self.coord = coord
        self.root = root
        self.board = root.board
        self.state = UNCLICKED
        self.num_of_flags = 0
        self.mines = 0 #flags or mines revealed
        self.nr = None
        self.bg = None
        self.fg = None
        self.text = None

    def refresh(self, del_imgs=True):
        if del_imgs:
            self.board.delete(self.bg)
            self.board.delete(self.fg)
            self.board.delete(self.text)
        self.bg = self.fg = self.text = None
        self.state = UNCLICKED
        self.num_of_flags = 0
        self.mines = 0
        self.nr = None

    def incr_flags(self):
        if self.fg:
            self.board.delete(self.fg)
        self.num_of_flags += 1
        self.fg = self.root.set_cell_image(self.coord,
            self.root.flag_images[self.num_of_flags])
        self.state = FLAGGED
        self.mines = self.num_of_flags



class Window(tk.Toplevel, object):
    def __init__(self, parent, title):
        self.parent = parent
        super(Window, self).__init__(parent)
        self.title(title)
        parent.track_window(self)
        self.mainframe = tk.Frame(self)
        self.mainframe.pack(ipadx=10, ipady=10)
        self.lowframe = tk.Frame(self)
        self.lowframe.pack(padx=10, pady=10)
        self.btns = []

    def make_btn(self, text, cmd):
        btn = tk.Button(self.lowframe, text=text, command=cmd)
        btn.pack(side='left', padx=10)
        btn.bind('<Return>', lambda x: btn.invoke())
        self.btns.append(btn)
        return btn



if __name__ == '__main__':
    t = TestGui()
    t.mainloop()