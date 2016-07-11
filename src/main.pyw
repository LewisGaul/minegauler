
# Button states are:
#     UNCLICKED
#     CLICKED
#     FLAGGED
#     MINE
#     COLOURED

# Drag-and-select flagging types are:
#     FLAG
#     UNFLAG

import sys
import os
from os.path import join, dirname, exists, split, splitext, getsize, isdir
from shutil import copy2 as copy_file
import Tkinter as tk
import tkFileDialog, tkMessageBox
from PIL import Image as PILImage, ImageTk
import time as tm
import json
from glob import glob
import threading

import numpy as np

from constants import * #version, platform etc.
from resources import direcs, blend_colours
from game import Game

if PLATFORM == 'win32':
    import win32com.client
# Use platform to determine which button is right-click.
RIGHT_BTN_NUM = 2 if PLATFORM == 'darwin' else 3

__version__ = VERSION

default_settings = {
    'diff': 'b',
    'dims': (8, 8),
    'mines': 10,
    'first_success': True,
    'lives': 1,
    'per_cell': 1,
    'detection': 1,
    'drag_select': False,
    'distance_to': False,
    'button_size': 16, #pixels
    'name': ''
    }

nr_mines = {
    'b': {
        0.5: 10, 1: 10, 1.5: 8, 1.8: 7, 2: 6,
        2.2: 5, 2.5: 5, 2.8: 4, 3: 4
        },
    'i': {
        0.5: 40, 1: 40, 1.5: 30, 1.8: 25,
        2: 25, 2.2: 20, 2.5: 18, 2.8: 16, 3: 16
        },
    'e': {
        0.5: 99, 1: 99, 1.5: 80, 1.8: 65,
        2: 60, 2.2: 50, 2.5: 45, 2.8: 40, 3: 40
        },
    'm': {
        0.5: 200, 1: 200, 1.5: 170, 1.8: 160,
        2: 150, 2.2: 135, 2.5: 110, 2.8: 100, 3: 100
        }
    }
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
detection_options = dict(
    [(str(i), i) for i in[0.5, 1, 1.5, 1.8, 2, 2.2, 2.5, 2.8, 3]])

bg_colours = {
    '': (240, 240, 237), #button grey
   'red':  (255,   0,   0),
   'blue': (128, 128, 255)
   }
nr_font = ('Tahoma', 9, 'bold')
msg_font = ('Times', 10, 'bold')



class BasicGui(tk.Tk, object):
    def __init__(self, settings=None):
        # Defaults which may be overwritten below.
        self.settings = {
            'diff': 'b',
            'per_cell': 1,
            'detection': 1,
            'drag_select': False,
            'distance_to': False,
            'button_size': 16, #pixels
            }
        if settings == None:
            settings = dict()
        # Force standard settings (basic version).
        settings['per_cell'] = 1
        settings['detection'] = 1
        # Overwrite with any given settings.
        for k, v in settings.items():
            self.settings[k] = v
        # Store each setting as an attribute of the class.
        for k, v in self.settings.items():
            setattr(self, k, v)
        # Check if custom.
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
        self.iconbitmap(default=join(direcs['images'], '3mine.ico'))
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

        # Make main body of GUI.
        self.make_panel()
        self.make_minefield()
        # t = tm.time()
        self.get_images()
        # print "Time to get images was {:.2f}s.".format(tm.time() - t)

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

    def run(self):
        """
        Final method to finish off any bits that are unique to the class
        before running the app with mainloop. Every subclass should have its
        own run method.
        """
        # Create menubar.
        self.menubar = MenuBar(self)
        self.config(menu=self.menubar)
        self.mainloop()

    # Make the GUI.
    def make_panel(self):
        self.panel = tk.Frame(self, pady=4, height=40)
        self.panel.pack(fill='both')
        self.face_images = dict()
        # Collect all faces that are in the folder and store in dictionary
        # under filename.
        for path in glob(join(direcs['images'], 'faces', '*.ppm')):
            im_name = splitext(split(path)[1])[0]
            self.face_images[im_name] = tk.PhotoImage(name=im_name,
                file=join(direcs['images'], 'faces', im_name + '.ppm'))
        face_frame = tk.Frame(self.panel)
        face_frame.place(relx=0.5, rely=0.5, anchor='center')
        # Create face button which will refresh the board.
        self.face_button = tk.Button(face_frame, bd=4, takefocus=False,
            image=self.face_images['ready1face'], command=self.refresh)
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

    def make_minefield(self):
        self.mainframe = tk.Frame(self, bd=10, relief='ridge')
        self.mainframe.pack()
        self.buttons = dict()
        for coord in self.all_coords:
            self.buttons[coord] = Cell(coord, self.mainframe, self)
        self.set_button_bindings()

    def set_button_bindings(self):
        self.bind_class('board', '<Button-1>', self.detect_left_press)
        self.bind_class('board', '<ButtonRelease-1>', self.detect_left_release)
        self.bind_class('board', '<Button-%s>'%RIGHT_BTN_NUM, self.detect_right_press)
        self.bind_class('board', '<ButtonRelease-%s>'%RIGHT_BTN_NUM,
            self.detect_right_release)
        self.bind_class('board', '<B1-Motion>', self.detect_motion)
        self.bind_class('board', '<B%s-Motion>'%RIGHT_BTN_NUM, self.detect_motion)
        self.bind_class('board', '<Control-1>', self.detect_ctrl_left_press)

    def unset_button_bindings(self):
        self.unbind_class('board', '<Button-1>')
        self.unbind_class('board', '<ButtonRelease-1>')
        self.unbind_class('board', '<Button-%s>'%RIGHT_BTN_NUM)
        self.unbind_class('board', '<ButtonRelease-%s>'%RIGHT_BTN_NUM)
        self.unbind_class('board', '<B1-Motion>')
        self.unbind_class('board', '<B%s-Motion>'%RIGHT_BTN_NUM)
        self.unbind_class('board', '<Control-1>')

    def get_images(self):
        # Create the .ppm files from the .png file. Should use zoom method on
        # tk.PhotoImage?...
        im_size = self.button_size - 2
        im_path = join(direcs['images'], 'mines')
        self.mine_images = dict()
        for c in bg_colours:
            n = 1
            im_name = '%s%smine' % (c, n)
            im = PILImage.open(join(im_path, '%smine.png'%n))
            data = np.array(im)
            data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
                list(bg_colours[c]) + [0])
            im = PILImage.fromarray(data, mode='RGBA').convert('RGB')
            im = im.resize(tuple([im_size]*2), PILImage.ANTIALIAS)
            im_tk = ImageTk.PhotoImage(im, name=im_name)
            if not c:
                key = n
            else:
                key = (c, n)
            self.mine_images[key] = im_tk

        im_size = self.button_size - 6
        im_path = join(direcs['images'], 'flags')
        self.flag_images = dict()
        n = 1
        im_name = '%sflag' % n
        im = PILImage.open(join(im_path, '%sflag.png'%n))
        data = np.array(im)
        data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
            list(bg_colours['']) + [0])
        im = PILImage.fromarray(data, mode='RGBA').convert('RGB')
        im = im.resize(tuple([im_size]*2), PILImage.ANTIALIAS)
        im_tk = ImageTk.PhotoImage(im, name=im_name)
        self.flag_images[n] = im_tk

    # Button actions.
    def detect_left_press(self, event=None):
        self.left_button_down = True
        if self.right_button_down:
            self.both_press(self.mouse_coord)
        else:
            self.mouse_coord = event.widget.coord
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
            self.mouse_coord = event.widget.coord
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
        orig_coord = event.widget.coord
        x = orig_coord[0] + event.y/self.button_size
        y = orig_coord[1] + event.x/self.button_size
        cur_coord = (x, y) if (x, y) in self.all_coords else None
        if cur_coord == self.mouse_coord:
            return
        if self.left_button_down:
            if self.right_button_down: #both
                self.both_motion(cur_coord, self.mouse_coord)
            elif not self.is_both_click or self.drag_select: #left
                self.left_motion(cur_coord, self.mouse_coord)
        elif not self.is_both_click: #right
            self.right_motion(cur_coord, self.mouse_coord)
        self.mouse_coord = cur_coord

    def detect_ctrl_left_press(self, event=None):
        coord = event.widget.coord
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
    def refresh(self, event=None):
        for b in [self.buttons[c] for c in self.all_coords
            if self.buttons[c].state != UNCLICKED]:
            self.reset_button(b.coord)
            b.state = UNCLICKED
        self.update_settings()
        self.set_button_bindings()
        self.left_button_down = self.right_button_down = False
        self.mouse_coord = None
        self.is_both_click = False

    def reset_button(self, coord):
        b = self.buttons[coord]
        b.config(bd=3, relief='raised', bg='SystemButtonFace',
            fg='black', font=self.nr_font, text='', image='')
        b.state = UNCLICKED
        b.num_of_flags = 0

    def show_info(self, event=None):
        title = 'Info'
        self.focus = win = self.active_windows[title] = tk.Toplevel(self)
        self.focus.focus_set()
        win.title(title)
        win.protocol('WM_DELETE_WINDOW', lambda: self.close_window(title))
        info = ""
        tk.Label(win, text=info, font=('Times', 10, 'bold')).pack()

    def close_root(self):
        with open(join(direcs['main'], 'settings.cfg'), 'w') as f:
            json.dump(self.settings, f)
            # print "Saved settings."
            self.destroy()

    def track_window(self, win):
        title = win.title()
        self.active_windows[title] = win
        win.protocol('WM_DELETE_WINDOW', lambda: self.close_window(title))
        self.block_windows = True

    def close_window(self, name):
        """
        Keep track of the windows which are open, and set the focus as
        appropriate.
        """
        self.active_windows[name].destroy()
        self.active_windows.pop(name)
        self.block_windows = False
        self.focus = self
        self.focus.focus_set()

    # Game menu methods.
    def set_difficulty(self):
        if self.diff_var.get() in diff_dims: #standard board
            self.diff = self.diff_var.get()
            self.mines = nr_mines[self.diff][self.detection]
            self.reshape(diff_dims[self.diff])
        else: #custom, open popup window
            # Don't change the radiobutton until custom is confirmed.
            self.diff_var.set(self.diff)
            if not self.block_windows:
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
            new_max = rows*cols/3
            mine_slider.set(new_max*float(mine_slider.get())/old_max)
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
            if (rows not in map(str, range(2, 101)) or
                cols not in map(str, range(2, 201))):
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
            # Check if this is really custom.
            if (dims in diff_dims and
                mines==nr_mines[diff_dims[dims]][self.detection]):
                self.diff = diff_dims[dims]
                self.diff_var.set(self.diff)
            else:
                self.diff = 'c'
                self.diff_var.set('c')

        title = 'Custom'
        win = Window(self, title)
        tk.Message(win.mainframe, width=200, text="""\
            Select the desired number of rows, columns and mines.\
            The number of mines must be less than the size of the board,\
            and the size of the board must be less than 100x200.\
            """).pack(pady=10)
        entry_frame = tk.Frame(win.mainframe)
        entry_frame.pack()
        row_slider = tk.Scale(entry_frame, from_=2, to=100, length=140,
            orient='horizontal', showvalue=False, takefocus=False,
            command=size_slide)
        col_slider = tk.Scale(entry_frame, from_=2, to=100, length=140,
            orient='horizontal', showvalue=False, takefocus=False,
            command=size_slide)
        mine_slider = tk.Scale(entry_frame, from_=1, to=self.get_size()/3,
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
        # This runs if one of the dimensions was previously larger.
        extras = [c for c in self.all_coords if c[0] >= dims[0] or
            c[1] >= dims[1]]
        for coord in extras:
            self.buttons[coord].frame.destroy()
            self.buttons.pop(coord)
        # This runs if one of the dimensions of the new shape is larger than
        # the previous.
        self.all_coords = [(i, j) for i in range(dims[0])
            for j in range(dims[1])]
        new = [c for c in self.all_coords if c[0] >= self.dims[0] or
            c[1] >= self.dims[1]]
        for coord in new:
            self.buttons[coord] = Cell(coord, self.mainframe, self)
        self.dims = dims
        self.refresh()

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
            if self.button_size == 16:
                self.zoom_var.set(False)
            else:
                self.zoom_var.set(True)
            if old_button_size != self.button_size:
                self.nr_font = (self.nr_font[0], 10*self.button_size/17,
                    self.nr_font[2])
                for b in self.buttons.values():
                    #Update frame sizes.
                    b.frame.config(height=self.button_size,
                        width=self.button_size)
                    b.config(font=self.nr_font)
                self.get_images()
            self.close_window(title)

        # Ensure tick on radiobutton is correct.
        if self.button_size == 16:
            self.zoom_var.set(False)
        else:
            self.zoom_var.set(True)
        if self.block_windows:
            return
        title = 'Zoom'
        win = Window(self, title)
        tk.Message(win.mainframe, width=180,
            text="""Select the desired increase in button size compared to the\
                default, which should be an integer from 60 to 500.""").pack(
                pady=10)
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
        # Use Scrolledtext widget?
        win = self.active_windows[filename] = tk.Toplevel(self)
        win.title(filename.capitalize())
        scrollbar = Scrollbar(win)
        scrollbar.pack(side='right', fill=Y)
        self.focus = text = Text(win, width=width, height=height, wrap=WORD,
            yscrollcommand=scrollbar.set)
        text.pack()
        scrollbar.config(command=text.yview)
        if exists(join(direcs['files'], filename + '.txt')):
            with open(join(direcs['files'], filename + '.txt'), 'r') as f:
                text.insert(END, f.read())
        text.config(state='disabled')
        self.focus.focus_set()



class TestGui(BasicGui):
    def __init__(self):
        super(TestGui, self).__init__()

    # Button actions.
    def left_press(self, coord):
        super(TestGui, self).left_press(coord)
        b = self.buttons[coord]
        if self.drag_select:
            if b.state == UNCLICKED:
                self.click(coord)
        else:
            if b.state == UNCLICKED:
                b.config(bd=1, relief='sunken')

    def left_release(self, coord):
        super(TestGui, self).left_release(coord)
        b = self.buttons[coord]
        if b.state == UNCLICKED: #catches the case drag_select is on
            self.click(coord)

    def left_motion(self, coord, prev_coord):
        super(TestGui, self).left_motion(coord, prev_coord)
        if prev_coord and self.buttons[prev_coord].state == UNCLICKED:
            self.reset_button(prev_coord) #does more than necessary
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
            b.config(image=self.flag_images[1])
            b.state = FLAGGED
            b.num_of_flags = 1
        elif b.state == FLAGGED:
            if b.num_of_flags == self.per_cell:
                b.config(image='')
                b.state = UNCLICKED
                b.num_of_flags = 0
            else:
                b.config(image=self.flag_images[b.num_of_flags+1])
                b.num_of_flags += 1

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
            b.config(image=self.flag_images[1])
            b.state = FLAGGED
            b.num_of_flags = 1
        elif self.drag_flag == UNFLAG and b.state == FLAGGED:
            b.config(image='')
            b.state = UNCLICKED
            b.num_of_flags = 0

    def both_press(self, coord):
        super(TestGui, self).both_press(coord)
        # Buttons which neighbour the current selected button.
        new_nbrs = self.get_nbrs(coord, include=True)
        # Only consider unclicked cells.
        new_nbrs = {self.buttons[c] for c in new_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Sink the new neighbouring buttons.
        for b in new_nbrs:
            b.config(bd=1, relief='sunken')

    def both_release(self, coord):
        super(TestGui, self).both_release(coord)
        # Buttons which neighbour the previously selected button.
        old_nbrs = self.get_nbrs(coord, include=True)
        # Only worry about unclicked cells.
        old_nbrs = {self.buttons[c] for c in old_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Raise the old neighbouring buttons.
        for b in old_nbrs:
            b.config(bd=3, relief='raised', text='.')

    def both_motion(self, coord, prev_coord):
        super(TestGui, self).both_motion(coord, prev_coord)
        if prev_coord:
            # Buttons which neighbour the previously selected button.
            old_nbrs = self.get_nbrs(prev_coord, include=True)
            # Only worry about unclicked cells.
            old_nbrs = {self.buttons[c] for c in old_nbrs
                if self.buttons[c].state == UNCLICKED}
            # Raise the old neighbouring buttons.
            for b in old_nbrs:
                b.config(bd=3, relief='raised')
        if coord:
            self.both_press(coord)

    def click(self, coord):
        b = self.buttons[coord]
        b.config(bd=1, relief='sunken', text='!')
        b.state = CLICKED



class GameGui(BasicGui):
    def __init__(self, settings=None):
        super(GameGui, self).__init__(settings)
        # Set variables.
        self.first_success_var = tk.BooleanVar()
        self.first_success_var.set(self.first_success)
        self.hide_timer = False
        # Create a minefield stored within the game.
        self.refresh()

    def run(self):
        # Create menubar.
        self.menubar = MenuBar(self, 'full')
        self.config(menu=self.menubar)
        self.mainloop()

    # Make the GUI.
    def make_panel(self):
        super(GameGui, self).make_panel()
        # Create and place the mines counter.
        self.mines_var = tk.StringVar()
        self.mines_label = tk.Label(self.panel, bg='black', fg='red', bd=5,
            relief='sunken', font=('Verdana',11,'bold'),
            textvariable=self.mines_var)
        self.mines_label.place(x=7, rely=0.5, anchor='w')
        self.add_to_bindtags(self.mines_label, 'panel')

        # Create and place the timer.
        self.timer = Timer(self.panel)
        self.timer.place(relx=1, x=-7, rely=0.5, anchor='e')
        self.timer.bind('<Button-%s>'%RIGHT_BTN_NUM, self.toggle_timer)
        self.add_to_bindtags(self.timer, 'panel')

    # Button actions.
    def left_press(self, coord):
        super(GameGui, self).left_press(coord)
        b = self.buttons[coord]
        self.face_button.config(image=self.face_images['active1face'])
        if self.drag_select:
            if b.state == UNCLICKED:
                self.click(coord)
        else:
            if b.state == UNCLICKED:
                b.config(bd=1, relief='sunken')

    def left_release(self, coord):
        super(GameGui, self).left_release(coord)
        b = self.buttons[coord]
        if b.state == UNCLICKED: #catches the case drag_select is on
            self.click(coord)
        if self.game.state in [READY, ACTIVE]:
            self.face_button.config(image=self.face_images['ready1face'])

    def left_motion(self, coord, prev_coord):
        super(GameGui, self).left_motion(coord, prev_coord)
        if prev_coord and self.buttons[prev_coord].state == UNCLICKED:
            self.reset_button(prev_coord) #does more than necessary
        if coord:
            self.left_press(coord)

    def right_press(self, coord):
        super(GameGui, self).right_press(coord)
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
            b.config(image=self.flag_images[1])
            b.state = FLAGGED
            b.num_of_flags = 1
        elif b.state == FLAGGED:
            if b.num_of_flags == self.per_cell:
                b.config(image='')
                b.state = UNCLICKED
                b.num_of_flags = 0
            else:
                b.config(image=self.flag_images[b.num_of_flags+1])
                b.num_of_flags += 1
        self.set_mines_counter()

    def right_motion(self, coord, prev_coord):
        super(GameGui, self).right_motion(coord, prev_coord)
        # Do nothing if leaving the board.
        if not coord:
            return
        b = self.buttons[coord]
        if self.drag_flag == FLAG and b.state == UNCLICKED:
            b.config(image=self.flag_images[1])
            b.state = FLAGGED
            b.num_of_flags = 1
        elif self.drag_flag == UNFLAG and b.state == FLAGGED:
            b.config(image='')
            b.state = UNCLICKED
            b.num_of_flags = 0
        self.set_mines_counter()

    def both_press(self, coord):
        super(GameGui, self).both_press(coord)
        self.face_button.config(image=self.face_images['active1face'])
        # Buttons which neighbour the current selected button.
        new_nbrs = self.get_nbrs(coord, include=True)
        # Only consider unclicked cells.
        new_nbrs = {self.buttons[c] for c in new_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Sink the new neighbouring buttons.
        for b in new_nbrs:
            b.config(bd=1, relief='sunken')

    def both_release(self, coord):
        super(GameGui, self).both_release(coord)
        # Buttons which neighbour the previously selected button.
        nbrs = self.get_nbrs(coord, include=True)
        grid_nr = self.game.grid[coord]
        if grid_nr > 0: #potential chording
            nbr_mines = sum([self.buttons[c].num_of_flags for c in nbrs])
            if nbr_mines == grid_nr:
                for coord in {c for c in nbrs
                    if self.buttons[c].state == UNCLICKED}:
                    self.click(coord, check_for_win=False)
                if np.array_equal(
                    self.game.mf.completed_grid>=0, self.game.grid>=0):
                    self.finalise_win()
        # Reset buttons if not clicked.
        for b in {self.buttons[c] for c in nbrs if
            self.buttons[c].state == UNCLICKED}:
            b.config(bd=3, relief='raised')
        # Reset face.
        if (self.game.state in [READY, ACTIVE] and
            not (self.left_button_down and self.drag_select)):
            self.face_button.config(image=self.face_images['ready1face'])

    def both_motion(self, coord, prev_coord):
        super(GameGui, self).both_motion(coord, prev_coord)
        if prev_coord:
            # Buttons which neighbour the previously selected button.
            old_nbrs = self.get_nbrs(prev_coord, include=True)
            # Only worry about unclicked cells.
            old_nbrs = {self.buttons[c] for c in old_nbrs
                if self.buttons[c].state == UNCLICKED}
            # Raise the old neighbouring buttons.
            for b in old_nbrs:
                b.config(bd=3, relief='raised')
        if coord:
            self.both_press(coord)

    # GUI and game methods.
    def click(self, coord, check_for_win=True):
        b = self.buttons[coord]
        if self.game.state == READY:
            if self.first_success and self.game.mf.origin != KNOWN:
                self.game.mf.generate_rnd(open_coord=coord)
                self.game.mf.setup()
            elif self.game.mf.mines_grid is None:
                self.game.mf.generate_rnd()
                self.game.mf.setup()
            self.game.state = ACTIVE
            self.game.start_time = tm.time()
            self.timer.update(self.game.start_time)

        cell_nr = self.game.mf.completed_grid[coord]
        # Check if the cell clicked is an opening, safe or a mine.
        if cell_nr == 0: #opening hit
            # Find which opening has been hit.
            for opening in self.game.mf.openings:
                if coord in opening:
                    break # Work with this set of coords
            for c in [c1 for c1 in opening if
                self.buttons[c1].state == UNCLICKED]:
                self.reveal_safe_cell(c)
        elif cell_nr > 0: #normal success
            self.reveal_safe_cell(coord)
        else: #mine hit, game over
            self.finalise_loss(coord)
            return #don't check for completion
        # We hold off from checking for a win if chording has been used.
        if (check_for_win and
            np.array_equal(self.game.mf.completed_grid>=0, self.game.grid>=0)):
            self.finalise_win()

    def reveal_safe_cell(self, coord):
        b = self.buttons[coord]
        nr = self.game.mf.completed_grid[coord]
        # Assign the game grid with the numbers which are uncovered.
        self.game.grid.itemset(coord, nr)
        b.state = CLICKED
        # Display the number unless it is a zero.
        text = nr if nr else ''
        try:
            nr_colour = NR_COLOURS[nr]
        except KeyError:
            # In case the number is unusually high.
            nr_colour = 'black'
        b.config(bd=1, relief='sunken', #bg='SystemButtonFace',
            text=text, fg=nr_colour, font=self.nr_font)

    def finalise_win(self):
        self.game.finish_time = tm.time()
        self.unset_button_bindings()
        self.timer.start_time = None
        self.game.state = WON
        self.face_button.config(image=self.face_images['won1face'])
        for btn in [b for b in self.buttons.values()
            if b.state in [UNCLICKED, FLAGGED]]:
            n = self.game.mf.mines_grid[btn.coord]
            btn.config(image=self.flag_images[n])
            btn.state = FLAGGED
            btn.num_of_flags = n
        self.timer.set_var(min(int(self.game.get_time_passed() + 1), 999))
        self.timer.config(fg='red')
        self.set_mines_counter()

    def finalise_loss(self, coord):
        self.game.finish_time = tm.time()
        self.unset_button_bindings()
        self.timer.start_time = None
        b = self.buttons[coord]
        b.state = MINE
        self.game.state = LOST
        colour = self.get_tk_colour(bg_colours['red'])
        b.config(bd=1, relief='sunken', bg=colour,
            image=self.mine_images[('red', 1)])
        self.face_button.config(image=self.face_images['lost1face'])
        for c, b in [(btn.coord, btn) for btn in self.buttons.values()
            if btn.state != CLICKED]:
            # Check for incorrect flags.
            if b.state == FLAGGED and self.game.mf.mines_grid[c] == 0:
                # Could use an image here..
                b.config(text='X', image='', font=self.nr_font)
            # Reveal remaining mines.
            elif b.state == UNCLICKED and self.game.mf.mines_grid[c] > 0:
                b.state = MINE
                b.config(bd=1, relief='sunken',
                    image=self.mine_images[self.game.mf.mines_grid[c]])
        self.timer.set_var(min(int(self.game.get_time_passed() + 1), 999))
        self.timer.config(fg='red')

    def set_mines_counter(self):
        nr_found = sum([b.num_of_flags for b in self.buttons.values()])
        nr_rem = self.mines - nr_found
        self.mines_var.set("{:03d}".format(abs(nr_rem)))
        if nr_rem < 0:
            self.mines_label.config(bg='red', fg='black')
        else:
            self.mines_label.config(bg='black', fg='red')

    def refresh(self, event=None, is_replay=False):
        super(GameGui, self).refresh()
        self.timer.start_time = None
        self.timer.set_var(0)
        self.face_button.config(image=self.face_images['ready1face'])
        if is_replay:
            self.game = Game(self.settings, self.game.mf)
        else:
            self.game = Game(self.settings)
        self.set_mines_counter()
        if self.hide_timer:
            self.timer.config(fg='black')

    def toggle_timer(self, event=None):
        if event:
            self.hide_timer = not(self.hide_timer)
        # Always show the timer if the game is lost or won.
        if self.hide_timer and self.game.state not in [WON, LOST]:
            self.timer.config(fg='black')
        else:
            self.timer.config(fg='red')

    # Game menu methods.
    def save_board(self):
        pass

    def load_board(self):
        pass

    # Options menu methods.
    def update_settings(self):
        self.first_success = self.first_success_var.get()
        self.drag_select = self.drag_select_var.get()
        for k in default_settings:
            self.settings[k] = getattr(self, k)



class MenuBar(tk.Menu, object):
    def __init__(self, parent, config='basic'):
        super(MenuBar, self).__init__(parent)
        self.parent = parent
        self.config = config
        self.make_game_menu()
        self.make_options_menu()
        self.make_help_menu()

    def make_game_menu(self):
        self.g_menu = tk.Menu(self)
        self.add_cascade(label='Game', menu=self.g_menu)

        self.g_menu.add_command(label='New',
            command=self.parent.refresh, accelerator='F2')
        self.parent.bind('<F2>', self.parent.refresh)
        if self.config == 'full':
            self.g_menu.add_command(label='Replay',
                command=lambda: self.parent.refresh(is_replay=True))
            self.g_menu.add_command(label='Save board',
                command=self.parent.save_board)
            self.g_menu.add_command(label='Load board',
                command=self.parent.load_board)
        self.g_menu.add_separator()
        for i in diff_names:
            self.g_menu.add_radiobutton(label=i[1], value=i[0],
                variable=self.parent.diff_var, command=self.parent.set_difficulty)
        self.g_menu.add_separator()
        self.g_menu.add_checkbutton(label='Zoom', variable=self.parent.zoom_var,
            command=self.parent.get_zoom)
        self.g_menu.add_separator()
        self.g_menu.add_command(label='Exit', command=self.parent.destroy)

    def make_options_menu(self):
        self.o_menu = tk.Menu(self)
        self.add_cascade(label='Options', menu=self.o_menu)

        if self.config == 'full':
            self.o_menu.add_checkbutton(label='FirstAuto',
                variable=self.parent.first_success_var,
                command=self.parent.update_settings)
        self.o_menu.add_checkbutton(label='Drag select',
            variable=self.parent.drag_select_var,
            command=self.parent.update_settings)

    def make_help_menu(self):
        self.h_menu = tk.Menu(self)
        self.add_cascade(label='Help', menu=self.h_menu)
        self.h_menu.add_command(label='About',
            command=lambda: self.parent.show_text('about', 40, 5), accelerator='F1')
        self.bind_all('<F1>', lambda: self.parent.show_text('about', 40, 5))

    def set_to_official(self):
        pass



class Cell(tk.Label, object):
    def __init__(self, coord, parent, model):
        """Automatically pack the created cell."""
        self.coord = coord
        self.parent = parent
        self.model = model
        self.state = UNCLICKED
        self.num_of_flags = 0
        # Initialise a frame of correct size to contain a button.
        self.frame = tk.Frame(parent, width=model.button_size,
            height=model.button_size)
        self.frame.rowconfigure(0, weight=1) #enable button to fill frame
        self.frame.columnconfigure(0, weight=1)
        self.frame.grid_propagate(False) #disable resizing of frame
        # Place with the grid packer.
        self.frame.grid(row=coord[0], column=coord[1])
        super(Cell, self).__init__(self.frame, bd=3, relief='raised',
            font=model.nr_font)
        self.grid(sticky='nsew')
        self.bindtags(('board',) + self.bindtags())



class Timer(tk.Label, object):
    def __init__(self, parent):
        self.var = tk.StringVar()
        self.set_var(0)
        super(Timer, self).__init__(parent, bg='black', fg='red', bd=5, relief='sunken',
            font=('Verdana',11,'bold'), textvariable=self.var)
        self.start_time = None

    def __repr__(self):
        return "<Timer object inheriting from Tkinter.Label>"

    def update(self, start_time=None):
        # A start time is passed in if Timer is being started.
        if start_time:
            self.start_time = start_time
        # Timer updates if it has been started. It is stopped by setting start_time=None.
        if self.start_time:
            elapsed = tm.time() - self.start_time
            self.var.set("%03d" % (min(elapsed + 1, 999)))
            self.after(100, self.update)

    def set_var(self, time):
        self.var.set('{:03d}'.format(time))



class Window(tk.Toplevel, object):
    def __init__(self, parent, title, **kwargs):
        # kwargs are used to check if the OK and Cancel buttons are desired.
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
    try:
        with open(join(direcs['main'], 'settings.cfg'), 'r') as f:
            settings = json.load(f)
        # print "Imported settings."
        #print "Imported settings: ", settings
    except:
        settings = default_settings
    # Check for corrupt info.txt file and ensure it contains the version.
    try:
        with open(join(direcs['files'], 'info.txt'), 'r') as f:
            json.load(f)['version']
    except:
        with open(join(direcs['files'], 'info.txt'), 'w') as f:
            json.dump({'version': VERSION}, f)
    # Create and run the GUI.
    GameGui(settings).run()