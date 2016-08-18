# Button states are:
#     UNCLICKED
#     CLICKED
#     FLAGGED
#     MINE

# Drag-and-select flagging types are:
#     FLAG
#     UNFLAG

import sys
import os
from os.path import join
import Tkinter as tk
import tkFileDialog, tkMessageBox
from PIL import Image as PILImage, ImageTk
import time as tm
import json
from glob import glob

import numpy as np

from constants import * #version, platform etc.
from utils import direcs, where_coords
from gui import BasicGui, MenuBar, Window
from game import Game, Minefield

if PLATFORM == 'win32':
    import win32com.client

__version__ = VERSION

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

nr_font = ('Tahoma', 9, 'bold')
msg_font = ('Times', 10, 'bold')


class GameGui(BasicGui):
    def __init__(self, **kwargs):
        super(GameGui, self).__init__(**kwargs)
        self.hide_timer = False
        # Create a minefield stored within the game.
        self.start_new_game()

    # Make the GUI.
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

    def make_menubar(self):
        super(GameGui, self).make_menubar()
        menu = self.menubar
        i = menu.game_items.index('New') + 1 - len(menu.game_items)
        menu.add_item('game', 'command', 'Replay', i,
            command=self.replay_game)
        menu.add_item('game', 'command', 'Save board', i,
            command=self.save_board)
        menu.add_item('game', 'command', 'Load board', i,
            command=self.load_board)
        menu.add_item('game', 'separator', index=i)
        menu.add_item('game', 'command', 'Current info', i,
            command=self.show_info, accelerator='F4')
        self.bind('<F4>', self.show_info)

        self.first_success_var = tk.BooleanVar()
        self.first_success_var.set(self.first_success)
        menu.add_item('opts', 'checkbutton', 'FirstAuto', 0,
            variable=self.first_success_var, command=self.update_settings)

        menu.add_item('help', 'separator')
        menu.add_item('help', 'command', 'Basic rules',
            command=lambda: self.show_text('rules'))
        menu.add_item('help', 'command', 'Special features',
            command=lambda: self.show_text('features'))
        menu.add_item('help', 'command', 'Tips',
            command=lambda: self.show_text('tips'))

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
                b.fg = self.set_cell_image(coord, self.btn_images['down'])

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
            self.buttons[prev_coord].refresh()
        if coord:
            self.left_press(coord)

    def right_press(self, coord):
        super(GameGui, self).right_press(coord)
        b = self.buttons[coord]
        if b.state == UNCLICKED:
            b.incr_flags()
        elif b.state == FLAGGED:
            b.refresh()
        # Check whether drag-clicking should flag or unflag if drag is on.
        if self.drag_select:
            if b.state == UNCLICKED:
                self.drag_flag = UNFLAG
            elif b.state == FLAGGED:
                self.drag_flag = FLAG
            else:
                self.drag_flag = None
        else:
            self.drag_flag = None
        self.set_mines_counter()

    def right_motion(self, coord, prev_coord):
        super(GameGui, self).right_motion(coord, prev_coord)
        # Do nothing if leaving the board.
        if not coord:
            return
        b = self.buttons[coord]
        if self.drag_flag == FLAG and b.state == UNCLICKED:
            b.incr_flags()
        elif self.drag_flag == UNFLAG and b.state == FLAGGED:
            b.refresh()
        self.set_mines_counter()

    def both_press(self, coord):
        super(GameGui, self).both_press(coord)
        self.face_button.config(image=self.face_images['active1face'])
        b = self.buttons[coord]
        if b.state == UNCLICKED:
            b.refresh()
        # Buttons which neighbour the current selected button.
        nbrs = self.get_nbrs(coord, include=True)
        # Sink the new neighbouring buttons.
        for c in nbrs:
            b = self.buttons[c]
            if b.state == UNCLICKED:
                b.fg = self.set_cell_image(c, self.btn_images['down'])

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
        for c in {c for c in nbrs if self.buttons[c].state == UNCLICKED}:
            self.buttons[c].refresh()
        # Reset face.
        if self.game.state in [READY, ACTIVE]:
            self.face_button.config(image=self.face_images['ready1face'])

    def both_motion(self, coord, prev_coord):
        super(GameGui, self).both_motion(coord, prev_coord)
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

    # GUI and game methods.
    def click(self, coord, check_for_win=True):
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
        nr = self.game.mf.completed_grid.item(coord)
        # Assign the game grid with the numbers which are uncovered.
        self.game.grid.itemset(coord, nr)
        b.fg = self.set_cell_image(coord, self.btn_images[nr])
        b.state = CLICKED
        b.nr = nr

    def finalise_win(self):
        self.game.finish_time = tm.time()
        self.unset_button_bindings()
        self.timer.start_time = None
        self.game.state = WON
        self.face_button.config(image=self.face_images['won1face'])
        for b in self.buttons.values():
            if b.state in [UNCLICKED, FLAGGED]:
                n = b.num_of_flags = self.game.mf.mines_grid[b.coord]
                b.fg = self.set_cell_image(b.coord, self.flag_image)
                b.state = FLAGGED
        self.timer.set_var(min(int(self.game.get_time_passed() + 1), 999))
        self.timer.config(fg='red')
        self.mines_var.set('000')

    def finalise_loss(self, coord):
        self.game.finish_time = tm.time()
        self.unset_button_bindings()
        self.timer.start_time = None
        b = self.buttons[coord]
        b.state = MINE
        self.game.state = LOST
        b.fg = self.set_cell_image(coord, self.mine_image_red)
        self.face_button.config(image=self.face_images['lost1face'])
        for c, b in [(btn.coord, btn) for btn in self.buttons.values()
            if btn.state != CLICKED]:
            # Check for incorrect flags.
            if b.state == FLAGGED and self.game.mf.mines_grid[c] == 0:
                self.board.delete(b.fg)
                b.fg = self.set_cell_image(c, image=self.cross_image)
            # Reveal remaining mines.
            elif b.state == UNCLICKED and self.game.mf.mines_grid[c] > 0:
                b.state = MINE
                b.fg = self.set_cell_image(c, self.mine_image)
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

    def refresh_board(self, event=None):
        super(GameGui, self).refresh_board()
        self.timer.start_time = None
        self.timer.set_var(0)
        self.face_button.config(image=self.face_images['ready1face'])
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

    def close_root(self):
        self.update_settings()
        with open(join(direcs['main'], 'settings.cfg'), 'w') as f:
            json.dump(self.settings, f)
            # print "Saved settings."
        super(GameGui, self).close_root()

    # Game menu methods.
    def start_new_game(self):
        self.game = Game(**self.settings)
        super(GameGui, self).start_new_game()

    def replay_game(self):
        self.refresh_board()
        self.game = Game(minefield=self.game.mf, **self.settings)

    def save_board(self):
        if self.game.mf.mines_grid is None:
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
        if path:
            self.game.serialise(path)

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
        for s in ['mines']:
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
            "Detection level: {},  Drag select: {}"
            ).format(self.mines, self.per_cell, self.detection,
                'on' if self.drag_select else 'off',
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
            font=('Times', 10, 'bold')).pack()
        win.make_btn('OK', lambda: self.close_window('Info'))
        self.focus = win.btns[0]
        self.focus.focus_set()

    # Options menu methods.
    def update_settings(self):
        self.first_success = self.first_success_var.get()
        self.drag_select = self.drag_select_var.get()
        for k in default_settings:
            self.settings[k] = getattr(self, k)



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



if __name__ == '__main__':
    try:
        with open(join(direcs['main'], 'settings.cfg'), 'r') as f:
            settings = json.load(f)
        # print "Imported settings."
        #print "Imported settings: ", settings
    except:
        settings = default_settings
    # Ensure info.txt file contains the version number.
    try:
        with open(join(direcs['files'], 'info.txt'), 'r') as f:
            json.load(f)['version']
    except:
        with open(join(direcs['files'], 'info.txt'), 'w') as f:
            json.dump({'version': VERSION}, f)
    print settings
    # Create and run the GUI.
    GameGui(**settings).mainloop()