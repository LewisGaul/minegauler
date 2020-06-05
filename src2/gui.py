
import os
from os.path import join, split, splitext, exists, basename
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
msg_font = ('Times', 10, 'bold')


class BasicGui(tk.Tk, object):
    def __init__(self, **kwargs):
        self.default_btn_size = 16
        # Defaults which may be overwritten below.
        self.settings = default_settings.copy()
        # Overwrite with any given settings.
        for s, val in kwargs.items():
            self.settings[s] = val
        # Store each setting as an attribute of the class.
        for s, val in self.settings.items():
            setattr(self, s, val)
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
        self.msg_font = msg_font

        # # Turn off option of resizing window.
        # self.resizable(False, False)
        if not hasattr(self, 'base_height'):
            self.base_height = 40
        if not hasattr(self, 'base_width'):
            self.base_width = 0
        self.minsize(20+128, self.base_height+20+128) #size of beginner
        self.block_windows = False

        # Set variables.
        self.diff_var = tk.StringVar()
        self.diff_var.set(self.diff)
        self.zoom_var = tk.BooleanVar()
        if self.btn_size != self.default_btn_size:
            self.zoom_var.set(True)
        self.drag_select_var = tk.BooleanVar()
        self.drag_select_var.set(self.drag_select)

        self.face_images = dict()
        self.btn_images = dict() #images to be displayed on buttons
        self.frame_images = dict()
        # t = tm.time()
        self.get_images() #takes 0.3 seconds...
        # print "Time to get images was {:.2f}s.".format(tm.time() - t)
        # Make main body of GUI.
        self.make_panel()
        self.make_minefield()
        self.make_menubar()
        # Used to determine which image to use when right-clicking.
        self.flag_type = 'flag'

        # Keep track of mouse clicks.
        self.left_btn_down = False
        self.right_btn_down = False
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
    def make_menubar(self):
        menu = self.menubar = MenuBar(self)
        self.config(menu=menu)
        menu.game_menu.add_item('command', 'New',
            command=self.start_new_game, accelerator='F2')
        self.bind('<F2>', self.start_new_game)
        menu.game_menu.add_item('separator')
        for i in diff_names:
            menu.game_menu.add_item('radiobutton', i[1], value=i[0],
                command=self.set_difficulty(i[0]), variable=self.diff_var,
                accelerator=i[0])
            self.bind('<{}>'.format(i[0]),
                self.set_difficulty(i[0], hotkey=True))
        menu.game_menu.add_item('separator')
        menu.game_menu.add_item('checkbutton', 'Zoom',
            command=self.get_zoom, variable=self.zoom_var)
        styles_menu = tk.Menu(menu)
        menu.game_menu.add_item('cascade', 'Styles', menu=styles_menu)
        self.style_vars = dict()
        for i in ['buttons']:
            submenu = tk.Menu(styles_menu)
            styles_menu.add_cascade(label=i.capitalize(), menu=submenu)
            self.style_vars[i] = tk.StringVar()
            self.style_vars[i].set(self.styles[i])
            for j in glob(join(direcs['images'], i, '*')):
                style = basename(j)
                submenu.add_radiobutton(label=style.capitalize(),
                    variable=self.style_vars[i], value=style,
                    command=self.update_style(i))
        menu.game_menu.add_item('separator')
        menu.game_menu.add_item('command', 'Exit', command=self.destroy)

        menu.opts_menu.add_item('checkbutton', 'Drag-select',
            variable=self.drag_select_var, command=self.update_settings)

        show_about = lambda e=None: self.show_text('about', 40, 5)
        menu.help_menu.add_item('command', 'About', accelerator='F1',
            command=show_about)
        self.bind_all('<F1>', show_about)

    def make_panel(self):
        self.panel = tk.Frame(self, pady=4, height=40)
        self.panel.pack(fill='both')
        # Make the gridded widgets fill the panel.
        self.panel.columnconfigure(1, weight=1)
        face_frame = tk.Frame(self.panel)
        face_frame.place(relx=0.5, rely=0.5, anchor='center')
        n = min(3, self.lives)
        # Create face button which will refresh the board.
        self.face_button = tk.Button(face_frame, bd=4, takefocus=False,
            image=self.face_images['ready%s'%n],
            command=self.start_new_game)
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
        self.mainframe = tk.Frame(self)
        self.mainframe.pack()
        # Create canvas to contain board and frame images.
        self.canvas = tk.Canvas(self.mainframe, highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        f = tk.Frame(self.mainframe, height=16) #dummy to expand frame
        # f.grid(row=1)
        tk.Frame(self.mainframe, width=16).grid(column=1)
        # Create scrollbars (not displayed unless needed).
        self.sbx = tk.Scrollbar(self.mainframe, command=self.canvas.xview,
            orient='horizontal')
        self.sby = tk.Scrollbar(self.mainframe, command=self.canvas.yview)
        # self.sbx.place(relx=0, rely=1, anchor='sw')
        self.sbx.frame = f
        self.sbx.ismapped, self.sby.ismapped = False, False
        self.canvas.config(xscrollcommand=self.sbx.set,
            yscrollcommand=self.sby.set)
        self.bind('<Left>',
            lambda event: self.canvas.xview_scroll(-1, 'units'))
        self.bind('<Right>',
            lambda event: self.canvas.xview_scroll( 1, 'units'))
        self.bind('<Up>', lambda event: self.canvas.yview_scroll(-1, 'units'))
        self.bind('<Down>',
            lambda event: self.canvas.yview_scroll( 1, 'units'))
        self.canvas.create_image(0, 0, image=self.frame_images['nw'],
            anchor='nw')
        self.block_scrollbar_function = False
        self.bind('<Configure>', self.configure_action)
        # self.bind('<Configure>', self.config_scrollbars)
        self.set_board_size(True)
        # Create board image.
        self.board = PILImage.new('RGB',
            (self.dims[1]*self.btn_size, self.dims[0]*self.btn_size))
        self.boardID = None
        self.buttons = dict()
        self.block_of_8 = PILImage.new('RGB', tuple([8*self.btn_size]*2))
        for i in range(8):
            for j in range(8):
                self.block_of_8.paste(self.btn_images['btn_up'],
                    (i*self.btn_size, j*self.btn_size))
        for coord in self.all_coords:
            self.buttons[coord] = Cell(coord, self)
        for i in range(0, self.dims[1], 8):
            for j in range(0, self.dims[0], 8):
                self.board.paste(self.block_of_8,
                    (i*self.btn_size,j*self.btn_size))
        self.new_board = self.board.copy()
        self.place_board_image()
        self.create_button_methods()
        self.set_button_bindings()

    def set_cell_image(self, coord, image, place_im=True):
        x, y = (i*self.btn_size for i in coord)
        self.board.paste(image, (y, x))
        if place_im:
            self.place_board_image()

    def place_board_image(self):
        self.canvas.delete(self.boardID)
        self.canvas.im = ImageTk.PhotoImage(self.board)
        self.boardID = self.canvas.create_image(10, 10,
            image=self.canvas.im, anchor='nw')

    def config_scrollbars(self, event=None, dims=None):
        """
        Make window bigger when adding in one scrollbar to accomodate.
        Make window stay same size when making board bigger.
        Don't pack scrollbars when zooming in.
        """
        def scroll(event, direction):
            if PLATFORM == 'mac':
                amount = event.delta
            else:
                amount = event.delta / 120
            if direction == 'x':
                self.canvas.xview_scroll(-amount, "units")
            else:
                self.canvas.yview_scroll(-amount, "units")
        def bind_mousewheel(direction='y'):
            scroll2 = lambda e: scroll(e, direction)
            if PLATFORM == 'linux':
                self.bind('<Button-4>', scroll2)
                self.bind('<Button-5>', scroll2)
            else:
                self.bind('<MouseWheel>', scroll2)
        # Size of board with frame.
        w0, h0 = self.canvas.width, self.canvas.height
        # Size of displayed part of canvas.
        if dims:
            w, h = dims
        else:
            if self.block_scrollbar_function:
                # Don't run the function again until it has finished running.
                return
            w = self.winfo_width() - self.base_width
            h = self.winfo_height() - self.base_height
        self.block_scrollbar_function = True
        # print w0, h0
        # print w, h
        set_maxw = set_maxh = False
        if h0 > h:
            if not self.sby.ismapped:
                # Pack vertical scrollbar.
                self.sby.place(relx=1, rely=0, anchor='ne', height=h)
                self.sby.ismapped = True
                self.base_width += 16
                bind_mousewheel()
                if not self.sbx.ismapped:
                    set_maxw = True
            else:
                self.sby.place_configure(height=h)
        elif h0 == h and self.sby.ismapped:
            self.sby.place_forget()
            self.sby.ismapped = False
            self.base_width -= 16
            if w0 > w:
                bind_mousewheel('x')
        if w0 > w:
            if not self.sbx.ismapped:
                # Pack horizontal scrollbar.
                self.sbx.place(relx=0, rely=1, anchor='sw', width=w)
                self.sbx.frame.grid(row=1)
                self.sbx.ismapped = True
                self.base_height += 16
                if not self.sby.ismapped:
                    set_maxh = True
                    bind_mousewheel('x')
            else:
                self.sbx.place_configure(width=w)
        elif w0 == w and self.sbx.ismapped:
            self.sbx.place_forget()
            self.sbx.frame.grid_forget()
            self.sbx.ismapped = False
            self.base_height -= 16
        self.canvas.config(width=self.winfo_width()-self.base_width,
            height=self.winfo_height()-self.base_height)
        maxw = min(1000, self.canvas.width) + self.base_width
        maxh = min(500, self.canvas.height) + self.base_height
        self.maxsize(maxw, maxh)
        # if set_maxw:
        #     self.geometry('{}x{}'.format(maxw, self.winfo_height()))
        # elif set_maxh:
        #     self.geometry('{}x{}'.format(self.winfo_width(), maxh))
        # def delay():
        #     self.block_scrollbar_function = False
        #     self.config_scrollbars()
        # self.after(1000, delay)
        self.block_scrollbar_function = False

    def configure_action(self, event):
        if tm.time() - self.block_scrollbar_function > 1:
            self.config_scrollbars()

    def set_board_size(self, new=False):
        h0, w0 = (20 + i*self.btn_size for i in self.dims)
        self.canvas.width = w0
        self.canvas.height = h0
        w = min(1000, w0)
        h = min(500, h0)
        f_ims = self.frame_images
        self.canvas.delete('frame')
        self.canvas.create_image(0, h0, image=f_ims['s'], anchor='sw',
            tag='frame')
        self.canvas.create_image(w0, 0, image=f_ims['e'], anchor='ne',
            tag='frame')
        self.canvas.create_image(w0, h0, image=f_ims['se'], anchor='se',
            tag='frame')
        self.canvas.config(scrollregion=(0, 0, w0, h0))
        maxw = w + self.base_width
        maxh = h + self.base_height
        maxsize = self.maxsize()
        self.maxsize(maxw, maxh)
        # Determine size of window by which dimensions are full-sized.
        if self.winfo_width() == maxsize[0] or new:
            width = maxw
        else:
            width = self.winfo_width()
        if self.winfo_height() == maxsize[1] or new:
            height = maxh
        else:
            height = self.winfo_height()
        self.block_scrollbar_function = tm.time()
        self.geometry('{}x{}'.format(width, height))
        self.config_scrollbars(dims=(w, h))

    def create_button_methods(self):
        for i in ['left', 'right', 'both']:
            setattr(BasicGui, '{}_press'.format(i), lambda s, c: None)
            setattr(BasicGui, '{}_release'.format(i), lambda s, c: None)
            setattr(BasicGui, '{}_motion'.format(i), lambda s, c1, c2: None)
        setattr(BasicGui, 'double_left_press', lambda s, c: None)
        setattr(BasicGui, 'ctrl_left_press', lambda s, c: None)

    def set_button_bindings(self):
        self.canvas.bind('<Button-1>', self.detect_left_press)
        self.canvas.bind('<ButtonRelease-1>', self.detect_left_release)
        self.canvas.bind('<Button-%s>'%RIGHT_BTN_NUM, self.detect_right_press)
        self.canvas.bind('<ButtonRelease-%s>'%RIGHT_BTN_NUM,
            self.detect_right_release)
        self.canvas.bind('<B1-Motion>', self.detect_motion)
        self.canvas.bind('<B%s-Motion>'%RIGHT_BTN_NUM, self.detect_motion)
        self.canvas.bind('<Double-Button-1>', self.detect_double_left_press)
        self.canvas.bind('<Control-1>', self.detect_ctrl_left_press)

    def unset_button_bindings(self):
        self.canvas.unbind('<Button-1>')
        self.canvas.unbind('<ButtonRelease-1>')
        self.canvas.unbind('<Button-%s>'%RIGHT_BTN_NUM)
        self.canvas.unbind('<ButtonRelease-%s>'%RIGHT_BTN_NUM)
        self.canvas.unbind('<B1-Motion>')
        self.canvas.unbind('<B%s-Motion>'%RIGHT_BTN_NUM)
        self.canvas.unbind('<Double-Button-1>')
        self.canvas.unbind('<Control-1>')

    def overlay_image(self, path, overlay):
        size = self.btn_size
        im = PILImage.open(path)
        overlay = PILImage.open(overlay)
        if overlay.mode == 'RGB':
            overlay = overlay.convert('RGBA')
        pos = (80 - overlay.size[0]) / 2 #change to accomodate any size
        # Place the overlay on top of the image using it as a mask.
        im.paste(overlay, (pos, pos), overlay)
        return im.resize((size, size), PILImage.ANTIALIAS)

    def get_images(self, change='all'):
        if change in ['all', 'faces']:
            # Collect all faces that are in the folder and store in dictionary
            # under filename.
            for path in glob(join(direcs['images'], 'faces', '*.ppm')):
                # Remove 'face.ppm' from end of filename.
                im_name = splitext(basename(path))[0][:-4]
                self.face_images[im_name] = tk.PhotoImage(name=im_name,
                    file=join(direcs['images'], 'faces', im_name + 'face.ppm'))

        # Create the PhotoImages from the png files.
        def get_im(f1, im_type=None, f2=None):
            # If image isn't present in current style use standard style.
            path1 = join(direcs['images'], 'buttons',
                self.styles['buttons'], f1)
            if not exists(path1):
                path1 = join(direcs['images'], 'buttons', 'standard', f1)
            if im_type and f2:
                path2 = join(direcs['images'], im_type,
                    self.styles[im_type], f2)
                if not exists(path2):
                    path2 = join(direcs['images'], im_type, 'standard', f2)
                return self.overlay_image(path1, path2)
            else:
                path2 = None
                return PILImage.open(path1).resize(
                    (self.btn_size,self.btn_size), PILImage.ANTIALIAS)

        if change in ['all', 'buttons']:
            self.btn_images['btn_up'] = get_im('btn_up.png')
            self.btn_images['btn_down'] = get_im('btn_down.png')
            self.btn_images['btn_red'] = get_im('btn_down_red.png')
            self.btn_images['btn_life'] = get_im('btn_down_life.png')
            self.btn_images['num0'] = self.btn_images['btn_down']
        if change in ['all', 'numbers', 'buttons']:
            for i in range(1, 19):
                self.btn_images['num%s'%i] = get_im('btn_down.png',
                    'numbers', 'num%s.png'%i)
        if change in ['all', 'images', 'buttons']:
            for i in range(1, 4):
                for c in bg_colours:
                    key = 'mine%s%s' % (i, c)
                    btn_file = 'btn_down{}.png'.format(
                        '_%s'%c if c else '')
                    self.btn_images[key] = get_im(btn_file,
                        'images', 'mine%s.png'%i)
                self.btn_images['flag%s'%i] = get_im('btn_up.png',
                    'images', 'flag%s.png'%i)
                self.btn_images['cross%s'%i] = get_im('btn_up.png',
                    'images', 'cross%s.png'%i)
                self.btn_images['flag%slife'%i] = get_im('btn_up.png',
                    'images', 'flag%slife.png'%i)
        if change in ['all', 'frames']:
            direc = join(direcs['images'], 'frames', self.styles['frames'])
            for i in ['topleft', 'bottom', 'right', 'corner']:
                if not exists(join(direc, 'frame_%s.png'%i)):
                    direc = join(dirname(direc), 'standard')
                    break
            for tup in [('nw', 'topleft'), ('s', 'bottom'), ('e', 'right'),
                ('se', 'corner')]:
                self.frame_images[tup[0]] = ImageTk.PhotoImage(
                    PILImage.open(join(direc, 'frame_%s.png'%tup[1])))

    def get_mouse_coord(self, event):
        x = int(self.canvas.canvasx(event.x) - 10)/self.btn_size
        y = int(self.canvas.canvasy(event.y) - 10)/self.btn_size
        if x not in range(self.dims[1]) or y not in range(self.dims[0]):
            # Clicked on border.
            return None
        else:
            return (y, x)

    # Button actions, redirected to appropriate methods.
    def detect_left_press(self, event):
        self.left_btn_down = True
        if self.right_btn_down:
            self.is_both_click = True
            self.both_press(self.mouse_coord)
        else:
            self.mouse_coord = self.get_mouse_coord(event)
            if self.mouse_coord:
                self.left_press(self.mouse_coord)

    def detect_left_release(self, event):
        # Catch the case the click wasn't received as a button click.
        if not self.left_btn_down:
            return
        self.left_btn_down = False
        if not self.mouse_coord:
            self.is_both_click = False
            self.right_btn_down = False #shouldn't be needed
            return
        if self.right_btn_down:
            self.both_release(self.mouse_coord)
        elif self.is_both_click:
            self.is_both_click = False
            self.mouse_coord = None
        else:
            self.left_release(self.mouse_coord)
            self.mouse_coord = None

    def detect_double_left_press(self, event):
        self.left_btn_down = True
        self.mouse_coord = self.get_mouse_coord(event)
        if self.mouse_coord:
            self.double_left_press(self.mouse_coord)

    def detect_right_press(self, event):
        self.right_btn_down = True
        if self.left_btn_down:
            self.is_both_click = True
            self.both_press(self.mouse_coord)
        else:
            self.mouse_coord = self.get_mouse_coord(event)
            if self.mouse_coord:
                self.right_press(self.mouse_coord)

    def detect_right_release(self, event):
        self.right_btn_down = False
        if not self.mouse_coord:
            self.is_both_click = False
            self.left_btn_down = False #shouldn't be needed
            return
        if self.left_btn_down:
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
        if self.left_btn_down:
            if self.right_btn_down: #both
                self.both_motion(cur_coord, self.mouse_coord)
            elif not self.is_both_click: #left
                self.left_motion(cur_coord, self.mouse_coord)
        elif self.right_btn_down and not self.is_both_click: #right
            self.right_motion(cur_coord, self.mouse_coord)
        self.mouse_coord = cur_coord

    def detect_ctrl_left_press(self, event):
        coord = self.get_mouse_coord(event)
        if not self.right_btn_down:
            self.ctrl_left_press(coord)

    # GUI and game methods.
    def refresh_board(self, event=None):
        self.board = self.new_board.copy()
        self.place_board_image()
        for b in self.buttons.values():
            b.refresh(False)
        self.update_settings()
        self.set_button_bindings()
        self.left_btn_down = self.right_btn_down = False
        self.mouse_coord = self.drag_flag = None
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

    def set_difficulty(self, diff, run=False, hotkey=False):
        def action(event=None):
            # Don't change difficulty using key bindings if not in the main
            # game or not changing difficulty.
            if hotkey and (
                self.focus != self or diff == self.diff in diff_dims):
                return
            if diff in diff_dims: #standard board
                self.diff = self.settings['dims'] = diff
                self.mines = nr_mines[self.diff][self.detection]
                self.settings['mines'] = self.mines
                self.reshape(diff_dims[self.diff])
                self.start_new_game()
            else: #custom, open popup window
                # Don't change the radiobutton until custom is confirmed.
                self.diff_var.set(self.diff)
                self.get_custom()
        if run:
            action()
        else:
            return action

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

        def finish(event=None):
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
            self.mines = self.settings['mines'] = mines
            self.reshape(dims)
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

        win.make_btn('OK', finish)
        win.make_btn('Cancel', lambda: self.close_window(title))
        self.add_to_bindtags([win, row_entry, col_entry, mine_entry], 'custom')
        self.bind_class('custom', '<Return>', finish)
        self.focus = row_entry
        self.focus.focus_set()

    def reshape(self, dims):
        old_dims = self.dims
        self.dims = dims
        self.set_board_size()
        # This runs if one of the dimensions was previously larger.
        extras = [c for c in self.all_coords if c[0] >= dims[0] or
            c[1] >= dims[1]]
        for coord in extras:
            b = self.buttons.pop(coord)
        self.all_coords = [(i, j) for i in range(dims[0])
            for j in range(dims[1])]
        new = [c for c in self.all_coords if c[0] >= old_dims[0] or
            c[1] >= old_dims[1]]
        old_board = self.new_board
        self.board = PILImage.new('RGB',
            (self.dims[1]*self.btn_size, self.dims[0]*self.btn_size))
        self.board.paste(old_board, (0, 0))
        for coord in new: #speed up using blocks of 8
            self.buttons[coord] = Cell(coord, self)
        # # Round up to nearest multiple of 8.
        # rounded = tuple(8 * ((i-1)/8 + 1) for i in old_dims)
        for i in range(0, self.dims[1], 8):
            for j in range(0, self.dims[0], 8):
                self.board.paste(self.block_of_8,
                    (i*self.btn_size,j*self.btn_size))
        self.place_board_image()
        self.new_board = self.board
        # Check if this is custom.
        if (dims in diff_dims and
            self.mines == nr_mines[diff_dims[dims]][self.detection]):
            self.diff = diff_dims[dims]
            self.diff_var.set(self.diff)
        else:
            self.diff = 'c'
            self.diff_var.set('c')
        for s in ['dims', 'mines', 'diff']:
            self.settings[s] = getattr(self, s)
        self.refresh_board()

    def get_zoom(self):
        def slide(num):
            # Slider is moved, change text entry.
            zoom_entry.delete(0, 'end')
            zoom_entry.insert(0, num)

        # Ensure tick on radiobutton is correct.
        if self.btn_size == 16:
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
        zoom = int(round(self.btn_size*100.0/self.default_btn_size, 0))
        slider = tk.Scale(win.mainframe, from_=60, to=200, length=140,
            orient='horizontal', showvalue=False, command=slide)
        zoom_entry = tk.Entry(win.mainframe, width=4, justify='right')
        tk.Label(win.mainframe, text='%  ').pack(side='right')
        zoom_entry.pack(side='right')
        slider.pack(side='right', padx=10)
        slider.set(zoom)
        zoom_entry.insert(0, zoom)

        win.make_btn('Default', lambda: self.set_zoom())
        win.make_btn('OK', lambda: self.set_zoom(zoom_entry.get()))
        win.make_btn('Cancel', lambda: self.close_window(title))
        self.add_to_bindtags([win, slider, zoom_entry], 'zoom')
        self.bind_class('zoom','<Return>',
            lambda event=None: self.set_zoom(zoom_entry.get()))
        self.focus = zoom_entry
        self.focus.focus_set()

    def set_zoom(self, zoom=None):
        if zoom is None:
            zoom = '100'
        if zoom not in map(str, range(60, 501)): #invalid
            return
        old_btn_size = self.btn_size
        self.btn_size = int(round(int(zoom)*self.default_btn_size/100.0, 0))
        self.settings['btn_size'] = self.btn_size
        if self.btn_size == self.default_btn_size:
            self.zoom_var.set(False)
        else:
            self.zoom_var.set(True)
        if old_btn_size != self.btn_size:
            self.get_images('buttons')
            self.board = PILImage.new('RGB',
                (self.dims[1]*self.btn_size,self.dims[0]*self.btn_size))
            self.block_of_8 = PILImage.new('RGB', tuple([8*self.btn_size]*2))
            for i in range(8):
                for j in range(8):
                    self.block_of_8.paste(self.btn_images['btn_up'],
                        (i*self.btn_size,j*self.btn_size))
            for i in range(0, self.dims[1], 8):
                for j in range(0, self.dims[0], 8):
                    self.board.paste(self.block_of_8,
                        (i*self.btn_size,j*self.btn_size))
            self.new_board = self.board.copy()
            for b in self.buttons.values():
                b.size = self.btn_size
                if b.im != 'btn_up':
                    b.set_image()
            self.place_board_image()
            self.set_board_size()
        if 'Zoom' in self.active_windows:
            self.close_window('Zoom')

    def update_style(self, change, run=False):
        def action():
            new_style = self.style_vars[change].get()
            if new_style == self.styles[change]: #no change
                return
            self.styles[change] = new_style
            self.settings['styles'] = self.styles
            self.get_images(change)
            if change == 'buttons':
                for i in range(8):
                    for j in range(8):
                        self.block_of_8.paste(self.btn_images['btn_up'],
                            (i*self.btn_size,j*self.btn_size))
                for i in range(0, self.dims[0], 8):
                    for j in range(0, self.dims[1], 8):
                        self.board.paste(self.block_of_8,
                            (i*self.btn_size,j*self.btn_size))
                self.new_board = self.board.copy()
                for b in self.buttons.values():
                    if b.im != 'btn_up':
                        b.set_image()
                self.place_board_image()
        if run:
            action()
        else:
            return action

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
        text.bind('<Return>', lambda e: self.close_window(title))
        win.make_btn('OK', lambda: self.close_window(title))
        self.focus = text
        self.focus.focus_set()



class TestGui(BasicGui):
    def __init__(self, **kwargs):
        super(TestGui, self).__init__(**kwargs)

    # Button actions.
    def left_press(self, coord):
        b = self.buttons[coord]
        if self.drag_select:
            if b.state == UNCLICKED:
                self.click(coord)
        else:
            if b.state == UNCLICKED:
                b.set_image('btn_down')
                self.place_board_image()

    def left_release(self, coord):
        b = self.buttons[coord]
        if b.state == UNCLICKED: #catches the case drag_select is on
            self.click(coord)

    def left_motion(self, coord, prev_coord):
        if prev_coord and self.buttons[prev_coord].state == UNCLICKED:
            self.buttons[prev_coord].refresh()
        if coord:
            self.left_press(coord)

    def right_press(self, coord):
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
            b.set_image('flag1')
            b.state = FLAGGED
            b.num_of_flags = 1
        elif b.state == FLAGGED:
            b.refresh()
            b.state = UNCLICKED
            b.num_of_flags = 0
        self.place_board_image()

    def right_motion(self, coord, prev_coord):
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
            b.set_image('flag1')
            b.state = FLAGGED
            b.num_of_flags = 1
        elif self.drag_flag == UNFLAG and b.state == FLAGGED:
            b.refresh()
            b.state = UNCLICKED
            b.num_of_flags = 0
        else:
            return
        self.place_board_image()

    def both_press(self, coord):
        b = self.buttons[coord]
        if b.state == UNCLICKED:
            # Get rid of down-image that already exists.
            b.refresh()
        # Buttons which neighbour the current selected button.
        nbrs = self.get_nbrs(coord, include=True)
        # Only consider unclicked cells.
        nbrs = {c for c in nbrs
            if self.buttons[c].state == UNCLICKED}
        # Sink the new neighbouring buttons.
        for c in nbrs:
            b.set_image('btn_down')
        self.place_board_image()

    def both_release(self, coord):
        # Buttons which neighbour the previously selected button.
        old_nbrs = self.get_nbrs(coord, include=True)
        # Only worry about unclicked cells.
        old_nbrs = {c for c in old_nbrs
            if self.buttons[c].state == UNCLICKED}
        # Raise the old neighbouring buttons.
        for c in old_nbrs:
            self.buttons[c].refresh()

    def both_motion(self, coord, prev_coord):
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
        b.set_image('mine1')
        self.place_board_image()
        b.state = CLICKED



class CreateGui(BasicGui):
    def __init__(self, **kwargs):
        super(CreateGui, self).__init__(**kwargs)
        self.is_create_mode = True

    def left_press(self, coord):
        b = self.buttons[coord]
        if self.drag_select:
            if (b.state == UNCLICKED or
                self.is_create_mode and b.state == CLICKED):
                self.click(coord)
        else:
            if b.state == UNCLICKED:
                b.set_image('btn_down')
                self.place_board_image()

    def left_release(self, coord):
        if not self.drag_select and self.buttons[coord].state != MINE:
            self.click(coord)
        self.drag_flag = None

    def left_motion(self, coord, prev_coord):
        if prev_coord and self.buttons[prev_coord].state == UNCLICKED:
            self.buttons[prev_coord].refresh()
        if coord:
            b = self.buttons[coord]
            if self.drag_flag == UNFLAG:
                if b.state == FLAGGED:
                    b.refresh()
                    self.set_mines_counter()
                return
            self.left_press(coord)

    def right_press(self, coord):
        b = self.buttons[coord]
        if (b.state == UNCLICKED or
            (b.state == FLAGGED and b.num_of_flags < self.per_cell)):
            b.incr_flags()
        elif (b.state == FLAGGED or
            (b.state == CLICKED and self.is_create_mode)):
            b.refresh()
        # Check whether drag-clicking should set or unset mines.
        if self.drag_select:
            if b.state == UNCLICKED:
                self.drag_flag = UNFLAG
            elif b.state == FLAGGED:
                self.drag_flag = FLAG
            else:
                self.drag_flag = None
        else:
            self.drag_flag = None
        self.place_board_image()

    def right_release(self, coord):
        self.drag_flag = None

    def right_motion(self, coord, prev_coord):
        # Do nothing if leaving the board.
        if not coord:
            return
        b = self.buttons[coord]
        if self.drag_flag == FLAG and b.state == UNCLICKED:
            b.incr_flags()
        elif self.drag_flag == UNFLAG and b.state == FLAGGED:
            b.refresh()
        else:
            return
        self.place_board_image()

    def both_press(self, coord):
        b = self.buttons[coord]
        if b.state == UNCLICKED:
            # Get rid of down-image that already exists.
            b.refresh()
        # Buttons which neighbour the current selected button.
        nbrs = self.get_nbrs(coord, include=True)
        # Only consider unclicked cells.
        nbrs = {c for c in nbrs
            if self.buttons[c].state == UNCLICKED}
        # Sink the new neighbouring buttons.
        for c in nbrs:
            self.buttons[c].set_image('btn_down')
        self.place_board_image()

    def both_release(self, coord):
        # Buttons which neighbour the previously selected button.
        nbrs = self.get_nbrs(coord, include=True)
        # Raise the old neighbouring buttons.
        for c in nbrs:
            b = self.buttons[c]
            if b.state == UNCLICKED:
                b.refresh()
        self.place_board_image()

    def both_motion(self, coord, prev_coord):
        if prev_coord:
            # Buttons which neighbour the previously selected button.
            old_nbrs = self.get_nbrs(prev_coord, include=True)
            # Raise the old neighbouring buttons.
            for c in old_nbrs:
                b = self.buttons[c]
                if b.state == UNCLICKED:
                    b.refresh()
        if coord:
            self.both_press(coord)
        self.place_board_image()

    def double_left_press(self, coord):
        b = self.buttons[coord]
        if (self.per_cell > 1 and b.state == FLAGGED):
            b.refresh()
            self.place_board_image()
            if self.drag_select:
                self.drag_flag = UNFLAG
            self.set_mines_counter()
        if b.state == CLICKED:
            self.left_press(coord)

    def click(self, coord):
        b = self.buttons[coord]
        if b.nr == 8:
            return
        elif b.nr is None:
            b.nr = 0
            b.state = CLICKED
        else:
            b.nr += 1
        b.set_image('num{}'.format(b.nr))
        self.place_board_image()



class MenuBar(tk.Menu, object):
    def __init__(self, parent):
        super(MenuBar, self).__init__(parent)
        self.parent = parent
        for i in ['game', 'opts', 'help']:
            menu = tk.Menu(self)
            setattr(self, i + '_menu', menu)
            menu.items = []
            menu.add_item = self.get_add_item(i)
            menu.del_item = self.get_del_item(i)
        self.add_cascade(label='Game', menu=self.game_menu)
        self.add_cascade(label='Options', menu=self.opts_menu)
        self.add_cascade(label='Help', menu=self.help_menu)

    def get_add_item(self, menu_):
        def add_item(type_, label=None, index='end', **kwargs):
            m = getattr(self, menu_ + '_menu')
            if type(index) is int and index < 0:
                index += len(m.items)
            m.insert(index, type_, label=label, **kwargs)
            if index == 'end':
                m.items.append(label)
            else:
                m.items.insert(index, label)
        return add_item

    def get_del_item(self, menu):
        def del_item(index):
            menu = getattr(self, menu + '_menu')
            menu.delete(index)
            if index == 'end':
                menu.items.pop(index)
        return del_item



class Cell(object):
    def __init__(self, coord, root):
        self.coord = coord
        self.root = root
        self.size = root.btn_size
        self.refresh(False)

    def refresh(self, overlay=True):
        if overlay:
            self.set_image('btn_up')
        else:
            self.im = 'btn_up'
        self.state = UNCLICKED
        self.num_of_flags = 0
        self.mines = 0 #flags or mines revealed
        self.nr = None #number displayed
        self.prob_mine = None #probability of containing at least one mine
        self.fg = None

    def incr_flags(self):
        self.num_of_flags += 1
        if self.root.flag_type == 'mine':
            self.set_image('mine{}'.format(self.num_of_flags))
        else:
            self.set_image('flag{}'.format(self.num_of_flags))
        self.state = FLAGGED
        self.mines = self.num_of_flags

    def set_image(self, image=None):
        if image:
            self.im = image
        x, y = (i*self.size for i in self.coord)
        self.root.board.paste(self.root.btn_images[self.im], (y, x))



class Window(tk.Toplevel, object):
    def __init__(self, parent, title):
        self.parent = parent
        super(Window, self).__init__(parent)
        self.title(title)
        parent.track_window(self)
        self.mainframe = tk.Frame(self)
        self.mainframe.pack(ipadx=10, ipady=10)
        self.lowframe = tk.Frame(self)
        self.lowframe.pack(padx=10, pady=5)
        self.btns = []

    def make_btn(self, text, cmd):
        btn = tk.Button(self.lowframe, text=text, command=cmd)
        btn.pack(side='left', padx=10)
        btn.bind('<Return>', lambda x: btn.invoke())
        self.btns.append(btn)
        return btn



if __name__ == '__main__':
    # g = TestGui()
    g = CreateGui()
    g.mainloop()
