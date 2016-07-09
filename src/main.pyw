
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
from PIL import Image as PILImage
import time as tm
import json
from glob import glob

import numpy as np

from constants import * #version, platform etc.
from resources import nr_colours, direcs, get_neighbours, blend_colours
from game import Game
# import update_highscores
# from probabilities import NrConfig

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
        if self.diff in ['b', 'i', 'e', 'm']: # If difficulty is not custom
            self.dims = self.settings['dims'] = diff_dims[self.diff]

        self.all_coords = [(i, j) for i in range(self.dims[0])
            for j in range(self.dims[1])]

        # Dictionary to keep track of which windows are open.
        self.active_windows = dict()
        # Initialise the root window.
        super(BasicGui, self).__init__()
        self.focus = self.active_windows['root'] = self
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

        # Set size of root window.
        self.resizable(False, False)
        width = max(147, self.dims[1]*self.button_size + 20)
        height = self.dims[0]*self.button_size + self.panel['height'] + 20
        self.geometry('{}x{}'.format(width, height))
        # Turn off option of resizing window.

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
        # Create face button which will refresh_board the board.
        self.face_button = tk.Button(face_frame, bd=4,
            image=self.face_images['ready1face'], takefocus=False,
            command=self.refresh_board)
        self.face_button.pack()

        # Add bindtag to panel.
        self.panel.bindtags(('panel',) + self.panel.bindtags())
        # Bind to mouse click and release on panel.
        self.panel.bind_class('panel', '<Button-1>',
            lambda x: self.face_button.config(relief='sunken'))
        def panel_click(event):
            self.face_button.config(relief='raised')
            if (event.x > 0 and event.x < event.widget.winfo_width()
                and event.y > 0 and event.y < 40):
                self.face_button.invoke()
        self.panel.bind_class('panel', '<ButtonRelease-1>', panel_click)

    def make_minefield(self):
        self.board = tk.Frame(self, bd=10, relief='ridge')
        self.board.pack()
        self.buttons = dict()
        for coord in self.all_coords:
            self.buttons[coord] = Cell(coord, self.board, self)
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
        for n in range(1, 2):
            for colour in bg_colours:
                im = PILImage.open(join(im_path, '%smine.png'%n))
                data = np.array(im)
                data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
                    list(bg_colours[colour]) + [0])
                im = PILImage.fromarray(data, mode='RGBA').convert('RGB')
                im = im.resize(tuple([im_size]*2), PILImage.ANTIALIAS)
                im.close()
        self.mine_images = dict()
        for n in range(1, 2):
            for c in bg_colours:
                im_name = '%s%smine' % (c, n)
                if not c:
                    key = n
                else:
                    key = (c, n)
                self.mine_images[key] = tk.PhotoImage(name=im_name,
                    file=join(
                        im_path, '%s%smine%02d.ppm'%(c, n, im_size)))

        im_size = self.button_size - 6
        im_path = join(direcs['images'], 'flags')
        for n in range(1, 2):
            im = PILImage.open(join(im_path, '%sflag.png'%n))
            data = np.array(im)
            data[(data == (255, 255, 255, 0)).all(axis=-1)] = tuple(
                list(bg_colours['']) + [0])
            im = PILImage.fromarray(data, mode='RGBA').convert('RGB')
            im = im.resize(tuple([im_size]*2), PILImage.ANTIALIAS)
            im.close()
        self.flag_images = dict()
        for n in range(1, 2):
            im_name = '%sflag' % n
            self.flag_images[n] = tk.PhotoImage(name=im_name,
                file=join(im_path, '%sflag%02d.ppm'%(n, im_size)))

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
    def refresh_board(self, event=None):
        for b in [self.buttons[c] for c in self.all_coords
            if self.buttons[c].state != UNCLICKED]:
            self.reset_button(b.coord)
            b.state = UNCLICKED
        self.set_button_bindings()

    def reset_button(self, coord):
        b = self.buttons[coord]
        b.config(bd=3, relief='raised', bg='SystemButtonFace',
            fg='black', font=self.nr_font, text='', image='')
        b.state = UNCLICKED
        b.num_of_flags = 0

    def show_info(self, event=None):
        self.focus = window = self.active_windows['info'] = tk.Toplevel(self)
        self.focus.focus_set()
        window.title('Info')
        window.protocol('WM_DELETE_WINDOW', lambda: self.close_window('info'))
        info = ""
        tk.Label(window, text=info, font=('Times', 10, 'bold')).pack()

    def close_root(self):
        self.destroy()

    def close_window(self, window):
        self.active_windows[window].destroy()
        self.active_windows.pop(window)
        self.focus = self
        self.focus.focus_set()
        if window == 'highscores':
            with open(join(direcs['data'], 'datacopy.txt'), 'w') as f:
                json.dump(self.all_data, f)

    # Game menu methods.
    def set_difficulty(self):
        pass

    def set_zoom(self, event=None):
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
            self.geometry(
                '{}x{}'.format(self.width, self.height + 62))
            #Make the frames the right size.
            self.board.config(height=self.height, width=self.width)
            self.mainborder.config(height=self.height, width=self.width)
            self.zoomframe.config(height=100*self.button_size + 20,
                width=200*self.button_size + 20)
            for coord, frame in self.button_frames.items():
                #Update frame sizes.
                frame.config(height=self.button_size,
                    width=self.button_size)
            for button in [b for b in self.buttons.values()
                if b.state == SAFE]:
                button.config(font=self.nr_font)
            for button in [b for b in self.buttons.values()
                if b.state == COLOURED]:
                if self.button_size < 24 and len(button['text']) > 1:
                    button.config(text='')
                else:
                    prob = round(self.probs.item(coord), 5)
                    text = int(prob) if prob in [0, 1] else '%.2f'%round(
                        prob, 2)
                    button.config(fg='black', text=text, font=('Times',
                        int(0.2*self.button_size+3.7), 'normal'))
            self.get_images()
        if self.active_windows.has_key('zoom'):
            self.close_window('zoom')
    def get_zoom(self):
        self.submit_name_entry()
        if self.button_size == 16:
            self.zoom_var.set(False)
        else:
            self.zoom_var.set(True)
        if self.focus.bindtags()[1] == 'Entry':
            self.focus.focus_set()
            return
        window = self.active_windows['zoom'] = tk.Toplevel(self)
        window.title('Zoom')
        window.protocol('WM_DELETE_WINDOW', lambda: self.close_window('zoom'))
        Message(window, width=150, text="Enter desired button size in pixels or click 'Default'.").pack()
        scrollbar = Scrollbar(window, orient=HORIZONTAL)
        # scrollbar.pack(side='left', padx=10)
        self.focus = zoom_entry = Entry(window, width=5)
        zoom_entry.insert(0, self.button_size)
        zoom_entry.pack(side='left', padx=10)
        zoom_entry.bind('<Return>', self.set_zoom)
        zoom_entry.focus_set()
        tk.Button(window, text='Default', command=self.set_zoom).pack(side='left')

    # Options menu methods.
    def update_settings(self):
        self.drag_select = self.drag_select_var.get()

    # Help menu methods.
    def show_text(self, filename, width=80, height=24):
        window = self.active_windows[filename] = tk.Toplevel(self)
        window.title(filename.capitalize())
        scrollbar = Scrollbar(window)
        scrollbar.pack(side='right', fill=Y)
        self.focus = text = Text(window, width=width, height=height, wrap=WORD,
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
        new_nbrs = get_neighbours(coord, self.dims, self.detection,
            include=True)
        # Only consider unclicked cells.
        new_nbrs = {self.buttons[c] for c in new_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Sink the new neighbouring buttons.
        for b in new_nbrs:
            b.config(bd=1, relief='sunken')

    def both_release(self, coord):
        super(TestGui, self).both_release(coord)
        # Buttons which neighbour the previously selected button.
        old_nbrs = get_neighbours(coord, self.dims, self.detection,
            include=True)
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
            old_nbrs = get_neighbours(prev_coord, self.dims, self.detection,
                include=True)
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
        # Create a minefield stored within the game, which will generate a
        # board if first_success is False. Otherwise call
        # Game.mf.generate_rnd() and Game.mf.setup() to complete
        # initialisation.
        self.game = Game(self.settings)

    def run(self):
        # Create menubar.
        self.menubar = MenuBar(self, 'full')
        self.config(menu=self.menubar)
        self.mainloop()

    # Make the GUI.
    def make_panel(self):
        super(GameGui, self).make_panel()
        # Create and place the timer.
        self.timer_hide_var = tk.BooleanVar()
        self.timer = Timer(self.panel)
        self.timer.place(relx=1, x=-7, rely=0.5, anchor='e')
        self.timer.bind('<Button-%s>'%RIGHT_BTN_NUM, self.toggle_timer)
        self.timer.bindtags(('panel',) + self.timer.bindtags())

    # Button actions.
    def left_press(self, coord):
        super(GameGui, self).left_press(coord)
        b = self.buttons[coord]
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

    def right_motion(self, coord, prev_coord):
        super(GameGui, self).right_motion(coord, prev_coord)
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
        super(GameGui, self).both_press(coord)
        # Buttons which neighbour the current selected button.
        new_nbrs = get_neighbours(coord, self.dims, self.detection,
            include=True)
        # Only consider unclicked cells.
        new_nbrs = {self.buttons[c] for c in new_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Sink the new neighbouring buttons.
        for b in new_nbrs:
            b.config(bd=1, relief='sunken')

    def both_release(self, coord):
        super(GameGui, self).both_release(coord)
        # Buttons which neighbour the previously selected button.
        old_nbrs = get_neighbours(coord, self.dims, self.detection,
            include=True)
        # Only worry about unclicked cells.
        old_nbrs = {self.buttons[c] for c in old_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Raise the old neighbouring buttons.
        for b in old_nbrs:
            b.config(bd=3, relief='raised', text='.')

    def both_motion(self, coord, prev_coord):
        super(GameGui, self).both_motion(coord, prev_coord)
        if prev_coord:
            # Buttons which neighbour the previously selected button.
            old_nbrs = get_neighbours(prev_coord, self.dims, self.detection,
                include=True)
            # Only worry about unclicked cells.
            old_nbrs = {self.buttons[c] for c in old_nbrs
                if self.buttons[c].state == UNCLICKED}
            # Raise the old neighbouring buttons.
            for b in old_nbrs:
                b.config(bd=3, relief='raised')
        if coord:
            self.both_press(coord)

    def click(self, coord, check_for_win=True):
        b = self.buttons[coord]
        if self.game.state == READY:
            if self.first_success and self.game.mf.origin != KNOWN:
                self.game.mf.generate_rnd(open_coord=coord)
                self.game.mf.setup()
            self.game.state = ACTIVE
            self.game.start_time = tm.time()
            # self.timer.update(self.game.start_time)

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
            if check_for_win:
                self.check_completion()
        elif cell_nr > 0: #normal success
            self.reveal_safe_cell(coord)
            if check_for_win:
                self.check_completion()
        else: #mine hit, game over
            self.game.finish_time = tm.time()
            self.unset_button_bindings()
            b.state = MINE
            self.game.state = LOST
            colour = '#%02x%02x%02x' % bg_colours['red']
            b.config(bd=1, relief='sunken', bg=colour,
                image=self.mine_images[('red', 1)])
            self.face_button.config(image=self.face_images['lost1face'])
            for c, b in [(b1.coord, b1) for b1 in self.buttons.values()
                if b1.state != CLICKED]:
                # Check for incorrect flags.
                if b.state == FLAGGED and self.game.mf.mines_grid[c] == 0:
                    # Could use an image here..
                    b.config(text='X', image='', font=self.nr_font)
                # Reveal remaining mines.
                elif b.state == UNCLICKED and self.game.mf.mines_grid[c] > 0:
                    b.state = MINE
                    b.config(bd=1, relief='sunken',
                        image=self.mine_images[self.game.mf.mines_grid[c]])
            # self.finalise_game()

    # GUI and game methods.
    def reveal_safe_cell(self, coord):
        b = self.buttons[coord]
        nr = self.game.mf.completed_grid[coord]
        # Assign the game grid with the numbers which are uncovered.
        self.game.grid.itemset(coord, nr)
        b.state = CLICKED
        # Display the number unless it is a zero.
        text = nr if nr else ''
        try:
            nr_colour = nr_colours[nr]
        except KeyError:
            # In case the number is unusually high.
            nr_colour = 'black'
        b.config(bd=1, relief='sunken', #bg='SystemButtonFace',
            text=text, fg=nr_colour, font=self.nr_font)

    def check_completion(self):
        pass

    def toggle_timer(self, event=None):
        if event:
            self.timer_hide_var.set(not(self.timer_hide_var.get()))
        # Always show the timer if the game is lost or won.
        if (self.timer_hide_var.get() and self.game.state not in [WON, LOST]):
            self.timer.config(fg='black')
        else:
            self.timer.config(fg='red')

    # Game menu methods.
    def refresh_board(self, event=None, is_replay=False):
        super(GameGui, self).refresh_board()
        if not is_replay:
            self.game = Game(self.settings)

    # Options menu methods.
    def update_settings(self):
        self.first_success = self.first_success_var.get()
        self.drag_select = self.drag_select_var.get()



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

        self.g_menu.add_command(label='Refresh', command=self.parent.refresh_board,
            accelerator='F2')
        self.bind_all('<F2>', self.parent.refresh_board)
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
        self.coord = coord
        self.parent = parent
        self.model = model
        self.state = UNCLICKED
        # Initialise a frame of correct size to contain a button.
        frame = tk.Frame(parent, width=model.button_size,
            height=model.button_size)
        frame.rowconfigure(0, weight=1) #enable button to fill frame
        frame.columnconfigure(0, weight=1)
        frame.grid_propagate(False) #disable resizing of frame
        # Place with the grid packer.
        frame.grid(row=coord[0], column=coord[1])
        super(Cell, self).__init__(frame, bd=3, relief='raised',
            font=model.nr_font)
        self.grid(sticky='nsew')
        self.bindtags(('board',) + self.bindtags())




class Timer(tk.Label, object):
    def __init__(self, parent):
        self.var = tk.StringVar()
        self.var.set("000")
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