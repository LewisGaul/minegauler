"""
==================
Bugs
------------------
Load board - radiobutton custom (urgent).
Change style dimensions.
------------------

==================
Improvements
------------------
Highscores window left open.
Defocus name entry.
Create mode 'done' button and auto load board.
Remove numpy use.
Speed up large boards.
Add scroll with arrow keys.
------------------

==================
Additions
------------------
Resize window (with addition of scrollbars) option.
Position amongst highscores in current info after winning (and lives).
Save and load highscore board files (.mgh).
Detection strength.
'Official' settings.
Ctrl+click instead of rightclick.
Solvable boards / board solver.
'Distance to' setting.
Human vs. computer.
Achievements.
Hexagonal/rectangular/triangular(/circular - randomly placed) buttons.
------------------
"""

# Button states are:
#     UNCLICKED
#     CLICKED
#     FLAGGED
#     MINE
#
# Drag-and-select flagging types are:
#     FLAG
#     UNFLAG

import sys
import os
from os.path import join, dirname, isdir, getsize, exists
from shutil import copy2 as copy_file
import Tkinter as tk
import ttk
import tkFileDialog, tkMessageBox
from PIL import Image as PILImage, ImageTk
import time as tm
import json
from glob import glob
from distutils.version import LooseVersion
from functools import wraps

import numpy as np

from constants import * #version, platform etc.
from utils import direcs, blend_colours, where_coords, enchs
import highscore_utils
from gui import BasicGui, CreateGui, MenuBar, Window, diff_names
from game import Game, Minefield
from probabilities import NrConfig

if PLATFORM == 'windows':
    import win32com.client

__version__ = VERSION

detection_options = dict(
    [(str(i), i) for i in[0.5, 1, 1.5, 1.8, 2, 2.2, 2.5, 2.8, 3]])

msg_font = ('Times', 10, 'bold')


def defocus(method):
    # Decolour buttons and select out of name entry.
    @wraps(method)
    def decorated(obj, *args, **kwargs):
        if obj.is_coloured:
            for b in obj.buttons.values():
                if b.state == UNCLICKED:
                    b.refresh()
            obj.is_coloured = False
            obj.probs = None
        obj.submit_name_entry()
        return method(obj, *args, **kwargs)
    return decorated


class GameGui(CreateGui):
    def __init__(self, **kwargs):
        self.base_height = 60
        self.base_width = 0
        super(GameGui, self).__init__(**kwargs)
        self.resizable(True, True)
        self.make_name_entry()
        self.hide_timer = False
        self.is_coloured = False
        self.probs = None
        self.prob_label = tk.Label(self) #dummy label
        # Remove probability label when ctrl key is released.
        self.bind_all('<KeyRelease-Control_L>',
            lambda event: self.prob_label.place_forget())
        self.bind_all('<KeyRelease-Control_R>',
            lambda event: self.prob_label.place_forget())
        self.paused = False
        self.bind_all('<p>', self.pause_game)
        self.is_create_mode = False

        data_path = join(direcs['data'], 'highscores.json')
        datacopy_path = join(direcs['data'], 'highscores_copy.json')
        # If datacopy file is larger assume an error in saving the
        # data, and copy the file across.
        if exists(data_path):
            # print "Data file is {:.1f}MB in size.".format(
            #     getsize(data_path)*1e-6)
            if (exists(datacopy_path) and
                getsize(data_path) < getsize(datacopy_path)):
                print "Highscores file is smaller than the copy."
                # First save smaller file.
                # fname = 'highscores recovery{}.json'.format(
                #     tm.asctime().replace(':', ''))
                # destn = join(direcs['data'], fname)
                # copy_file(data_path, destn)
                # copy_file(datacopy_path, data_path)
        try:
            with open(data_path, 'r') as f:
                self.all_highscores = json.load(f)
        except IOError:
            self.all_highscores = dict()
        except ValueError: #invalid file for loading with json
            destn = join(direcs['data'], 'highscores_recovery{}.json'.format(
                tm.asctime().replace(':', '')))
            copy_file(data_path, destn)
            self.all_highscores = dict()
        self.corrupt_highscores = dict()
        self.highscores = self.hs_key = None

        # Create a minefield within the game.
        self.start_new_game()

    # Make the GUI.
    def make_menubar(self):
        super(GameGui, self).make_menubar()
        menu = self.menubar
        index = (menu.game_menu.items.index('New') + 1 -
            len(menu.game_menu.items))
        menu.game_menu.add_item('command', 'Replay', index,
            command=self.replay_game, accelerator='F3')
        self.bind('<F3>', self.replay_game)
        self.create_var = tk.BooleanVar()
        menu.game_menu.add_item('checkbutton', 'Create', index,
            variable=self.create_var, command=self.toggle_create_mode)
        menu.game_menu.add_item('command', 'Save board', index,
            command=self.save_board)
        menu.game_menu.add_item('command', 'Load board', index,
            command=self.load_board)
        menu.game_menu.add_item('separator', index=index)
        menu.game_menu.add_item('command', 'Current info', index,
            command=self.show_info, accelerator='F4')
        self.bind('<F4>', self.show_info)
        solver_menu = tk.Menu(menu)
        menu.game_menu.add_item('cascade', 'Solver', index, menu=solver_menu)
        solver_menu.add_command(label='Show probabilities',
            command=self.show_probs, accelerator='F5')
        self.bind('<F5>', self.show_probs)
        solver_menu.add_command(label='Auto flag', command=self.auto_flag,
            accelerator='Ctrl+F')
        self.bind('<Control-Key-f>', self.auto_flag)
        solver_menu.add_command(label='Auto click',
            command=self.auto_click, accelerator='Ctrl+Enter')
        self.bind('<Control-Return>', self.auto_click)
        menu.game_menu.add_item('command', 'Highscores', index,
            command=self.show_highscores, accelerator='F6')
        self.bind('<F6>', self.show_highscores)
        index = menu.game_menu.items.index('Zoom')
        menu.game_menu.add_item('checkbutton', 'Resizable window', index+1,
            command=self.toggle_resizable, state='disabled')
        menu.game_menu.add_item('command', 'Factory reset', -1,
            command=self.reset_to_default)

        self.first_success_var = tk.BooleanVar()
        self.first_success_var.set(self.first_success)
        menu.opts_menu.add_item('checkbutton', 'FirstAuto', 0,
            variable=self.first_success_var, command=self.update_settings)
        self.lives_var = tk.IntVar()
        if self.lives > 3:
            self.lives_var.set(-1)
        else:
            self.lives_var.set(self.lives)
        lives_menu = tk.Menu(menu)
        menu.opts_menu.add_item('cascade', 'Lives', menu=lives_menu)
        for i in range(1, 4):
            lives_menu.add_radiobutton(label=i, variable=self.lives_var,
                value=i, command=self.update_settings)
        lives_menu.add_radiobutton(label='Other', variable=self.lives_var,
            value=-1, command=self.get_lives)
        per_cell_menu = tk.Menu(menu)
        menu.opts_menu.add_item('cascade', 'Per cell', menu=per_cell_menu)
        self.per_cell_var = tk.IntVar()
        self.per_cell_var.set(self.per_cell)
        for i in range(1, 4):
            per_cell_menu.add_radiobutton(label=i, variable=self.per_cell_var,
                value=i, command=self.update_settings)

        menu.help_menu.add_item('separator')
        menu.help_menu.add_item('command', 'Basic rules',
            command=lambda: self.show_text('rules'))
        menu.help_menu.add_item('command', 'Special features',
            command=lambda: self.show_text('features'))
        menu.help_menu.add_item('command', 'Tips',
            command=lambda: self.show_text('tips'))
        menu.help_menu.add_item('separator')
        menu.help_menu.add_item('command', 'Retrieve highscores',
            command=self.retrieve_highscores)

    def make_panel(self):
        super(GameGui, self).make_panel()
        # Create and place the mines counter.
        self.mines_var = tk.StringVar()
        self.mines_label = tk.Label(self.panel, bg='black', fg='red', bd=5,
            relief='sunken', font=('Verdana',11,'bold'),
            textvariable=self.mines_var)
        self.mines_label.grid(row=0, padx=(6, 0))
        self.add_to_bindtags(self.mines_label, 'panel')

        # Create and place the timer.
        self.timer = Timer(self.panel)
        self.timer.grid(row=0, column=2, padx=(0, 6))
        self.timer.bind('<Button-%s>'%RIGHT_BTN_NUM, self.toggle_timer)
        self.add_to_bindtags(self.timer, 'panel')

    def submit_name_entry(self, event=None):
        if self.name_entry['state'] == 'disabled':
            return
        self.name_entry.config(state='disabled')
        self.name = self.game.name = self.name_entry.get().strip()[:20]
        self.settings['name'] = self.name
        self.focus = self
        if self.won_game and not self.won_game['name']:
            self.won_game['name'] = self.name
            self.won_game['key'] = enchs(self.won_game, self.hs_key)
            # if 'Highscores' in self.active_windows:
            #     self.show_highscores()
    def make_name_entry(self):
        def select(event):
            self.name_entry.config(state='normal') #NORMAL is in use
            self.focus = self.name_entry
            self.focus.focus_set()
            self.name_entry.select_range(0, 'end')
        self.name_entry = tk.Entry(self, bd=2, justify='center',
            font=self.msg_font, disabledforeground='black',
            disabledbackground='grey94')
        if self.name:
            self.name_entry.insert(0, self.name)
            self.name_entry.config(state='disabled')
        else:
            self.focus = self.name_entry
        self.name_entry.pack(fill='x')
        self.name_entry.bind("<Return>", self.submit_name_entry)
        self.name_entry.bind("<Double-Button-1>", select)
        self.focus.focus_set()

    # Button actions.
    def left_press(self, coord):
        self.submit_name_entry()
        if not self.is_create_mode:
            n = min(3, self.game.lives_rem)
            self.face_button.config(image=self.face_images['active%s'%n])
        super(GameGui, self).left_press(coord)

    def left_release(self, coord):
        if self.is_create_mode:
            super(GameGui, self).left_release(coord)
            return
        self.drag_flag = None
        if self.buttons[coord].state == UNCLICKED and not self.drag_select:
            self.click(coord)
        if self.game.state in [READY, ACTIVE]:
            n = min(3, self.game.lives_rem)
            self.face_button.config(image=self.face_images['ready%s'%n])

    def left_motion(self, coord, prev_coord):
        super(GameGui, self).left_motion(coord, prev_coord)
        if self.is_create_mode:
            return
        if not coord:
            n = min(self.game.lives_rem, 3)
            self.face_button.config(image=self.face_images['ready%s'%n])

    @defocus
    def right_press(self, coord):
        super(GameGui, self).right_press(coord)
        self.set_mines_counter()

    def right_motion(self, coord, prev_coord):
        super(GameGui, self).right_motion(coord, prev_coord)
        self.set_mines_counter()

    def both_press(self, coord):
        super(GameGui, self).both_press(coord)
        if not self.is_create_mode:
            n = min(3, self.game.lives_rem)
            self.face_button.config(image=self.face_images['active%s'%n])

    def both_release(self, coord):
        super(GameGui, self).both_release(coord)
        # Buttons which neighbour the previously selected button.
        nbrs = self.get_nbrs(coord, include=True)
        grid_nr = self.game.grid[coord]
        if grid_nr >= 0: #potential chording
            nbr_mines = sum([self.buttons[c].mines for c in nbrs])
            if nbr_mines == grid_nr:
                for coord in {c for c in nbrs
                    if self.buttons[c].state == UNCLICKED}:
                    self.click(coord, check_for_win=False)
                if self.is_complete():
                    self.finalise_win()
        if self.is_create_mode:
            return
        # Reset face.
        if self.game.state in [READY, ACTIVE]:
            n = min(3, self.game.lives_rem)
            self.face_button.config(image=self.face_images['ready%s'%n])

    def both_motion(self, coord, prev_coord):
        super(GameGui, self).both_motion(coord, prev_coord)
        if self.is_create_mode:
            return
        if not coord:
            n = min(self.game.lives_rem, 3)
            self.face_button.config(image=self.face_images['ready%s'%n])

    def ctrl_left_press(self, coord):
        super(GameGui, self).ctrl_left_press(coord)
        if not self.is_coloured:
            return
        b = self.buttons[coord]
        if b.state == UNCLICKED:
            self.prob_label.place_forget()
            prob = round(self.probs[coord], 4)
            if round(prob, 2) == prob:
                text = '%d%s' % (int(100*prob), '%')
            elif round(prob, 3) == prob:
                text = '%.1f%s' % (100*round(prob, 3), '%')
            else:
                text = '%.3f%s' % (100*prob, '%')
            self.prob_label = tk.Label(self, bd=2, relief='groove',
                bg='white', text=text)
            x = min(coord[1]*self.btn_size,
                self.dims[1]*self.btn_size - 30)
            y = coord[0]*self.btn_size + 47
            self.prob_label.place(x=x, y=y, anchor='sw')

    # GUI and game methods.
    @defocus
    def click(self, coord, check_for_win=True):
        if self.is_create_mode:
            super(GameGui, self).click(coord)
            return
        b = self.buttons[coord]
        if self.game.state == READY:
            if self.first_success and self.game.mf.origin != KNOWN:
                self.game.mf.generate_rnd(open_coord=coord)
                self.game.mf.setup()
            # In case FirstAuto is turned off and a grid of mines is needed.
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
                    break #work with this set of coords
            for c in opening:
                if self.buttons[c].state == UNCLICKED:
                    self.reveal_safe_cell(c)
        elif cell_nr > 0: #normal success
            self.reveal_safe_cell(coord)
        else: #mine hit
            self.game.lives_rem -= 1
            if self.game.lives_rem == 0: #game over
                self.finalise_loss(coord)
            else:
                b.state = MINE
                n = b.mines = self.game.mf.mines_grid[coord]
                b.set_image('mine{}life'.format(n))
                if self.left_btn_down:
                    face_state = 'active'
                else:
                    face_state = 'ready'
                n = min(self.game.lives_rem, 3)
                self.face_button.config(
                    image=self.face_images['%s%s'%(face_state,n)])
                self.set_mines_counter()
        # We hold off from checking for a win if chording has been used.
        if check_for_win and self.is_complete():
            self.finalise_win()
        self.place_board_image()

    def reveal_safe_cell(self, coord):
        b = self.buttons[coord]
        nr = self.game.mf.completed_grid.item(coord)
        # Assign the game grid with the numbers which are uncovered.
        self.game.grid.itemset(coord, nr)
        b.set_image('num{}'.format(nr))
        b.state = CLICKED
        b.nr = nr

    def is_complete(self):
        return np.array_equal(
            self.game.mf.completed_grid>=0, self.game.grid>=0)

    def finalise_win(self):
        self.game.finish_time = tm.time()
        self.unset_button_bindings()
        self.timer.start_time = None
        self.timer.set_var(self.game.get_time_passed())
        self.timer.config(fg='red')
        self.game.state = WON
        n = min(3, self.game.lives_rem)
        self.face_button.config(image=self.face_images['won%s'%n])
        self.game.flags = 0
        for coord, b in self.buttons.items():
            if b.state in [UNCLICKED, FLAGGED]:
                self.game.flags += b.num_of_flags
                n = b.num_of_flags = self.game.mf.mines_grid[coord]
                b.set_image('flag{}'.format(n))
                b.state = FLAGGED
        self.mines_var.set('000')
        if self.hs_key and self.game.mf.origin != KNOWN:
            self.won_game = {
                'name': self.name,
                'time': '{:.2f}'.format(self.game.get_time_passed() + 0.01),
                '3bv': self.game.mf.get_3bv(),
                '3bv/s': '{:.2f}'.format(self.game.get_3bvps()),
                'date': self.game.finish_time,
                'flagging': self.game.get_prop_flagged(),
                'lives_rem': self.game.lives_rem,
                'first_success': self.game.first_success,
                'btn_size': self.game.btn_size
            }
            self.won_game['key'] = enchs(self.won_game, self.hs_key)
            self.highscores.append(self.won_game)
            if not self.name:
                self.show_highscores()
            else:
                for t in ['time', '3bv/s']:
                    for f in ['all', 'F', 'NF']:
                        if self.won_game in self.get_highscores(
                            order=t, flagging=f)[:5]:
                            self.show_highscores(order=t, flagging=f)
                # Backup current highscores in case of corruption.
                with open(
                    join(direcs['data'],'highscores_copy.json'), 'w') as f:
                    json.dump(self.all_highscores, f)
                copy_file(join(direcs['data'],'highscores_copy.json'),
                    join(direcs['data'],'highscores.json'))

    def finalise_loss(self, coord):
        self.game.finish_time = tm.time()
        self.unset_button_bindings()
        self.timer.start_time = None
        self.timer.set_var(self.game.get_time_passed())
        self.timer.config(fg='red')
        b = self.buttons[coord]
        b.state = MINE
        self.game.state = LOST
        n = self.game.mf.mines_grid[coord]
        b.set_image('mine{}red'.format(n))
        self.face_button.config(image=self.face_images['lost1'])
        for c, b in [(btn.coord, btn) for btn in self.buttons.values()
            if btn.state != CLICKED]:
            n = self.game.mf.mines_grid[c]
            # Check for incorrect flags.
            if b.state == FLAGGED and n != b.num_of_flags:
                b.set_image('cross{}'.format(b.num_of_flags))
            # Reveal remaining mines.
            elif b.state == UNCLICKED and self.game.mf.mines_grid[c] > 0:
                b.state = MINE
                b.set_image('mine{}'.format(n))

    def init_highscores(self):
        menu_index = self.menubar.game_menu.items.index('Highscores')
        if self.diff == 'c' or self.lives > 1:
            if not self.highscores:
                return
            self.hs_key = self.highscores = None
            self.menubar.game_menu.entryconfig(menu_index, state='disabled')
            return
        self.menubar.game_menu.entryconfig(menu_index, state='normal')
        # Settings tuple - keys are alphabetical.
        settings = ['diff', 'drag_select', 'per_cell', 'lives', 'detection',
            'distance_to']
        # The key to be used in the dictionary must be a string to use json.
        self.hs_key = ','.join(
            map(lambda s: str(self.settings[s]), sorted(settings)))
        # No copy.
        self.highscores = self.all_highscores.setdefault(self.hs_key, [])
        # Only keep highscores with the correct key.
        for h in self.highscores[:]:
            if h['key'] != enchs(h, self.hs_key):
                self.highscores.remove(h)
                self.corrupt_highscores.setdefault(self.hs_key, []).append(h)

    def set_mines_counter(self):
        nr_found = sum([b.mines for b in self.buttons.values()])
        mines = self.mines if not self.is_create_mode else 0
        nr_rem = mines - nr_found
        self.mines_var.set('{:03d}'.format(abs(nr_rem)))
        if nr_rem < 0 and not self.is_create_mode:
            self.mines_label.config(bg='red', fg='black')
        else:
            self.mines_label.config(bg='black', fg='red')

    def refresh_board(self, event=None):
        super(GameGui, self).refresh_board()
        self.is_coloured = False
        self.probs = None
        self.won_game = None
        self.timer.start_time = None
        self.timer.pause_time = 0
        self.timer.set_var(0)
        n = min(3, self.lives)
        self.face_button.config(image=self.face_images['ready%s'%n])
        self.set_mines_counter()
        if self.hide_timer:
            self.timer.config(fg='black')

    def pause_game(self, event=None):
        if self.focus != self or self.game.state != ACTIVE:
            return
        self.paused = not(self.paused)
        if self.paused:
            self.game.mf.origin = KNOWN #not allowed on highscores
            self.unset_button_bindings()
            self.timer.paused = tm.time()
            y1, x1 = (10 + self.btn_size * i for i in self.dims)
            self.pause_cover = self.canvas.create_rectangle(10, 10, x1, y1,
                fill='grey94', width=0)
        else:
            self.set_button_bindings()
            self.canvas.delete(self.pause_cover)
            self.timer.pause_time += tm.time() - self.timer.paused
            self.game.pause_time = self.timer.pause_time
            self.timer.paused = False
            self.timer.update()

    def toggle_timer(self, event=None):
        if event:
            self.hide_timer = not(self.hide_timer)
        # Always show the timer if the game is lost or won.
        if self.hide_timer and self.game.state not in [WON, LOST]:
            self.timer.config(fg='black')
        else:
            self.timer.config(fg='red')

    def close_root(self):
        self.game.state = READY #so that settings can be updated
        self.update_settings()
        with open(join(direcs['main'], 'settings.cfg'), 'w') as f:
            json.dump(self.settings, f)
            # print "Saved settings."
        with open(join(direcs['data'], 'highscores.json'), 'w') as f:
            json.dump(self.all_highscores, f)
            print "Saved highscores."
        for i in self.corrupt_highscores.values():
            if len(i) > 0: #at least one corrupt highscore
                print "Saving corrupt highscores:"
                print self.corrupt_highscores
                with open(
                    join(direcs['data'], 'highscores_corrupt.json'), 'w') as f:
                    json.dump(self.corrupt_highscores, f)
                break
        super(GameGui, self).close_root()

    # Game menu methods.
    def start_new_game(self, event=None):
        self.game = Game(**self.settings)
        super(GameGui, self).start_new_game()

    def replay_game(self, event=None):
        self.refresh_board()
        self.game = Game(minefield=self.game.mf, **self.settings)

    def toggle_create_mode(self):
        self.is_create_mode = not(self.is_create_mode)
        if self.is_create_mode:
            self.flag_type = 'mine'
        else:
            self.flag_type = 'flag'
        self.start_new_game()

    def save_board(self):
        if not self.is_create_mode and self.game.mf.mines_grid is None:
            return
        if not isdir(join(direcs['boards'], 'saved')):
            os.mkdir(join(direcs['boards'], 'saved'))
        fname = '{} {}.mgb'.format(self.diff,
            tm.strftime('%d%b%Y %H.%M', tm.gmtime()))
        options = {
            'defaultextension': '.mgb',
            'filetypes': [('MineGauler Board', '.mgb')],
            'initialdir': join(direcs['boards'], 'saved'),
            'initialfile': fname,
            'parent': self,
            'title': 'Save MineGauler Board'
            }
        path = tkFileDialog.asksaveasfilename(**options)
        if not path: #canceled
            return
        if self.is_create_mode:
            mine_coords = [c for c, b in self.buttons.items()
                for i in range(b.mines)]
            minefield = Minefield(mine_coords, diff='c', dims=self.dims,
                per_cell=self.per_cell)
        else:
            minefield = self.game.mf
        minefield.serialise(path)

    def load_board(self):
        options = {
            'defaultextension': '.mgb',
            'filetypes': [('MineGauler Board', '.mgb')],
            'initialdir': join(direcs['main'], 'boards'),
            'parent': self,
            'title': 'Load MineGauler Board'
            }
        path = tkFileDialog.askopenfilename(**options)
        if not path: #canceled
            return
        mf = Minefield.deserialise(path)
        settings = self.settings
        settings.update(mf.settings)
        self.game = Game(minefield=mf, **settings)
        self.reshape(self.game.dims)
        # Set appropriate settings.
        for s in ['mines', 'per_cell', 'detection']:
            setattr(self, s, getattr(self.game, s))
            self.settings[s] = getattr(self.game, s)
        self.set_mines_counter()

    def show_info(self, event=None):
        if self.block_windows:
            self.focus.focus_set()
            return
        win = Window(self, 'Info')
        info = (
            "This {d[0]} x {d[1]} grid has {} mines with "
            "a max of {} per cell.\n"
            "Detection level: {},  Drag select: {},  Lives remaining: {}"
            ).format(self.mines, self.per_cell, self.detection,
                'on' if self.drag_select else 'off', self.game.lives_rem,
                d=self.dims)
        time = self.game.get_time_passed()
        if self.game.state == WON:
            info += (
                "\n\nIt has 3bv of {}.\n\n"
                "You completed it in {:.2f} seconds, with 3bv/s of {:.2f}."
                ).format(self.game.mf.bbbv, time+0.01,
                    self.game.get_3bvps())
        elif self.game.state == LOST:
            info += (
                "\n\nIt has 3bv of {}.\n\n"
                "You lost after {:.2f} seconds, completing {:.1f}%. The grid "
                "has a remaining 3bv of {}."
                ).format(self.game.mf.bbbv, time+0.01,
                    100*self.game.get_prop_complete(), self.game.get_rem_3bv())
            # In case mine was hit on first click (ZeroDivisionError).
            if self.game.get_prop_complete() > 0:
                info += (
                    "\n\nPredicted completion time "
                    "of {:.1f} seconds with a continued 3bv/s of {:.2f}."
                    ).format(time/self.game.get_prop_complete(),
                        self.game.get_3bvps())
        tk.Message(win.mainframe, width=300, text=info,
            font=self.msg_font).pack()
        win.make_btn('OK', lambda: self.close_window('Info'))
        self.focus = win.btns[0]
        self.focus.focus_set()

    def show_probs(self, event=None):
        # Reset previously coloured buttons.
        if self.is_coloured:
            for b in self.buttons.values():
                if b.state==UNCLICKED:
                    b.refresh()
                else:
                    b.prob_mine = None
            self.is_coloured = False
            self.probs = None
            return
        if (self.detection != 1 or self.distance_to or
            self.game.state not in [READY, ACTIVE]):
            return
        if not self.probs:
            self.probs = NrConfig(self.buttons, self.mines,
                self.per_cell, True).probs
            # cfg.print_info()
            # Check for invalid flag configuration.
            # if cfg.probs is None:
            #     return
        if self.game.state == ACTIVE:
            self.game.mf.origin = KNOWN
        self.is_coloured = True
        density = float(self.mines) / self.get_size()
        for coord, p in self.probs.items():
            b = self.buttons[coord]
            if p is None or b.state != UNCLICKED: #shouldn't need second cond
                continue
            text = str(int(p)) if p in [0, 1] else ''
            if not text and self.btn_size >= 24:
                text = "%.2f" % round(p, 2)
            if p >= density:
                ratio = (p - density)/(1 - density)
                colour = blend_colours(ratio)
            else:
                ratio = (density - p)/density
                colour = blend_colours(ratio, high_colour=(0, 255, 0))
            y0, x0 = [10 + (i + 1.0/16) * self.btn_size for i in coord]
            y1, x1 = [10 + (i + 15.0/16) * self.btn_size for i in coord]
            b.prob_fg = self.canvas.create_rectangle(x0, y0, x1, y1, width=0,
                fill=colour, tag='overlay')
            if text:
                b.text = self.canvas.create_text((x0 + x1)/2, (y0 + y1)/2 - 1,
                    font=('Times', int(0.2*self.btn_size + 3.7), 'normal'),
                    text=text, tag='overlay')

    def auto_flag(self, event=None):
        if (self.detection != 1 or self.distance_to or self.per_cell > 1 or
            self.game.state not in [ACTIVE, READY]):
            return
        self.probs = NrConfig(self.buttons, self.mines, self.per_cell,
            ignore_flags=True).probs
        self.game.mf.origin = KNOWN
        for coord, p in self.probs.items():
            b = self.buttons[coord]
            if p == 1 and b.state != FLAGGED:
                b.refresh()
                b.set_image('flag1life')
                b.state = MINE
                b.mines = 1
            elif p != 1 and b.state == FLAGGED:
                b.refresh()
        self.place_board_image()
        self.set_mines_counter()

    def auto_click(self, event=None):
        """Assumes flags are correct."""
        if self.game.state not in [ACTIVE, READY]:
            return
        if self.game.state == READY:
            # Click any cell.
            self.click(self.buttons.keys()[0])
            return
        if not self.probs:
            self.probs = NrConfig(self.buttons, self.mines,
                self.per_cell).probs
            self.game.mf.origin = KNOWN
            # Check for invalid flag configuration.
            # if cfg.probs is None:
            #     return
        if self.is_coloured:
            # After clicking, the colouring is incorrect.
            for b in self.buttons.values():
                if b.state == UNCLICKED:
                    b.refresh()
            self.is_coloured = False
        click_coords = filter(lambda c: self.probs[c] == 0, self.probs.keys())
        if not click_coords:
            prob_coords = filter(lambda c: self.probs[c], self.probs.keys())
            click = min(prob_coords, key=lambda c: self.probs[c])
            click_coords = [click]
        density = float(self.mines) / self.get_size()
        for c in click_coords:
            self.click(c, False)
        if self.is_complete():
            self.finalise_win()
            self.place_board_image()
        self.probs = None

    def get_highscores(self, name=None, order='time', flagging=None):
        all_hscores = self.highscores[:] #copy
        if flagging == 'NF':
            all_hscores = [h for h in all_hscores if h['flagging'] <= 0.1]
        elif flagging == 'F':
            all_hscores = [h for h in all_hscores if h['flagging'] > 0.1]
        all_hscores.sort(key=lambda x: float(x[order]))
        if order == '3bv/s':
            all_hscores.reverse()
        if self.name:
            all_hscores = [h for h in all_hscores
                if h['name'].lower() == self.name.lower()]
        else:
            names = ['']
            all_hscores2 = all_hscores[:] #copy
            all_hscores = []
            for h in all_hscores2:
                n = h['name'].lower()
                if n not in names or h == self.won_game:
                    all_hscores.append(h)
                    names.append(n)
        return all_hscores

    def show_highscores(self, event=None, order='time', flagging=None):
        self.submit_name_entry()
        if self.block_windows or self.lives > 1 or self.diff == 'c':
            self.focus.focus_set()
            return
        if not flagging:
            flagging = 'all'
        self.hs_order = order
        self.hs_flagging = flagging
        def close():
            if self.won_game and not self.won_game['name']:
                name = self.won_game['name'] = entry.get()[:20]
                self.won_game['key'] = enchs(self.won_game, self.hs_key)
                with open(
                    join(direcs['data'], 'highscores_copy.json'), 'w') as f:
                    json.dump(self.all_highscores, f)
                copy_file(join(direcs['data'], 'highscores_copy.json'),
                    join(direcs['data'], 'highscores.json'))
            self.close_window('Highscores')
        def set_name(event):
            name = self.won_game['name'] = event.widget.get()[:20]
            self.won_game['key'] = enchs(self.won_game, self.hs_key)
            self.focus = win.btns[0]
            self.focus.focus_set()
            with open(join(direcs['data'], 'highscores_copy.json'), 'w') as f:
                json.dump(self.all_highscores, f)
            copy_file(join(direcs['data'], 'highscores_copy.json'),
                join(direcs['data'], 'highscores.json'))
            row1, col1 = (tab1.entry.grid_info()[x] for x in ['row', 'column'])
            row2, col2 = (tab2.entry.grid_info()[x] for x in ['row', 'column'])
            tab1.entry.destroy()
            tab2.entry.destroy()
            tk.Label(tab1.table, text=name,
                font=('Times', 11, 'bold')).grid(row=row1, column=col1)
            tk.Label(tab2.table, text=name,
                font=('Times', 11, 'bold')).grid(row=row2, column=col2)
        def pack_hscores(flagging):
            self.focus = win.btns[0]
            for order, frame in [('time', tab1), ('3bv/s', tab2)]:
                all_hscores = self.get_highscores(self.name, order, flagging)
                if self.name:
                    hscores = all_hscores[:5]
                else:
                    hscores = all_hscores[:10]
                if (self.won_game and self.won_game not in hscores and
                    (not self.name or self.won_game['name'] == self.name)):
                    f = True if self.won_game['flagging'] > 0.1 else False
                    if (flagging == 'all' or (flagging == 'F' and f) or
                        (flagging == 'NF' and not f)):
                        hscores.append(self.won_game)
                # Create a frame to contain the gridded highscores.
                table = frame.table = tk.Frame(frame) #store in tab
                table.grid(row=2, column=2, sticky='n')
                if order == '3bv/s':
                    headings = ['3bv/s', '3bv', 'Time', 'Date']
                else:
                    headings = ['Time', '3bv', '3bv/s', 'Date']
                if not self.name:
                    headings.insert(0, 'Name')
                # Display the headings.
                for i, h in enumerate(headings):
                    tk.Label(table, text=h, font=('Times', 12, 'normal')).grid(
                        row=0, column=i+1)
                row = 1
                for hs in hscores:
                    font = 'bold' if hs == self.won_game else 'normal'
                    font = ('Times', 11, font)
                    if hs == self.won_game == hscores[-1]:
                        place = all_hscores.index(hs) + 1
                    else:
                        place = row
                    # Display position in highscores.
                    tk.Label(table, text=place, font=font, padx=10).grid(
                        row=row, column=0)
                    col = 1
                    for h in headings:
                        if h == 'Name' and not hs['name'] and hs == self.won_game:
                            self.focus = frame.entry = tk.Entry(table)
                            frame.entry.grid(row=row, column=col)
                            frame.entry.bind('<Return>', set_name)
                        elif h == 'Date':
                            text = tm.strftime('%d %b %Y %H:%M',
                                tm.localtime(hs['date']))
                            tk.Label(table, text=text, font=font).grid(
                                row=row, column=col)
                        else:
                            tk.Label(table, text=hs[h.lower()],
                                font=font).grid(row=row, column=col)
                        col += 1
                    row += 1
                self.focus.focus_set()
        def toggle_hscores():
            if self.hs_flagging == flagging_var.get():
                return
            self.hs_flagging = flagging_var.get()
            tab1.table.destroy()
            tab2.table.destroy()
            pack_hscores(self.hs_flagging)

        win = Window(self, 'Highscores')
        win.make_btn('OK', close)
        f1 = tk.Frame(win.mainframe, bd=2, relief='groove')
        f1.grid(row=2, column=1, sticky='ns')
        flagging_var = tk.StringVar()
        flagging_var.set(flagging)
        for tp in [('All', 'all'), ('Flagged', 'F'), ('Non-flagged', 'NF')]:
            tk.Radiobutton(f1, text=tp[0], value=tp[1], variable=flagging_var,
                indicatoron=False, command=toggle_hscores).pack(fill='x')
        container = ttk.Notebook(win.mainframe, takefocus=False)
        container.grid(row=2, column=2, sticky='nsew')
        container.enable_traversal()
        tab1 = tk.Frame(container)
        tab2 = tk.Frame(container)
        container.add(tab1, text='Time')
        container.add(tab2, text='3bv/s')
        tabID = 1 if order == '3bv/s' else 0
        container.select(tabID)

        if self.won_game:
            settings = self.game.settings
        else:
            settings = self.settings
        name_phrase = self.name + "'s " if self.name else ''
        intro = (
            "{}{} highscores with settings:\n" +
            "Max per cell = {}, Drag = {}\n").format(
                name_phrase, dict(diff_names)[settings['diff']],
                settings['per_cell'],
                settings['drag_select'])
        tk.Message(win.mainframe, width=300, text=intro,
            font=self.msg_font).grid(row=1, column=2)
        pack_hscores(flagging)

    def set_zoom(self, zoom=None):
        old_btn_size = self.btn_size
        super(GameGui, self).set_zoom(zoom)
        if old_btn_size != self.btn_size and self.game.state == ACTIVE:
            self.game.btn_size = None

    def toggle_resizable(self):
        self.is_resizable = not(self.is_resizable)
        self.resizable(self.is_resizable, self.is_resizable)

    def reset_to_default(self):
        self.set_zoom()
        for k, v in default_settings.items():
            setattr(self, k, v)
        self.settings = default_settings.copy()
        self.hide_timer = False
        self.timer.config(fg='red')
        self.first_success_var.set(self.first_success)
        self.lives_var.set(self.lives if self.lives in [1, 2, 3] else -1)
        self.drag_select_var.set(self.drag_select)
        self.per_cell_var.set(self.per_cell)
        self.diff_var.set(self.diff)
        # self.detection_var.set(self.detection)
        self.set_difficulty(self.diff, run=True) #also makes new game
        self.name_entry.config(state='normal')
        self.name_entry.delete(0, 'end')
        self.focus = self.name_entry
        self.focus.focus_set()

    # Options menu methods.
    def update_settings(self):
        if self.game.state in [WON, LOST]:
            return
        # Stored as 0 or 1 (boolean).
        self.first_success = int(self.first_success_var.get())
        self.settings['first_success'] = self.first_success
        if self.game.state == READY:
            # Stored as boolean for highscores.
            self.settings['drag_select'] = bool(self.drag_select_var.get())
            lives = self.lives_var.get()
            if lives == -1:
                lives = self.settings['lives']
            else:
                self.settings['lives'] = lives
            n = min(lives, 3)
            self.face_button.config(image=self.face_images['ready%s'%n])
            if self.game.mf.origin != KNOWN:
                self.settings['per_cell'] = self.per_cell_var.get()
                self.game = Game(**self.settings)
            else:
                for s in ['drag_select', 'lives']:
                    setattr(self.game, s, self.settings[s])
                self.game.lives_rem = self.game.lives
        for s in ['first_success', 'drag_select', 'lives', 'per_cell']:
            setattr(self, s, self.settings[s])
        self.init_highscores()

    def get_lives(self):
        # Don't change radiobutton yet.
        self.lives_var.set(self.lives if self.lives in [1, 2, 3] else -1)
        if self.block_windows:
            self.focus.focus_set()
            return
        def finish(event=None):
            lives = lives_entry.get()
            if not lives:
                self.lives = 1
            elif not lives.isdigit() or int(lives) < 1:
                return
            else:
                self.lives = int(lives)
            self.settings['lives'] = self.lives
            self.lives_var.set(self.lives if self.lives in [1, 2, 3] else -1)
            self.close_window('Lives')
            if self.game.state == READY:
                self.game.lives_rem = self.lives
                n = min(3, self.lives)
                self.face_button.config(image=self.face_images['ready%s'%n])

        title = 'Lives'
        win = Window(self, title)
        tk.Message(win.mainframe, width=150, text=(
            "Enter a number of lives."
            )).pack(pady=10)
        lives_entry = tk.Entry(win.mainframe, width=10, justify='center')
        lives_entry.pack()
        lives_entry.insert(0, self.lives)
        lives_entry.bind('<Return>', finish)
        win.make_btn('OK', finish)
        win.make_btn('Cancel', lambda: self.close_window(title))
        self.focus = lives_entry
        self.focus.focus_set()

    # Help menu methods.
    @defocus
    def show_text(self, filename, width=80, height=24):
        super(GameGui, self).show_text(filename, width, height)

    def retrieve_highscores(self):
        options = {
            'initialdir': dirname(direcs['main']),
            'mustexist': True,
            'parent': self,
            'title': ("Select the dist folder which contains the executable\n" +
                "(versions >= 1.1.2 only)")}
        old_direc = tkFileDialog.askdirectory(**options)
        if not old_direc:
            return
        error_msg = None
        if glob(join(old_direc, '*.exe')):
            # Try to get the old version from the old executable or info file.
            if PLATFORM == 'windows':
                ver_parser = win32com.client.Dispatch(
                    'Scripting.FileSystemObject')
                old_version = ver_parser.GetFileVersion(
                    glob(join(old_direc, '*.exe'))[0])
                # print old_version
            else:
                try:
                    with open(join(old_direc, 'files', 'info.txt'), 'r') as f:
                        old_version = json.load(f)['version']
                except:
                    error_msg = (
                        "Unknown version. Try running the old version first.")
                    old_version = BIG
            if LooseVersion(old_version) < '1.1.2':
                error_msg = ("Cannot retrieve highscores from versions " +
                    "older than 1.1.2.")
        else:
            error_msg = "Cannot find the required file."
        if error_msg:
            tkMessageBox.showerror('Retrieve highscores', error_msg)
        else:
            if LooseVersion(old_version) < '1.2':
                old_path = join(old_direc, 'files', 'data.txt')
            else:
                old_path = join(old_direc, 'files', 'highscores.json')
            # Save the highscores first so that none are lost when retrieving.
            with open(join(direcs['data'], 'highscores.json'), 'w') as f:
                json.dump(self.all_highscores, f)
            print old_version
            old_data = highscore_utils.update_format(old_path, old_version)
            # print len(old_data)
            self.all_highscores = highscore_utils.include_data(old_data,
                save=False)
            self.init_highscores()



class Timer(tk.Label, object):
    def __init__(self, parent):
        self.var = tk.StringVar()
        self.set_var(0)
        super(Timer, self).__init__(parent, bg='black', fg='red', bd=5,
            relief='sunken', font=('Verdana',11,'bold'), textvariable=self.var)
        self.start_time = None
        self.pause_time = 0
        self.paused = False

    def __repr__(self):
        return "<Timer object inheriting from Tkinter.Label>"

    def update(self, start_time=None):
        # A start time is passed in if Timer is being started.
        if start_time:
            self.start_time = start_time
        # Timer updates if it has been started. It is stopped by setting
        # self.start_time to None.
        if self.start_time and not self.paused:
            elapsed = tm.time() - self.start_time - self.pause_time
            self.set_var(elapsed)
            self.after(100, self.update)

    def set_var(self, time):
        if time == 0:
            self.var.set('000')
        else:
            self.var.set('{:03d}'.format(min(int(time) + 1, 999)))




if __name__ == '__main__':
    try:
        with open(join(direcs['main'], 'settings.cfg'), 'r') as f:
            settings = json.load(f)
        # print "Imported settings."
        # print "Imported settings: ", settings
    except:
        settings = default_settings
    # Check for corrupt info.txt file and ensure it contains the version number.
    with open(join(direcs['files'], 'info.txt'), 'w') as f:
        json.dump({'version': VERSION}, f)
    # Create and run the GUI.
    g = GameGui(**settings)
    g.mainloop()
