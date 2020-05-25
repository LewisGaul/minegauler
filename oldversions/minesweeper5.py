"""
Contains class for minesweeper fields, which has a size attribute. The following
are equivalent: beginner/b/1/(8,8), intermediate/i/2/(16,16), expert/e/3/(16,30).
It has functions to create (manually using Tkinter or randomly) the grid of mines,
and to play the game (again using Tkinter). There are also options to have a
maximum number of mines per cell greater than 1 and to have the numbers display
the number of mines in cells adjacent by more than one cell. Function _3bv() finds
the 3bv of the grid. Threading provides the option to play while leaving the shell active.
The play() function has become a Game() class which inherits from the Minefield() class.
Changed some functions' names to ensure all are verbs.
Added menu to Tkinter window.
Added combined click action.
Added single click and drag select option.
Added change lives option.
Added highscores and settings to be stored.
Added hide timer option.

New:
Added attribute 'game_state' in the Game play() method, which is used instead of making the grid a grid of zeros. Allows information for the end grid to be used.
Added proportion complete to show_info() for lost games and congratulations message to show_highscores() for best time.

To add:
Get images for flags etc.
Ensure double left clicking does not interfere and works with drag click.
-Stop clicking clicked cells doing anything - unbind and command=None.
Add zoom (Game menu).
-Add option to double click and drag to click multiple cells.
Check replay(/new) action.
Improve display_grid (integrate).
Add third dimension(!).
"""

import os.path
import threading
import time as tm
from Tkinter import *

import numpy as np


directory = os.path.dirname(__file__)
default_settings = {'per_cell': 1, 'first_success': False, 'mines': 10, 'detection': 1, 'shape': (8, 8), 'difficulty': 'b', 'lives': 1, 'drag_click': 'off'}
settings_order = ['difficulty', 'type', 'per_cell', 'detection', 'drag_click', 'lives']
highscore_order = ['Name', 'type', '3bv', 'other', 'Date']
detection_options = dict([('1', 1), ('2', 2), ('3', 3)] + [(str(i), i) for i in [0.5, 1.5, 1.8, 2.2, 2.8]])
default_mines = {(8,8):10, (16,16):40, (16,30):99, (30,16):99}
detection_mines = {
            ('b', 0.5): 10, ('b', 1): 10, ('b', 1.5): 8, ('b', 1.8): 6,
            ('b', 2): 6, ('b', 2.2): 5, ('b', 2.8): 4, ('b', 3): 4,
            ('i', 0.5): 40, ('i', 1): 40, ('i', 1.5): 35, ('i', 1.8): 25,
            ('i', 2): 25, ('i', 2.2): 20, ('i', 2.8): 16, ('i', 3): 16,
            ('e', 0.5): 99, ('e', 1): 99, ('e', 1.5): 85, ('e', 1.8): 70,
            ('e', 2): 65, ('e', 2.2): 50, ('e', 2.8): 40, ('e', 3): 40}
shape_difficulty = {(8,8):'b', (16,16):'i', (16,30):'e', (30,16):'e'}
difficulty_shape = {'b':(8,8), 'i':(16,16), 'e':(16,30)}
difficulties_list = [('b', 'Beginner'), ('i', 'Intermediate'), ('e', 'Expert'), ('c', 'Custom')]
colours = dict([(1,'blue'),
                (2,'#%02x%02x%02x'%(0,150,0)),
                (3,'red'),
                (4,'#%02x%02x%02x'%(0,0,120)),
                (5,'brown'),
                (6,'turquoise'),
                (7,'black'),
                (8,'#%02x%02x%02x'%(120,120,120)),
                (9,'#%02x%02x%02x'%(238,150,14)),
                (10,'#%02x%02x%02x'%(200,0,200)),
                (11,'#%02x%02x%02x'%(80,160,120))])
cellfont = ('Times', 9, 'bold')
mineflags = ["F", "B", "C", "D", "E", "G", "H", "J", "K", "M"]
minesymbols = ['*', ':', '%', '#', '&', '$']

class Minefield(object):
    def __init__(self, shape=(16,30), per_cell=1, detection=1, create='auto'):
        if type(shape) is str:
            shape = shape.lower()
        if shape in ['b', 'beginner', 1, 'easy']:
            self.shape = (8, 8)
        elif shape in ['i', 'intermediate', 2, 'medium']:
            self.shape = (16, 16)
        elif shape in ['e', 'expert', 3, 'difficult']:
            self.shape = (16, 30)
        elif type(shape) is tuple and len(shape) == 2:
            self.shape = shape
        else:
            print "Invalid shape, enter 2-tuple of integers."
            sys.exit()
        self.size = self.shape[0]*self.shape[1]
        self.per_cell = per_cell
        self.detection = detection

        self.mines_grid = np.zeros(self.shape, int)
        self.final_grid = np.zeros(self.shape, int)
        if create == 'auto':
            self.create()
        elif create == 'manual':
            self.create_manually()

    def __str__(self):
        return ("The field has dimensions {} x {} with {n} mines and 3bv of {b}:\n".format(
                            *self.shape, n=self.mines_grid.sum(), b=self.get_3bv())
                    + prettify_grid(self.final_grid))

    def __repr__(self):
        return "<{}x{} minefield with {n} mines>".format(*self.shape, n=self.mines_grid.sum())

    def create(self, mines='default', overwrite=False, prop=None):
        #If overwrite is set to True and prop is given then prop will be used to calculate the number of mines.
        if not overwrite and self.mines_grid.any():
            print "Grid already created and overwrite is set to False."
            return
        #Only works for 2D.
        elif type(mines) is np.ndarray or (np.array(mines).ndim == 2 and len(mines[0] != 2)):
            self.mines_grid = mines
            self.per_cell = max(mines.max(), self.per_cell)
            self.shape = mines.shape
            self.size = mines.size
            mines = -1
        elif type(mines) in [set, list]:
            for c in list(mines):
                self.mines_grid.itemset(c, list(mines).count(c))
            self.per_cell = max(self.mines_grid.max(), self.per_cell)
        elif type(prop) in [int, float] and prop > 0 and prop < 1:
            mines = int(round(self.size*prop, 0))
        elif (mines not in range(1, self.size*self.per_cell) and self.shape in shape_difficulty and (shape_difficulty[self.shape], self.detection) in detection_mines):
            mines = detection_mines[(shape_difficulty[self.shape], self.detection)]
        elif mines not in range(1, self.size*self.per_cell):
            prop = 0.19/self.detection
            mines = int(round(float(self.size)*prop, 0))

        if mines in range(1, self.size*self.per_cell):
            if self.per_cell == 1:
                permute = np.ones(mines, int)
                permute.resize(self.size)
                self.mines_grid = np.random.permutation(permute).reshape(self.shape)
            else:
                self.mines_grid = np.zeros(self.shape, int)
                while self.mines_grid.sum() < mines:
                    cell = np.random.randint(self.size)
                    old_val = self.mines_grid.item(cell)
                    if old_val < self.per_cell:
                        self.mines_grid.itemset(cell, old_val + 1)

        self.mines = mines
        self.mine_coords = set(map(tuple, np.transpose(np.nonzero(self.mines_grid>0))))
        self.get_final_grid()
        self.find_zero_patches()

    def create_manually(self, overwrite=False):
        if not overwrite and self.mines_grid.any():
            print "Grid already created and overwrite is set to False."
            return

        grid = -np.ones(self.shape, int)

        def quitfunc():
            self.mines_grid = np.zeros(self.shape, int)
            root.destroy()

        def clearfunc():
            self.mines_grid *= 0
            grid = -np.ones(self.shape, int)
            for b in buttons.values():
                reset_button(b, buttontexts[b])
                mines_var.set("000")

        def leftclick(coord):
            def action():
                b = buttons[coord]
                #Should work on the mine the mouse ends over.
                if grid[coord] >= -1:
                    b['relief'] = 'sunken'
                    b['bd'] = 0.5
                    grid[coord] += 1
                    if grid[coord] > 0:
                        buttontexts[b].set(grid[coord])
                        try:
                            b['fg'] = colours[grid[coord]]
                        except KeyError:
                            b['fg'] = 'black'
            return action

        def rightclick(coord):
            def action(event):
                b = buttons[coord]
                if grid[coord] == -1:
                    buttontexts[b].set("F")
                    self.mines_grid[coord] = 1
                    grid[coord] = -9
                elif grid[coord] < -1 and grid[coord] > -9*self.per_cell:
                    buttontexts[b].set(mineflags[-grid[coord]/9])
                    self.mines_grid[coord] += 1
                    grid[coord] -= 9
                else:
                    reset_button(b, buttontexts[b])
                    self.mines_grid[coord] = 0
                    grid[coord] = -1
                mines_var.set("%03d" % self.mines_grid.sum())
            return action

        topfont = ('Times', 10, 'bold')
        root = Tk()
        root.title("MineGauler")
        topframe = Frame(root)
        topframe.pack(side='top', pady=2)
        Button(topframe, bd=4, text="Done", font=topfont,
                  command=root.destroy).grid(row=0, column=1, padx=5)
        Button(topframe, bd=4, text="Clear", font=topfont,
                  command=clearfunc).grid(row=0, column=2, padx=5)
        Button(topframe, bd=4, text="Quit", font=topfont,
                  command=quitfunc).grid(row=0, column=3, padx=5)
        mines_var = StringVar()
        mines_var.set("000")
        Label(topframe, bd=1, fg='red', bg='black', textvariable=mines_var,
                 font=('Verdana', 12, 'bold'), padx=6).grid(row=0, column=0)

        mainframe = Frame(root)
        mainframe.pack()
        frames = make_frames_grid(mainframe, self.shape)
        buttons = dict()
        buttontexts = dict()
        for coord in sorted(list(frames)):
            btext = StringVar()
            b = Button(frames[coord], bd=2.4, takefocus=0, textvariable=btext, font=cellfont, command=leftclick(coord))
            buttons[coord] = b
            #Make the button fill the frame (stick to all sides).
            b.grid(sticky='NSEW')
            #Add the action when right click occurs.
            b.bind('<Button-3>', rightclick(coord))
            #Store the btext variable in a dictionary with the button instance as the key.
            buttontexts[b] = btext

        mainloop()

        self.mine_coords = set(map(tuple, np.transpose(np.nonzero(self.mines_grid>0))))
        self.get_final_grid()
        self.find_zero_patches()
        ##DispThread(threading.active_count(), self, (self.final_grid,)).start()
        prettify_grid(self.final_grid, 1)

    def get_final_grid(self):
        if self.mines_grid.size == 1:
            return
        self.final_grid = -9 * self.mines_grid
        for coord in np.transpose(np.nonzero(~(self.mines_grid>0))):
            entry = 0
            for k in self.get_neighbours(tuple(coord), self.detection):
                if self.mines_grid[k] > 0:
                    entry += self.mines_grid[k]
            x = self.final_grid.itemset(tuple(coord), entry)
        return self.final_grid

    def get_neighbours(self, coord, dist=1, include=False):
        d = int(dist) if dist % 1 == 0 else int(dist) + 1
        i, j = coord
        x, y = self.shape
        row = [u for u in range(i-d, i+1+d) if u in range(x)]
        col = [v for v in range(j-d, j+1+d) if v in range(y)]
        if dist % 1 > 0.5:
            neighbours = {(u, v) for u in row for v in col
                          if abs(u-i) + abs(v-j) < 2*d}
        elif dist % 1 != 0:
            neighbours = {(u, v) for u in row for v in col
                          if abs(u-i) + abs(v-j) <= d}
        else:
            neighbours = {(u, v) for u in row for v in col}
        if not include:
            ##The given coord is not included.
            neighbours.remove(coord)
        return neighbours

    def find_zero_patches(self):
        zero_coords = set(map(tuple, np.transpose(np.nonzero(self.final_grid==0))))
        check = set()
        found_coords = set()
        patches = []
        while len(zero_coords.difference(found_coords)) > 0:
            cur_patch = set()
            check.add(list(zero_coords.difference(found_coords))[0])
            while len(check) > 0:
                found_coords.update(check) #Same as |= (below)
                coord = check.pop()
                cur_patch.add(coord)
                cur_patch |= self.get_neighbours(coord, self.detection)
                check |= self.get_neighbours(coord, self.detection) & (zero_coords - found_coords)
            patches.append(cur_patch)
        self.zero_patches = patches
        return patches

    def get_3bv(self):
        clicks = len(self.find_zero_patches())
        exposed = len({c for patch in self.zero_patches for c in patch})
        clicks += self.size - len(self.mine_coords) - exposed
        return clicks


class Game(Minefield):
    def __init__(self, play=True):
        try:
            with open(os.path.join(directory, 'Settings.txt'), 'r') as f:
                settings = eval(f.read())
        except:
            settings = default_settings
        # print "Imported settings: ", settings
        for s in settings:
            setattr(self, s, settings[s])
        self.visitor = False
        self.settings = {'per_cell': self.per_cell, 'first_success': self.first_success, 'mines': self.mines, 'detection': self.detection, 'shape': self.shape, 'difficulty': self.difficulty, 'lives': self.lives, 'drag_click': self.drag_click, 'visitor': self.visitor}
        #Necessary??
        if self.difficulty != 'c':
            shape = self.difficulty
        else:
            shape = self.shape
        super(Game, self).__init__(shape, per_cell=self.per_cell, detection=self.detection)

        self.highscores = dict()
        try:
            for d in ['Beginner', 'Intermediate', 'Expert']:
                with open(os.path.join(directory, d, 'highscores.txt'), 'r') as f:
                    self.highscores.update(eval(f.read()))
        except:
            pass #Will be created when needed.

        if play:
            self.play(self.mines)

    def __str__(self):
        return ("This {} x {} game has {n} mines and 3bv of {b}:\n".format(*self.shape, n=self.mines, b=self.get_3bv()) + prettify_grid(self.final_grid))

    def __repr__(self):
        return "<{}x{} MineGauler game with {n} mines>".format(*self.shape, n=self.mines_grid.sum())

    def thread_play(self, mines='default'):
        ##Only works once per running...?
        PlayThread(threading.active_count(), self, (mines,)).start()
        tm.sleep(2)
        print ">>> ",

    def play(self, mines='default', first_success=False):
        self.grid = -np.ones(self.shape, int)
        self.time_passed = None
        self.leftbuttondown, self.rightbuttondown = False, False
        self.coord_leftclicked, self.coord_rightclicked = None, None
        self.original_coord, self.coord_flagged = None, None
        self.blockclick, self.score_checked = False, False
        self.grid_was_created, self.grid_was_replayed = False, False
        self.game_state = 'ready'
        delete_attrs = []

        def click(coord):
            b = buttons[coord]
            b['relief'] = 'sunken'
            b['bd'] = 0.5
            if self.final_grid[coord] != 0:
                try:
                    b['fg'] = colours[self.final_grid[coord]]
                except KeyError:
                    b['fg'] = 'black'
                buttontexts[b].set(self.final_grid[coord])
            self.grid.itemset(coord, self.final_grid[coord])

        def new(reset=True):
            if create_var.get():
                create_game(reset)
                return
            #Needed for set_detection() so we know the game is stopped.
            self.start = 0
            self.score_checked = False
            if per_cell_var.get() > 0:
                self.per_cell = per_cell_var.get()
            set_detection(create=False)
            self.create(self.mines, overwrite=1)
            self.grid_was_created, self.grid_was_replayed = False, False
            replay(reset, new=True)

        def create_game(reset=True):
            #Only implement if create_var is true.
            if create_var.get():
                self.game_state = 'create'
                self.mines_grid = np.zeros(self.shape, int)
                self.mine_coords = set()
                self.mines = 0
                if reset:
                    for coord in buttons:
                        reset_button(buttons[coord], buttontexts[buttons[coord]])
                self.grid = -np.ones(self.shape, int)
                self.start = 0
                timer_var.set("000")
                mines_var.set("%03d" % self.mines_grid.sum())
                if per_cell_var.get() > 0:
                    self.per_cell = per_cell_var.get()
                self.detection = detection_options[detection_var.get()]
                new_button_frame.forget()
                timer_label.forget()
                done_button.pack(side='left')
                first_success_var.set(False)
            else:
                self.create(self.mines, overwrite=1)
                self.grid_was_created, self.grid_was_replayed = False, False
                self.game_state = 'ready'
                replay(new=True)
                done_button.forget()
                new_button_frame.pack(side='left')
                timer_label.pack(side='left')

        def show_info():
            try:
                if self.focus.bindtags()[1] == 'Entry' or self.focus.title() == 'Info':
                    self.focus.focus_set()
                    return
            except TclError:
                #self.focus has been destroyed.
                pass
            if not self.start:
                if per_cell_var.get() > 0:
                    self.per_cell = per_cell_var.get()
                self.first_success = first_success_var.get()
                self.detection = detection_options[detection_var.get()]
            self.focus = info_window = Toplevel(root)
            info_window.title('Info')
            if create_var.get():
                #Improve this.
                self.detection = float(detection_var.get())
                created_minefield = Minefield(self.shape, self.per_cell, self.detection, create=False)
                created_minefield.mines_grid = np.where(self.grid<-1, -self.grid/9, 0)
                created_minefield.mine_coords = set(map(tuple, np.transpose(np.nonzero(self.mines_grid>0))))
                created_minefield.get_final_grid()
                m = created_minefield
            else:
                m = self
            info = "This {} x {} grid has {n} mines (max of {p} per cell)\nand 3bv of {b} with detection level {d}.".format(*self.shape, p=self.per_cell, n=m.mines_grid.sum(), b=m.get_3bv(), d=self.detection)
            if self.game_state == 'won':
                info += "\n\nYou completed it in {:.2f} seconds, with 3bv/s of {:.2f}.".format(self.time_passed+0.005, self.get_3bv()/self.time_passed+0.005)
            elif self.game_state == 'lost':
                lost_field = Minefield(shape=self.shape, detection=self.detection, create=False)
                lost_field.mine_coords = set(map(tuple, np.transpose(np.nonzero(self.mines_grid>0))))
                lost_field.final_grid = np.where(self.grid < 0, self.final_grid, 1)
                rem_3bv = lost_field.get_3bv()
                already_found = {c for c in set(map(tuple, np.transpose(np.nonzero(self.grid >= 0)))) if c not in [i for p in lost_field.zero_patches for i in p]}
                rem_3bv -= len(already_found)
                prop_complete = float(self.get_3bv()-rem_3bv)/self.get_3bv()
                info += "\n\nYou were {:.1f}% complete with a remaining 3bv of {}.\nIf completed your predicted time would be\n{:.1f} seconds with a continued 3bv/s of {:.2f}.".format(100*prop_complete, rem_3bv, self.time_passed/prop_complete, prop_complete*self.get_3bv()/self.time_passed)
            Label(info_window, text=info, font=('Times', 11, 'bold')).pack()

        def show_highscores(settings=None, flagging=None, window=None):
            try:
                if self.focus.bindtags()[1] == 'Entry':
                    self.focus.focus_set()
                    return
            except TclError:
                pass
            if not settings:
                if not self.start:
                    if per_cell_var.get() > 0:
                        self.per_cell = per_cell_var.get()
                    self.first_success = first_success_var.get()
                    self.detection = detection_options[detection_var.get()]
                if self.difficulty == 'c':
                    return
                settings = [self.difficulty, 'Time']
                for s in settings_order[2:]:
                    settings.append(getattr(self, s))
                settings = tuple(settings)

            if not window:
                self.focus = window = Toplevel(root)
                window.title('Highscores')
                #window.resizable(False, False)
            else:
                self.focus = window
            headings = highscore_order
            headings[1] = settings[1]
            headings[3] = '3bv/s' if headings[1] != '3bv/s' else 'Time'
            #Funny business.
            if self.lives > 1 and 'Lives remaining' not in headings:
                headings.insert(-1, 'Lives remaining')
            elif self.lives == 1 and 'Lives remaining' in headings:
                headings.remove('Lives remaining')

            diff = dict(difficulties_list)[settings[0]].lower()
            flag = 'non-flagged ' if flagging == 'NF' else ('flagged ' if flagging == 'F' else '')
            lives = ', Lives = %s\n' % self.lives if self.lives > 1 else '\n'
            intro = "{1} highscores for {f}{d} with:\nMax per cell = {2}, Detection = {3}, Drag = {4}{L}".format(*settings, d=diff, f=flag, L=lives)
            Label(window, text=intro, font=('times', 12, 'normal')).grid(row=1, column=0, columnspan=len(headings)+1)
            for i in headings:
                Label(window, text='Lives left' if i == 'Lives remaining' else i).grid(row=2, column=headings.index(i)+1)

            index = None
            if settings in self.highscores:
                for index in range(len(self.highscores[settings])):
                    if self.highscores[settings][index]['Mines grid'] == self.mines_grid.tolist():
                        break #index found
                else:
                    index = None
            if index == 0 and settings[1] == 'Time':
                Label(window, padx=10, pady=10, bg='yellow', text="Congratulations, you set a new\nall-time MineGauler time record\nfor these settings!!", font=('Times', 12, 'bold')).grid(row=0, columnspan=len(headings)+1)
            highscores = [] if settings not in self.highscores else [d for d in self.highscores[settings] if not flagging or d['Flagging'] == flagging]
            if self.visitor:
                highscores = [d for d in highscores if 'siwel' not in d['Name'].lower()]
            def set_name(event):
                name = event.widget.get()
                self.highscores[settings][index]['Name'] = name
                row = event.widget.grid_info()['row']
                event.widget.destroy()
                Label(window, text=name, font=('times', 9, 'bold')).grid(row=row, column=1)
                self.focus = window
                if settings[1] == 'Time':
                    set_highscore(htype='3bv/s', entry=self.highscores[settings][index])
                #Do not overwrite the main file until data is stored in other file.
                with open(os.path.join(directory, dict(difficulties_list)[self.difficulty], 'highscores.txt'), 'r') as f:
                    old_highscores = f.read()
                with open(os.path.join(directory, dict(difficulties_list)[self.difficulty], 'highscorescopy.txt'), 'w') as f:
                    f.write(old_highscores)
                with open(os.path.join(directory, dict(difficulties_list)[self.difficulty], 'highscores.txt'), 'w') as f:
                    f.write(str(dict([(k, v) for (k, v) in self.highscores.items() if k[0] == self.difficulty])))
            row = 3
            for d in highscores:
                font = ('Times', 10, 'bold') if d['Mines grid'] == self.mines_grid.tolist() else ('Times', 10, 'normal')
                Label(window, text=row-2, font=font).grid(row=row, column=0)
                col = 1
                for i in headings:
                    if i == 'Name' and not d[i] and d['Mines grid'] == self.mines_grid.tolist():
                        self.focus = e = Entry(window)
                        e.grid(row=row, column=col)
                        e.bind('<Return>', set_name)
                    else:
                        Label(window, text=d[i], font=font).grid(row=row, column=col)
                    col += 1
                row += 1
                if row == 13:
                    break
            #If new highscore but not in top 10 of visitors scores:
            if self.visitor and self.focus.bindtags()[1] != 'Entry' and index:
                d = self.highscores[settings][index]
                font = ('Times', 10, 'bold')
                Label(window, text=highscores.index(d)+1, font=font).grid(row=13, column=0)
                col = 1
                for i in headings:
                    if i == 'Name' and not d[i]:
                        self.focus = e = Entry(window)
                        e.grid(row=13, column=col)
                        e.bind('<Return>', set_name)
                    else:
                        Label(window, text=d[i], font=font).grid(row=row, column=col)
                    col += 1

            lower_frame = Frame(window)
            lower_frame.grid(row=14, column=0, columnspan=len(headings)+1)
            def change_flagging():
                for w in window.children.values():
                    w.destroy()
                flagging = None if flagging_var.get() == 'None' else flagging_var.get()
                show_highscores(settings, flagging, window=window)
            flagging_var = StringVar()
            flagging_var.set(str(flagging))
            for i in [('All', 'None'), ('Flagged', 'F'), ('Non-flagged', 'NF')]:
                Radiobutton(lower_frame, text=i[0], font=('times', 10, 'bold'), value=i[1], variable=flagging_var, command=change_flagging).pack(side='left')
            def change_type():
                ####Add in self.visitor=True action.
                new_settings = list(settings)
                new_settings[1] = '3bv/s' if new_settings[1] == 'Time' else 'Time'
                for w in window.children.values():
                    w.destroy()
                show_highscores(tuple(new_settings), flagging, window=window)
            Button(lower_frame, padx=10, bd=3, text='Time / 3bv/s', font=('times', 10, 'bold'), command=change_type).pack(side='top')
            # window.bind('<Return>', lambda event: window.destroy) #Doesn't work...
            self.focus.focus_set()

        def done_action():
            "Only used when creating game."
            create_var.set('False')
            self.grid_was_created = True
            self.mines_grid = np.where(self.grid < -1, -self.grid/9, 0)
            self.mine_coords = set(map(tuple, np.transpose(np.nonzero(self.mines_grid>0))))
            self.mines = self.mines_grid.sum()
            self.get_final_grid()
            self.find_zero_patches()
            ##DispThread(threading.active_count(), self, (self.final_grid,)).start()
            prettify_grid(self.final_grid, 1)
            replay()
            done_button.forget()
            new_button_frame.pack(side='left')
            timer_label.pack(side='left')
            first_success_var.set(False)
            diff = shape_difficulty[self.shape] if self.shape in shape_difficulty else 'c'
            if diff != 'c' and detection_mines[(diff, self.detection)] == self.mines:
                self.difficulty = diff
                difficulty_var.set(diff)

        def replay(reset=True, new=False):
            if not new:
                self.grid_was_replayed = True
            if reset:
                for coord in buttons:
                 reset_button(buttons[coord], buttontexts[buttons[coord]])
            self.grid = -np.ones(self.shape, int)
            self.game_state = 'ready'
            self.time_passed = None
            #Needed when a game is stopped to restart/new.
            self.start = 0
            timer_var.set("000")
            if timer_hide_var.get():
                timer_label['fg'] = 'black'
            mines_var.set("%03d" % self.mines_grid.sum())
            mines_label.config(bg='black', fg='red')
            lives_remaining_var.set(self.lives)
            set_detection(create=False)
            set_drag()

        def change_shape():
            self.start = 0
            def reshape():
                #To avoid problems with grid size in replay(), reset the buttons here.
                for coord in buttons:
                    b = buttons[coord]
                    reset_button(b, buttontexts[b])
                #This runs if one of the dimensions of the previous shape was larger.
                for coord in [(u, v) for u in range(self.grid.shape[0]) for v in range(self.grid.shape[1]) if u >= self.shape[0] or v >= self.shape[1]]:
                    #Could use mainframe.children rather than having frames global.
                    frames[coord].grid_forget()
                    buttons.pop(coord)
                #This runs if one of the dimensions of the new shape is larger than the previous.
                for coord in [(u, v) for u in range(self.shape[0]) for v in range(self.shape[1]) if u >= self.grid.shape[0] or v >= self.grid.shape[1]]:
                    if coord in frames:
                        frames[coord].grid_propagate(False)
                        frames[coord].grid(row=coord[0], column=coord[1])
                        buttons[coord] = frames[coord].children.values()[0]
                    else:
                        make_button(coord)
                new(reset=False)
                tm.sleep(0.5)

            def get_shape(event):
                self.shape = (rows.get(), cols.get())
                self.size = self.shape[0] * self.shape[1]
                self.mines = mines.get()
                if self.mines < 1:
                    self.mines = int(round(float(self.size)*0.19/self.detection, 0))
                #[Check if this is actually custom.]
                reshape()
                customise_window.destroy()
                diff = shape_difficulty[self.shape] if self.shape in shape_difficulty else 'c'
                if diff != 'c' and detection_mines[(diff, self.detection)] == self.mines:
                    self.difficulty = diff
                    difficulty_var.set(diff)

            if difficulty_var.get() == 'c':
                try:
                    if self.focus.bindtags()[1] == 'Entry':
                        self.focus.focus_set()
                        return
                except TclError:
                    #self.focus has been destroyed.
                    pass
                self.difficulty = difficulty_var.get()
                def get_mines(event):
                    shape = (rows.get(), cols.get())
                    if shape in shape_difficulty:
                        mines.set(detection_mines[(shape_difficulty[shape], self.detection)])
                    else:
                        #Formula for getting reasonable number of mines.
                        d = detection_var.get() - 1
                        mines.set(int((0.19*d**3 - 0.39*d**2 - 0.26*d + 1)*(shape[0]*shape[1]*0.2)))
                customise_window = Toplevel(root)
                customise_window.title('Custom')
                Label(customise_window, text="Enter a number for each\nof the following:").grid(row=0, column=0, columnspan=2)
                rows = IntVar()
                rows.set(self.shape[0])
                cols = IntVar()
                cols.set(self.shape[1])
                mines = IntVar()
                mines.set(self.mines)
                self.focus = rows_entry = Entry(customise_window, textvariable=rows)
                rows_entry.icursor(END)
                columns_entry = Entry(customise_window, textvariable=cols)
                mines_entry = Entry(customise_window, textvariable=mines)
                Label(customise_window, text='Rows').grid(row=1, column=0)
                rows_entry.grid(row=1, column=1)
                Label(customise_window, text='Columns').grid(row=2, column=0)
                columns_entry.grid(row=2, column=1)
                Label(customise_window, text='Mines').grid(row=3, column=0)
                mines_entry.grid(row=3, column=1)
                rows_entry.bind('<FocusOut>', get_mines)
                columns_entry.bind('<FocusOut>', get_mines)
                rows_entry.bind('<Return>', get_shape)
                columns_entry.bind('<Return>', get_shape)
                mines_entry.bind('<Return>', get_shape)
                rows_entry.focus_set()
            else:
                self.difficulty = difficulty_var.get()
                self.shape = difficulty_shape[self.difficulty]
                self.size = self.shape[0] * self.shape[1]
                self.mines = detection_mines[(self.difficulty, self.detection)]
                reshape()

        def toggle_timer():
            if timer_label['fg'] == 'red':
                if self.game_state not in ['lost', 'won']:
                    timer_label['fg'] = 'black'
                timer_hide_var.set(True)
            elif timer_label['fg'] == 'black':
                timer_label['fg'] = 'red'
                timer_hide_var.set(False)

        def reset_settings():
            for s in default_settings:
                setattr(self, s, default_settings[s])
            first_success_var.set(self.first_success)
            if self.lives > 1:
                lives_var.set(True)
            else:
                lives_var.set(False)
            drag_click_var.set(self.drag_click)
            if self.per_cell in [1, 2, 10]:
                per_cell_var.set(self.per_cell)
            else:
                per_cell_var.set(-1)
            difficulty_var.set(self.difficulty)
            detection_var.set(self.detection)
            visitor_var.set(self.visitor)
            change_shape()

        def choose_lives():
            if self.lives > 1:
                lives_var.set(True)
            else:
                lives_var.set(False)
            if self.start:
                return
            try:
                if self.focus.bindtags()[1] == 'Entry':
                    self.focus.focus_set()
                    return
            except TclError:
                #self.focus has been destroyed.
                pass
            def get_lives(event):
                try:
                    self.lives = max(1, int(event.widget.get()))
                except ValueError:
                    self.lives = 1
                lives_remaining_var.set(self.lives)
                if self.lives > 1:
                    lives_var.set(True)
                else:
                    lives_var.set(False)
                lives_window.destroy()

            lives_window = Toplevel(root)
            lives_window.title('Lives')
            Message(lives_window, text="Enter a number of lives.").pack()
            self.focus = lives_entry = Entry(lives_window)
            lives_entry.insert(0, self.lives)
            lives_entry.pack()
            lives_entry.bind('<Return>', get_lives)
            lives_entry.focus_set()

        def set_detection(create=True):
            if self.start == 0 and self.detection != float(detection_var.get()) and not self.grid_was_created:
                self.detection = detection_options[detection_var.get()]
                if self.difficulty in difficulty_shape:
                    self.mines = detection_mines[(self.difficulty, self.detection)]
                    if create:
                        new()
                else:
                    self.get_final_grid()
                    self.find_zero_patches()

        self.focus = root = Tk()
        root.title('MineGauler')
        #Turns off the option to resize the window.
        root.resizable(False, False)

        menubar = Menu(root)
        root.config(menu=menubar)
        root.option_add('*tearOff', False)
        game_menu = Menu(menubar)
        menubar.add_cascade(label='Game', menu=game_menu)

        game_menu.add_command(label='New', command=new)
        game_menu.add_command(label='Replay', command=replay)
        create_var = BooleanVar()
        game_menu.add_checkbutton(label='Create', variable=create_var, command=create_game)
        game_menu.add_command(label='Current info', command=show_info)
        game_menu.add_command(label='Highscores', command=show_highscores)
        game_menu.add_command(label='Statistics', command=None, state='disabled')

        game_menu.add_separator()
        difficulty_var = StringVar()
        difficulty_var.set(self.difficulty)
        for i in difficulties_list:
            game_menu.add_radiobutton(label=i[1], value=i[0], variable=difficulty_var, command=change_shape)

        game_menu.add_separator()
        game_menu.add_command(label='Zoom', command=None, state='disabled')
        timer_hide_var = BooleanVar()
        game_menu.add_checkbutton(label='Hide timer', variable=timer_hide_var, command=toggle_timer)
        visitor_var = BooleanVar()
        game_menu.add_checkbutton(label='Visitor', variable=visitor_var, command=lambda: setattr(self,'visitor', visitor_var.get()))
        game_menu.add_command(label='Reset to default', command=reset_settings)

        game_menu.add_separator()
        game_menu.add_command(label='Exit', command=root.destroy)


        options_menu = Menu(menubar)
        menubar.add_cascade(label='Options', menu=options_menu)

        first_success_var = BooleanVar()
        first_success_var.set(self.first_success)
        options_menu.add_checkbutton(label='FirstAuto', variable=first_success_var, command=setattr(self, 'first_success', first_success_var.get()))

        #Used on the new game button as textvariable.
        lives_remaining_var = IntVar()
        lives_remaining_var.set(self.lives)
        lives_var = BooleanVar()
        if self.lives > 1:
            lives_var.set(True)
        options_menu.add_checkbutton(label='Lives', variable=lives_var, command=choose_lives)

        per_cell_menu = Menu(options_menu)
        per_cell_var = IntVar()
        per_cell_var.set(-1 if self.per_cell not in [1, 2, 10] else self.per_cell)
        options_menu.add_cascade(label='Max mines per cell', menu=per_cell_menu)
        per_cell_menu.add_radiobutton(label='1', value=1, variable=per_cell_var)
        per_cell_menu.add_radiobutton(label='2', value=2, variable=per_cell_var)
        per_cell_menu.add_radiobutton(label='Many', value=10, variable=per_cell_var)
        per_cell_menu.add_radiobutton(label='(Other)', value=-1, variable=per_cell_var, state='disabled')

        detection_menu = Menu(options_menu)
        detection_var = StringVar()
        detection_var.set(self.detection)
        options_menu.add_cascade(label='Detection strength', menu=detection_menu)
        #Add detection options.
        for i in sorted(list(detection_options)):
            detection_menu.add_radiobutton(label=i, value=i, variable=detection_var, command=set_detection)

        def set_drag():
            if self.start == 0:
                self.drag_click = drag_click_var.get()
        dragclick_menu = Menu(options_menu)
        options_menu.add_cascade(label='Drag and select', menu=dragclick_menu)
        drag_click_var = StringVar()
        drag_click_var.set(self.drag_click)
        for i in ['Off', 'Single click', 'Double click']:
            #Double click not yet working.
            if i[0] == 'D':
                state = 'disabled'
            else:
                state = 'active'
            dragclick_menu.add_radiobutton(label=i, value=i.split()[0].lower(), variable=drag_click_var, command=set_drag, state=state)


        help_menu = Menu(menubar)
        menubar.add_cascade(label='Help', menu=help_menu, state='disabled')
        help_menu.add_command(label='Basic rules', command=None)
        help_menu.add_command(label='Additional features', command=None)
        help_menu.add_separator()
        help_menu.add_command(label='About', command=None)


        topframe = Frame(root, pady=2)
        topframe.pack()
        mines_var = StringVar()
        mines_var.set("%03d" % self.mines_grid.sum())
        mines_label = Label(topframe, padx=7, bg='black', fg='red', bd=5, relief='sunken', font=('Verdana',11,'bold'), textvariable=mines_var)
        mines_label.pack(side='left')
        new_button_frame = Frame(topframe, padx=10, width=40, height=25)
        new_button_frame.pack(side='left')
        Button(new_button_frame, textvariable=lives_remaining_var, command=new).grid(sticky='nsew')
        timer_var = StringVar()
        timer_var.set("000")
        timer_label = Label(topframe, padx=7, bg='black', fg='red', bd=5, relief='sunken', font=('Verdana',11,'bold'), textvariable=timer_var)
        timer_label.pack(side='left')
        done_button = Button(topframe, padx=10, bd=4, text="Done", font=('Times', 10, 'bold'), command=done_action)

        def set_highscore(htype='Time', entry=None):
            self.score_checked = True
            if self.difficulty != 'c' and not self.grid_was_created and not self.grid_was_replayed:
                if entry:
                    flagging = entry['Flagging']
                else:
                    flagging = 'F' if np.where((self.grid % 9 == 0) * (self.grid < 0), 1, 0).sum() > self.lives - lives_remaining_var.get() else 'NF'
                    entry = {
                        'Name': "",
                        'Time': "{:.2f}".format(self.time_passed+0.005),
                        '3bv': self.get_3bv(),
                        '3bv/s': "{:.2f}".format(self.get_3bv()/self.time_passed+0.005),
                        'Flagging': flagging,
                        'Date': tm.asctime(),
                        'Lives remaining': lives_remaining_var.get(),
                        'First success': self.first_success,
                        'Mines grid': self.mines_grid.tolist()}
                    #Time highscores:
                settings = [self.difficulty, htype]
                for s in settings_order[2:]:
                    settings.append(getattr(self, s))
                settings = tuple(settings)
                #Time highscores:
                if htype == 'Time':
                    if settings not in self.highscores:
                        self.highscores[settings] = []
                    if len(self.highscores[settings]) < 10 or float(entry['Time']) < max(map(lambda d: float(d['Time']), self.highscores[settings][:10])) or self.visitor:
                        self.highscores[settings].append(entry)
                        self.highscores[settings] = sorted(self.highscores[settings], key=lambda d: float(d['Time']))
                        show_highscores(settings)
                    elif len([d for d in self.highscores[settings] if d['Flagging'] == flagging]) < 10 or float(entry['Time']) < max(map(lambda d: float(d['Time']), [d for d in self.highscores[settings] if d['Flagging'] == flagging])[:10]):
                        self.highscores[settings].append(entry)
                        self.highscores[settings] = sorted(self.highscores[settings], key=lambda d: float(d['Time']))
                        show_highscores(settings, flagging)
                        return
                    else:
                        set_highscore(htype='3bv/s')
                        return
                elif htype == '3bv/s':
                    if settings not in self.highscores:
                        self.highscores[settings] = []
                    if len(self.highscores[settings]) < 10 or float(entry['3bv/s']) > min(map(lambda d: float(d['3bv/s']), self.highscores[settings][:10])):
                        self.highscores[settings].append(entry)
                        self.highscores[settings] = sorted(self.highscores[settings], key=lambda d: float(d['3bv/s']), reverse=True)
                        try:
                            if self.focus.title() != 'Highscores':
                                show_highscores(settings, flagging)
                        except TclError:
                            #Highscores window not open.
                            show_highscores(settings, flagging)
                    elif len([d for d in self.highscores[settings] if d['Flagging'] == flagging]) < 10 or float(entry['3bv/s']) > min(map(lambda d: float(d['3bv/s']), [d for d in self.highscores[settings] if d['Flagging'] == flagging])[:10]):
                        self.highscores[settings].append(entry)
                        self.highscores[settings] = sorted(self.highscores[settings], key=lambda d: float(d['3bv/s']), reverse=True)
                        try:
                            if self.focus.title() != 'Highscores':
                                show_highscores(settings, flagging)
                        except TclError:
                            #Highscores window not open.
                            show_highscores(settings, flagging)

        def leftclick(coord=None, actual_click=True):
            if not coord:
                coord = self.coord_leftclicked
            elif coord == self.coord_leftclicked:
                actual_click = True
            b = buttons[coord]
            if actual_click:
                self.leftbuttondown = False
                if self.rightbuttondown:
                    if create_var.get():
                        self.blockclick = True
                    combinedclick(self.coord_rightclicked)
                    return
                elif drag_click_var.get() == 'single' and self.final_grid[coord] >= 0 and (self.start or self.game_state == 'won'):
                    # b['relief'] == 'sunken' #Why is this not sufficient?!!
                    click(coord)
                    return
                #Used in doubleleftclick().
                elif self.blockclick:
                    self.blockclick = False
                    return
            if create_var.get() and self.grid[coord] >= -1:
                b.config(relief='sunken', bd=0.5)
                self.grid[coord] += 1
                if self.grid[coord] > 0:
                    buttontexts[b].set(self.grid[coord])
                    try:
                        b['fg'] = colours[self.grid[coord]]
                    except KeyError:
                        b['fg'] = 'black'
            else:
                if self.game_state == 'ready':
                    if per_cell_var.get() not in [self.per_cell, -1] and not self.grid_was_created and not self.grid_was_replayed:
                        self.per_cell = per_cell_var.get()
                        self.create(self.mines, overwrite=1)
                        b.invoke()
                    if first_success_var.get() and self.final_grid[coord] != 0 and not self.grid_was_created and not self.grid_was_replayed: #First success criteria.
                        if self.difficulty != 'c' or not self.final_grid.all():
                            self.create(self.mines_grid.sum(), overwrite=1)
                            b.invoke()
                            return
                        else:
                            print "Unable to find zero patch - change the settings."
                    self.start = tm.time()
                    self.mines = self.mines_grid.sum()
                    self.game_state = 'active'
                if self.grid[coord] == -1 and self.game_state in ['ready', 'active']:
                    if self.final_grid[coord] == 0:
                        for patch in self.zero_patches:
                            if coord in patch:
                                break
                        for c in patch:
                            if self.grid[c] == -1:
                                click(c)
                    elif self.final_grid[coord] > 0:
                        click(coord)
                    else:
                        lives_remaining_var.set(lives_remaining_var.get()-1)
                        b['relief'] = 'raised'
                        if lives_remaining_var.get() == 0:
                            self.time_passed = tm.time() - self.start
                            self.start = 0
                            self.game_state = 'lost'
                            timer_var.set("%03d" % (min(self.time_passed, 999)))
                            timer_label['fg'] = 'red'
                            for c in buttons:
                                b1 = buttons[c]
                                if (self.grid[c] < -1 and self.grid[c] != self.final_grid[c] and self.grid[c] != -900):
                                    buttontexts[b1].set("X")
                                elif self.grid[c] >= -1 and self.final_grid[c] < 0:
                                    buttontexts[b1].set(minesymbols[-self.final_grid[c]/9 - 1])
                            b['bg'] = '#%02x%02x%02x'%(255,50,50)
                            return
                        else:
                            self.grid[coord] = self.final_grid[coord]
                            buttontexts[b].set(minesymbols[-self.final_grid[coord]/9-1])
                            b['bg'] = '#%02x%02x%02x'%(120,120,255)
                            mines_var.set("%03d" % (self.mines_grid.sum() + np.where(self.grid<-1, self.grid, 0).sum()/9))
                            if self.mines_grid.sum() + np.where(self.grid<-1, self.grid, 0).sum()/9 < 0:
                                mines_label.config(bg='red', fg='black')
                            else:
                                mines_label.config(bg='black', fg='red')
                    if (np.where(self.grid < 0, -9, self.grid) == np.where(self.final_grid < 0, -9, self.final_grid)).all():
                        self.time_passed = tm.time() - self.start
                        self.start = 0
                        self.game_state = 'won'
                        mines_var.set("000")
                        timer_var.set("%03d" % (min(self.time_passed, 999)))
                        timer_label['fg'] = 'red'
                        for c in buttons:
                            b1 = buttons[c]
                            if self.grid[c] == -1 and self.final_grid[c] < 0:
                                buttontexts[b1].set(mineflags[-self.final_grid[c]/9 - 1])
                        if self.drag_click == 'off':
                            set_highscore()

        def rightdown(event):
            coord = tuple(map(int, event.widget.bindtags()[0].split()))
            self.original_coord = self.coord_rightclicked = coord
            self.rightbuttondown = True
            self.blockclick = False
            # combinedclick() will be implemented on release.
            if self.leftbuttondown:
                self.blockclick = True
                if self.grid[coord] >= 0:
                    for c in self.get_neighbours(coord, self.detection):
                        if self.grid[c] == -1:
                            buttons[c]['relief'] = 'sunken'
                return
            b = buttons[coord]
            if create_var.get() and per_cell_var.get() > 0:
                    self.per_cell = per_cell_var.get()
            elif not create_var.get() and (not self.start or buttontexts[b].get() in minesymbols):
                    return
            self.coord_flagged = coord
            if self.grid[coord] == -1:
                buttontexts[b].set("F")
                self.grid[coord] = -9
            elif self.grid[coord] < -1:
                if self.grid[coord] > -9*self.per_cell:
                    buttontexts[b].set(mineflags[-self.grid[coord]/9])
                    self.grid[coord] -= 9
                else:
                    buttontexts[b].set("")
                    self.grid[coord] = -1
            else:
                self.coord_flagged = None
            mines_var.set("%03d" % (abs(self.mines_grid.sum() + np.where(self.grid<-1, self.grid, 0).sum()/9)))
            if not create_var.get() and self.mines_grid.sum() - np.where(self.grid<-1, -self.grid/9, 0).sum() < 0:
                mines_label.config(bg='red', fg='black')
            else:
                mines_label.config(bg='black', fg='red')

        def doubleleftclick(event):
            coord = tuple(map(int, event.widget.bindtags()[0].split()))
            b = buttons[coord]
            if buttontexts[b].get() in mineflags and self.per_cell > 2 and (self.start or create_var.get()):
                self.blockclick = True
                reset_button(b, buttontexts[b])
                self.grid[coord] = -1
                mines_var.set("%03d" % (abs(self.mines_grid.sum() + np.where(self.grid<-1, self.grid, 0).sum()/9)))
                if not create_var.get() and self.mines_grid.sum() + np.where(self.grid<-1, self.grid, 0).sum()/9 < 0:
                    mines_label.config(bg='red', fg='black')
                else:
                    mines_label.config(bg='black', fg='red')

        def leftdown(event):
            coord = tuple(map(int, event.widget.bindtags()[0].split()))
            #Used in leftclick() when dragging with combinedclick to sink original button.
            self.original_coord = coord
            self.leftbuttondown = True
            self.blockclick = False
            self.coord_leftclicked = coord
            c = self.coord_rightclicked
            if self.rightbuttondown and self.grid[c] >= 0 and (not self.coord_flagged or self.grid[self.coord_flagged] < -1):
                for c1 in self.get_neighbours(c, self.detection):
                    if self.grid[c1] == -1:
                        buttons[c1]['relief'] = 'sunken'
            elif drag_click_var.get() == 'single' and self.start:
                if self.grid[coord] == -1:
                    self.leftbuttondown = False
                leftclick(actual_click=False)

        def rightrelease(event):
            coord = self.coord_rightclicked
            self.rightbuttondown = False
            self.coord_flagged = None
            if self.leftbuttondown:
                self.blockclick = True
                combinedclick(coord)
            elif create_var.get() and self.grid[coord] >= 0 and not self.blockclick:
                reset_button(buttons[coord], buttontexts[buttons[coord]])
                self.grid[coord] = -1
            if self.start and self.leftbuttondown and self.coord_leftclicked != coord:
                buttons[self.original_coord]['relief'] = 'sunken'

        def leftrelease(event):
            coord = tuple(map(int, event.widget.bindtags()[0].split()))
            #Only click a button if the mouse was clicked on one of the button widgets in mainframe.
            if self.leftbuttondown:
                #Used to click buttons that aren't originally clicked.
                if self.rightbuttondown or (self.coord_leftclicked != coord and (self.game_state == 'ready' or (self.drag_click == 'off' and self.game_state == 'active'))):
                    leftclick()
                if self.game_state == 'won' and self.drag_click == 'single' and not self.score_checked:
                    set_highscore()
            self.leftbuttondown = False

        def motion(leftorright):
            def action(event):
                coord = tuple(map(int, event.widget.bindtags()[0].split()))
                prev_coord = self.coord_leftclicked if leftorright == 'left' else self.coord_rightclicked
                c = (coord[0]+event.y/16, coord[1]+event.x/16)
                if c in [(u, v) for u in range(self.shape[0]) for v in range(self.shape[1])] and c != prev_coord:
                    if self.rightbuttondown and self.leftbuttondown:
                        old_neighbours = self.get_neighbours(self.coord_rightclicked, self.detection, 1)
                        new_neighbours = self.get_neighbours(c, self.detection, 1)
                        for c1 in {i for i in new_neighbours if self.grid[i] == -1}:
                            buttons[c1]['relief'] = 'sunken'
                        for c1 in {i for i in old_neighbours if self.grid[i] == -1} - new_neighbours:
                            buttons[c1]['relief'] = 'raised'
                    elif leftorright == 'left' and not self.blockclick:
                        if self.grid[prev_coord] == -1 and (self.game_state == 'ready' or self.drag_click == 'off'):
                            buttons[prev_coord]['relief'] = 'raised'
                        #For when the mouse is moved from the first button clicked.
                        elif self.drag_click == 'single' and prev_coord == coord and self.game_state in ['lost', 'won', 'active']:
                            leftclick(coord)
                        if self.grid[c] == -1 and self.game_state in ['ready', 'active']:
                            if self.drag_click == 'single' and self.game_state == 'active':
                                leftclick(c, actual_click=False)
                            elif self.drag_click == 'off' or (self.drag_click == 'single' and self.game_state == 'ready'):
                                buttons[c]['relief'] = 'sunken'
                    if self.rightbuttondown:
                        self.coord_rightclicked = c
                    if self.leftbuttondown:
                        self.coord_leftclicked = c
            return action

        def combinedclick(coord):
            #Either the left or right button has been released.
            neighbours = self.get_neighbours(coord, self.detection, 1)
            for c in neighbours:
                if self.grid[c] < 0:
                    buttons[c]['relief'] = 'raised'
            if self.grid[coord] >= 0:
                neighbouring_mines = 0
                for c in neighbours:
                    if self.grid[c] < -1:
                        neighbouring_mines -= self.grid[c]/9
                    if neighbouring_mines > self.grid[coord]:
                        return
                if neighbouring_mines == self.grid[coord]:
                    for c in neighbours:
                        if self.grid[c] == -1:
                            leftclick(c, actual_click=False)

        def make_button(coord, bindings=True):
            f = Frame(mainframe, width=16, height=16)
            frames[coord] = f
            f.rowconfigure(0, weight=1) #enables button to fill frame...
            f.columnconfigure(0, weight=1)
            f.grid_propagate(False) #disables resizing of frame
            f.grid(row=coord[0], column=coord[1])
            btext = StringVar()
            b = Button(f, bd=2.4, takefocus=0, textvariable=btext, font=cellfont, command=leftclick)
            buttontexts[b] = btext #Should the button really be the key??
            buttons[coord] = b
            b.grid(sticky='nsew')
            b.bindtags(tuple([coord]+list(b.bindtags())))
            b.bind('<Button-3>', rightdown)
            b.bind('<Double-Button-1>', doubleleftclick)
            b.bind('<Button-1>', leftdown)
            b.bind('<ButtonRelease-3>', rightrelease)
            b.bind('<ButtonRelease-1>', leftrelease)
            b.bind('<B1-Motion>', motion('left'))
            b.bind('<B3-Motion>', motion('right'))

        mainframe = Frame(root, bd=10, relief='ridge')
        mainframe.pack()
        frames = dict()
        buttons = dict()
        buttontexts = dict()
        for coord in [(u, v) for u in range(self.shape[0]) for v in range(self.shape[1])]:
            make_button(coord)

        self.start = 0
        TimerThread(threading.active_count(), self, timer_var).start()
        mainloop()
        self.keeptimer = False
        for attr in delete_attrs:
            delattr(self, attr)

        if per_cell_var.get() > 0:
            self.per_cell = per_cell_var.get()
        self.first_success = first_success_var.get()
        self.detection = detection_options[detection_var.get()]
        settings = dict()
        for s in default_settings:
            settings[s] = getattr(self, s)
        with open(os.path.join(directory, 'Settings.txt'), 'w') as f:
            f.write(str(settings))

        tm.sleep(0.2)
        return


def display_grid(array, mines=False):
    if mines:
        array *= -9
    replacements = dict([(-18,':'), (-27,'%'), (-36,'#'), (-45,'&'), (-54,'$'), (-9,'*'), (0,''), (-1,''), (-8,'X')])
    root = Tk()
    for coord in [(u, v) for u in range(array.shape[0]) for v in range(array.shape[1])]:
        f = Frame(root, width=16, height=16)
        f.rowconfigure(0, weight=1) #enables button to fill frame...
        f.columnconfigure(0, weight=1)
        f.grid_propagate(False) #disables resizing of frame
        f.grid(row=coord[0], column=coord[1])
        text = replacements[array[coord]] if array[coord] in replacements else str(array[coord])
        colour = colours[array[coord]] if array[coord] in colours else 'black'
        b = Button(f, bd=2.4, takefocus=0, text=text, font=cellfont, fg=colour)
        b.grid(sticky='NSEW')
        if array[coord] >= 0:
            b['relief'] = 'sunken'
            b['bd'] = 0.5
    mainloop()
    return

def reset_button(button, textvar=None):
    button['relief'] = 'raised'
    button['fg'] = 'black'
    button['bd'] = 2.4
    button['bg'] = 'SystemButtonFace'
    button['font'] = cellfont
    if textvar:
        textvar.set("")

def prettify_grid(array, do_print=False):
        replacements = [('-18','@'), ('-27','%'), ('-36','&'), ('-45','$'), ('-9','#'), ('\n  ',' '),
                        ('0','.'), ('-1','='), ('-8','X'), ('   ',' '), ('  ',' '), ('[ ','[')]
        ret = str(array)
        for r in replacements:
            ret = ret.replace(*r)
        if do_print:
            print ret
        else:
            return ret


class PlayThread(threading.Thread):
    def __init__(self, threadID, minefield, runargs):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.runargs = runargs
        self.minefield = minefield

    def run(self):
        print "Thread {} for playing the game is running.".format(self.threadID)
        self.minefield.play(*self.runargs)
        print "Thread {} ended.".format(self.threadID)


class DispThread(threading.Thread):
    #Not used.
    def __init__(self, threadID, minefield, runargs):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.runargs = runargs
        self.minefield = minefield

    def run(self):
        print "Thread {} for displaying grids is running.".format(self.threadID)
        self.minefield.display_grid(*self.runargs)
        print "Thread {} ended.".format(self.threadID)


class TimerThread(threading.Thread):
    def __init__(self, threadID, game, timervar):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.game = game
        self.timervar = timervar

    def run(self):
        print "Thread %d for the timer is running." % self.threadID
        self.game.keeptimer = True
        while self.game.keeptimer:
            if self.game.start:
                self.timervar.set("%03d" % (min(tm.time()+1 - self.game.start, 999)))
            tm.sleep(0.16)
        print "Thread %d ended." % self.threadID



#My record of 68.7 seconds (142 3bv). Mine coordinates are below.
example = [(0, 0), (0, 11), (0, 12), (0, 14), (1, 3), (2, 3), (2, 4), (2, 8), (3, 2), (3, 3), (3, 5), (3, 15), (4, 5), (4, 7), (4, 9), (4, 11), (5, 2), (5, 6), (6, 10), (7, 8), (8, 3), (8, 10), (9, 2), (9, 12), (10, 4), (10, 7), (10, 13), (11, 2), (11, 4), (11, 7), (11, 8), (11, 9), (11, 13), (12, 9), (13, 3), (13, 7), (13, 10), (13, 15), (14, 3), (15, 7), (15, 10), (16, 0), (16, 2), (16, 9), (16, 11), (16, 13), (17, 0), (17, 7), (17, 9), (18, 1), (18, 5), (18, 9), (18, 10), (18, 13), (19, 10), (19, 15), (20, 3), (20, 6), (20, 7), (20, 15), (21, 3), (21, 5), (22, 2), (22, 6), (22, 8), (22, 12), (22, 13), (22, 14), (22, 15), (23, 0), (23, 1), (23, 8), (23, 9), (23, 12), (23, 14), (24, 3), (24, 4), (24, 10), (24, 11), (25, 0), (25, 1), (25, 3), (25, 7), (26, 8), (26, 9), (26, 11), (26, 12), (27, 9), (27, 14), (27, 15), (28, 8), (28, 9), (28, 10), (28, 11), (28, 14), (29, 6), (29, 7), (29, 10), (29, 14)]



if __name__ == '__main__':
    g = Game('i')
    #g.thread_play()
    #display_grid(Minefield(per_cell=3).mines_grid, 1)
