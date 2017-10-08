"""
This file contains the GUI for minesweeper in two parts: the layout (BasicGui)
and the view and controller part of the app (GameGui).
"""

import sys
from os.path import join, exists, basename
from glob import glob

from PyQt5.QtWidgets import *
                            # (QApplication, QMainWindow, QWidget, QDesktopWidget,
                            #  QGridLayout, QPushButton, QLabel,)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QIcon
from PyQt5.QtCore import pyqtSignal, Qt, QSize

from utils import img_direc, get_nbrs


def QMouseButton_to_int(QMouseButton):
    if QMouseButton == Qt.LeftButton:
        return int(Qt.LeftButton)
    elif QMouseButton == Qt.RightButton:
        return int(Qt.RightButton)
    elif QMouseButton == Qt.LeftButton | Qt.RightButton:
        return int(Qt.LeftButton | Qt.RightButton)

app = QApplication(sys.argv)

class GameGUI(QMainWindow):
    btn_size = 16
    styles = {'buttons': 'pi',
              'numbers': 'standard',
              'markers':  'standard'}
    drag_select = True
    def __init__(self, processor):
        super().__init__()
        self.setWindowTitle('MineGaulerQt')
        self.procr = processor
        self.settings = dict()
        for attr in ['btn_size', 'styles', 'drag_select']:
            self.settings[attr] = getattr(self, attr)
        self.setupUI()
    def setupUI(self):
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        vlayout = QVBoxLayout(centralWidget)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        # Top panel widget configuration
        self.panel_frame = QFrame(centralWidget)
        self.panel_frame.setFixedHeight(40)
        self.panel_frame.setFrameShadow(QFrame.Sunken)
        self.panel_frame.setFrameShape(QFrame.Panel)
        self.panel_frame.setLineWidth(2)
        self.panel = TopPanel(self.panel_frame)
        vlayout.addWidget(self.panel_frame)
        lyt = QVBoxLayout(self.panel_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(self.panel)
        self.panel.pressed.connect(
            lambda: self.panel.face_button.setFrameShadow(QFrame.Sunken))
        self.panel.released.connect(
            lambda: self.panel.face_button.setFrameShadow(QFrame.Raised))
        self.panel.clicked.connect(self.procr.start_new_game)
        # Main body widget config - use horizontal layout for centre alignment
        hstretch = QHBoxLayout()
        hstretch.addStretch()
        self.body = QFrame(centralWidget)
        self.body.setFrameShadow(QFrame.Raised)
        self.body.setFrameShape(QFrame.Box)
        self.body.setLineWidth(5)
        hstretch.addWidget(self.body)
        hstretch.addStretch()
        vlayout.addLayout(hstretch)
        lyt = QVBoxLayout(self.body)
        self.mf_widget = MinefieldWidget(self.body, self.procr,
                                                self, **self.settings)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(self.mf_widget)
        self.make_menubar()
        self.setMaximumSize(self.body.width(),
                            self.panel.height() + self.body.height())
    def make_menubar(self):
        menu = self.menuBar() # QMainWindow has QMenuBar already
        game_menu = menu.addMenu('Game')
        opts_menu = menu.addMenu('Options')
        help_menu = menu.addMenu('Help')
        new_act = QAction('New', self)
        game_menu.addAction(new_act)
        new_act.triggered.connect(self.procr.start_new_game)
        new_act.setShortcut('F2')
        replay_act = QAction('Replay', self)
        # replay_act.triggered.connect(SOMETHING)
        replay_act.setShortcut('F3')
        game_menu.addAction(replay_act)
        game_menu.addSeparator()
        group = QActionGroup(self, exclusive=True)
        for diff in ['Beginner', 'Intermediate', 'Expert', 'Master', 'Custom']:
            diff_act = QAction(diff, self, checkable=True)
            # diff_act.triggered.connect(SOMETHING)
            diff_act.setShortcut(diff[0])
            group.addAction(diff_act)
            game_menu.addAction(diff_act)
        game_menu.addSeparator()
        zoom_act = QAction('Zoom', self)
        # zoom_act.triggered.connect(SOMETHING)
        game_menu.addAction(zoom_act)
        styles_menu = QMenu('Styles', self)
        game_menu.addMenu(styles_menu)
        for img_group in ['buttons']:
            submenu = QMenu(img_group.capitalize(), self)
            styles_menu.addMenu(submenu)
            group = QActionGroup(self, exclusive=True)
            for folder in glob(join(img_direc, img_group, '*')):
                style = basename(folder)
                style_act = QAction(style, self, checkable=True)
                # style_act.triggered.connect(SOMETHING)
                group.addAction(style_act)
                submenu.addAction(style_act)
        game_menu.addSeparator()
        exit_act = QAction('Exit', self)
        # exit_act.triggered.connect(SOMETHING)
        exit_act.setShortcut('Alt+F4')
        game_menu.addAction(exit_act)
        first_act = QAction('Safe start', self, checkable=True)
        # first_act.triggered.connect(SOMETHING)
        opts_menu.addAction(first_act)
        drag_act = QAction('Drag-select', self, checkable=True)
        drag_act.triggered.connect(self.set_drag_select)
        drag_act.setChecked(self.drag_select)
        opts_menu.addAction(drag_act)
    def set_drag_select(self):
        # [Should check if a game is in play]
        # print(self.drag_select)
        self.drag_select = not(self.drag_select)
        self.mf_widget.drag_select = self.drag_select
    def start(self):
        self.move(500, 150)
        self.show()
        app.exec_()
    def reveal_cell(self, x, y):
        """Make the cell at (x, y) show the same as is contained in the current
        game board."""
        b = self.mf_widget.buttons[y][x]
        contents = self.procr.game.board[y][x]
        if type(contents) is int:
            im_type = 'btn'
            num = contents
        elif type(contents) is str:
            char = contents[0]
            num = int(contents[1])
            if char == 'F':
                im_type = 'flag'
            elif char == 'M':
                im_type = 'mine'
            elif char == '!':
                im_type = 'hit'
            elif char == 'X':
                im_type = 'cross'
            elif char == 'L':
                im_type = 'life'
        else:
            # Used for dummy processor with an empty board
            return
        b.set_image(im_type, num)
    def finalise_loss(self):
        self.set_face('lost')
        for (x, y) in self.mf_widget.all_coords:
            b = self.mf_widget.buttons[y][x]
            b.remove_interaction()
            board_cell = self.procr.game.board[y][x]
            if str(board_cell)[0] in ['M', '!', 'X']:
                self.reveal_cell(x, y)
    def finalise_win(self):
        for (x, y) in self.mf_widget.all_coords:
            b = self.mf_widget.buttons[y][x]
            b.remove_interaction()
            n = self.procr.game.mf[y][x]
            if n > 0:
                self.reveal_cell(x, y)
                # b.setPixmap(self.flag_images[n])
        self.set_face('won')
        self.set_mines_counter()
    def flag(self, x, y, n):
        b = self.mf_widget.buttons[y][x]
        b.setPixmap(self.mf_widget.flag_images[n])
        rem_mines = self.procr.nr_mines - self.procr.nr_flags
        self.set_mines_counter()
        b.pressed.disconnect()
        b.released.disconnect()
        b.clicked.disconnect()
        b.areaPressed.disconnect()
        b.areaReleased.disconnect()
    def unflag(self, x, y):
        b = self.mf_widget.buttons[y][x]
        b.refresh()
        self.set_mines_counter()
    def set_mines_counter(self):
        rem_mines = self.procr.nr_mines - self.procr.nr_flags
        self.panel.mines_counter.setText('{:03d}'.format(abs(rem_mines)))
        if rem_mines >= 0:
            self.panel.mines_counter.setStyleSheet("""color: red;
                                                      background: black;
                                                      border-radius: 2px;
                                                      font: bold 15px Tahoma;
                                                      padding-left: 1px;""")
        else:
            self.panel.mines_counter.setStyleSheet("""color: black;
                                                      background: red;
                                                      border-radius: 2px;
                                                      font: bold 15px Tahoma;
                                                      padding-left: 1px;""")
    def set_face(self, state, check_game_state=False):
        if (check_game_state and
            self.procr.game.state not in ['ready', 'active']):
            return False
        life = 1
        fname = 'face' + str(life) + state + '.png'
        pixmap = QPixmap(join(img_direc, 'faces', fname))
        self.panel.face_button.setPixmap(pixmap.scaled(26, 26,
                                         transformMode=Qt.SmoothTransformation))
        return True
    def start_new_game(self):
        for (x, y) in self.mf_widget.all_coords:
            self.mf_widget.buttons[y][x].refresh()
        self.set_face('ready')
        self.set_mines_counter()


class MinefieldWidget(QWidget):
    def __init__(self, parent, processor, gui, **settings):
        super().__init__(parent)
        self.procr = processor
        self.gui = gui
        self.x_size, self.y_size = self.procr.x_size, self.procr.y_size
        self.all_coords = [(i, j) for i in range(self.x_size)
                           for j in range(self.y_size)]
        for attr in ['btn_size', 'styles', 'drag_select']:
            setattr(self, attr, settings[attr])
        self.populate()
        self.get_pixmaps()
        self.mouse_coord = None
        self.both_mouse_buttons_pressed = False
        self.mouse_buttons_down = Qt.NoButton
    def populate(self):
        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.buttons = []
        for j in range(self.y_size):
            row = []
            for i in range(self.x_size):
                b = CellButton(self, self.procr, i, j)
                layout.addWidget(b, j, i)
                row.append(b)
            self.buttons.append(row)
    def make_pixmap(self, fname1, im_type, fname2=None, prop=None):
        def get_path(im_type, fname):
            base = join(img_direc, im_type)
            path = join(base, self.styles[im_type], fname)
            if not exists(path):
                path = join(base, 'standard', fname)
            return path
        path1 = get_path('buttons', fname1)
        if fname2:
            image = QImage(path1).scaled(self.btn_size, self.btn_size,
                                         transformMode=Qt.SmoothTransformation)
            size2 = self.btn_size*prop
            overlay = QPixmap(get_path(im_type, fname2)).scaled(size2, size2,
                                         transformMode=Qt.SmoothTransformation)
            painter = QPainter(image)
            margin = self.btn_size * (1 - prop) / 2
            painter.drawPixmap(margin, margin, overlay)
            painter.end()
            image = QPixmap.fromImage(image)
        else:
            image = QPixmap(path1).scaled(self.btn_size, self.btn_size,
                                          transformMode=Qt.SmoothTransformation)
        return image
    def get_pixmaps(self, required='all'):
        if required in ['all', 'buttons']:
            self.btn_images = dict()
            self.btn_images['up'] = self.make_pixmap('btn_up.png', 'buttons')
            self.btn_images['down'] = self.make_pixmap('btn_down.png', 'buttons')
            self.btn_images[0] = self.btn_images['down']
        if required in ['all', 'numbers', 'buttons']:
            for i in range(1, 19):
                self.btn_images[i] = self.make_pixmap('btn_down.png', 'numbers',
                                                    'num{}.png'.format(i), 7/8)
        if required in ['all', 'markers', 'buttons']:
            self.mine_images = [0]
            self.hit_images = [0]
            self.life_images = [0]
            self.flag_images = [0]
            self.cross_images = [0]
            for i in range(1, 4):
                self.mine_images.append(self.make_pixmap('btn_down.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                self.hit_images.append(self.make_pixmap('btn_down_hit.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                self.life_images.append(self.make_pixmap('btn_down_life.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                self.flag_images.append(self.make_pixmap('btn_up.png',
                    'markers', 'flag{}.png'.format(i), 5/8))
                self.cross_images.append(self.make_pixmap('btn_up.png',
                    'markers', 'cross{}.png'.format(i), 5/8))
    def mousePressEvent(self, event):
        x, y = event.x() // self.btn_size, event.y() // self.btn_size
        self.mouse_coord = (x, y)
        b = self.buttons[y][x]
        self.mouse_buttons_down = QMouseButton_to_int(event.buttons())
        if self.mouse_buttons_down == int(Qt.LeftButton):
            self.both_mouse_buttons_pressed = False
            if self.drag_select:
                self.gui.set_face('active', check_game_state=True)
            b.pressed.emit()
        elif self.mouse_buttons_down == int(Qt.RightButton):
            self.both_mouse_buttons_pressed = False
            b.rightPressed.emit()
        elif self.mouse_buttons_down == int(Qt.LeftButton | Qt.RightButton):
            self.both_mouse_buttons_pressed = True
            # Reset face to account for case drag_select=True
            self.gui.set_face('ready', check_game_state=True)
            self.sink_area(x, y)
            if self.drag_select:
                self.procr.chord(x, y)
    def mouseReleaseEvent(self, event):
        if not self.mouse_coord:
            return # Do nothing it not currently over a button
        x, y = self.mouse_coord
        self.mouse_coord = None
        self.mouse_buttons_down -= QMouseButton_to_int(event.button())
        b = self.buttons[y][x]
        # Catch a case for drag_select=True (left-down always active)
        self.gui.set_face('ready', check_game_state=True)
        if self.mouse_buttons_down != int(Qt.NoButton): # Both buttons were down
            self.raise_area(x, y)
            if not self.drag_select:
                self.procr.chord(x, y)
            elif self.drag_select and event.button() == Qt.RightButton:
                self.gui.set_face('active', check_game_state=True)
        elif event.button() == Qt.LeftButton:
            if self.drag_select or not self.both_mouse_buttons_pressed:
                b.clicked.emit()
    def mouseMoveEvent(self, event):
        old_coord = self.mouse_coord
        x, y = event.x() // self.btn_size, event.y() // self.btn_size
        # Update mouse_coord
        self.mouse_coord = (x, y) if (x, y) in self.all_coords else None
        if old_coord != self.mouse_coord:
            if (event.buttons() != Qt.LeftButton | Qt.RightButton
                and self.both_mouse_buttons_pressed and not self.drag_select):
                # Do nothing if both buttons were pressed but aren't currently
                return
            if old_coord:
                old_x, old_y = old_coord
                if event.buttons() == Qt.LeftButton:
                    self.buttons[old_y][old_x].released.emit()
                elif event.buttons() == Qt.LeftButton | Qt.RightButton:
                    self.raise_area(old_x, old_y)
            if self.mouse_coord:
                if event.buttons() == Qt.LeftButton:
                    self.buttons[y][x].pressed.emit()
                elif event.buttons() == Qt.RightButton and self.drag_select:
                    self.buttons[y][x].rightPressed.emit()
                elif event.buttons() == Qt.LeftButton | Qt.RightButton:
                    self.sink_area(x, y)
    def sink_area(self, x, y):
        for (i, j) in get_nbrs(x, y, self.x_size, self.y_size):
            self.buttons[j][i].areaPressed.emit()
    def raise_area(self, x, y):
        for (i, j) in get_nbrs(x, y, self.x_size, self.y_size):
            self.buttons[j][i].areaReleased.emit()


class CellButton(QLabel):
    pressed = pyqtSignal()      # Left mouse button pressed down over button
    released = pyqtSignal()     # Left mouse button moved away from button
    clicked = pyqtSignal()      # Left mouse button released over button
    rightPressed = pyqtSignal() # Right mouse button pressed down
    areaPressed = pyqtSignal()  # Both mouse buttons down on a button in area
    areaReleased = pyqtSignal() # Area release (move away/raise mouse button...)
    def __init__(self, parent, processor, x, y):
        super().__init__(parent)
        self.parent = parent #stores data such as images, settings
        self.procr = processor
        self.x, self.y = x, y
    def press(self):
        if self.parent.drag_select:
            self.procr.click(self.x, self.y)
        else:
            self.parent.gui.set_face('active')
            self.setPixmap(self.parent.btn_images['down'])
    def release(self):
        self.parent.gui.set_face('ready')
        self.setPixmap(self.parent.btn_images['up'])
    def click(self):
        self.parent.gui.set_face('ready')
        self.procr.click(self.x, self.y)
    def rightPress(self):
        self.procr.toggle_flag(self.x, self.y)
    def areaPress(self):
        self.parent.gui.set_face('active')
        self.setPixmap(self.parent.btn_images['down'])
    def refresh(self):
        self.setPixmap(self.parent.btn_images['up'])
        # First remove connections so that signals are only connected once.
        self.remove_interaction()
        self.pressed.connect(self.press)
        self.released.connect(self.release)
        self.clicked.connect(self.click)
        self.rightPressed.connect(self.rightPress)
        self.areaPressed.connect(self.areaPress)
        self.areaReleased.connect(self.release)
    def remove_interaction(self):
        """Remove all connected signals for interation through clicks."""
        for signal in ['pressed', 'released', 'clicked', 'rightPressed',
                       'areaPressed', 'areaReleased']:
            try:
                getattr(self, signal).disconnect()
            except TypeError:
                pass # Already disconnected
    def set_image(self, im_type, num):
        self.remove_interaction()
        images = getattr(self.parent, im_type + '_images')
        self.setPixmap(images[num])


class TopPanel(QAbstractButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.populate()
    def paintEvent(self, e):
        # Must be implemented on QAbstractButton
        pass
    def sizeHint(self):
        return QSize(100, 40)
    def populate(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setAlignment(Qt.AlignCenter)
        self.mines_counter = QLabel(self)
        self.mines_counter.setFixedSize(39, 26)
        self.mines_counter.setFrameShape(QFrame.Panel)
        self.mines_counter.setFrameShadow(QFrame.Sunken)
        self.mines_counter.setLineWidth(2)
        # self.mines_counter.setStyleSheet("""color: red;
        #                                    background: black;
        #                                    border-radius: 2px;
        #                                    font: bold 15px Tahoma;
        #                                    padding-left: 1px;""")
        layout.addWidget(self.mines_counter)
        layout.addStretch()
        self.face_button = QLabel(self)
        self.face_button.setFixedSize(32, 32)
        self.face_button.setFrameShape(QFrame.Panel)
        self.face_button.setFrameShadow(QFrame.Raised)
        self.face_button.setLineWidth(3)
        layout.addWidget(self.face_button)
        layout.addStretch()
        self.timer = QLabel('000', self)
        self.timer.setFixedSize(39, 26)
        self.timer.setFrameShape(QFrame.Panel)
        self.timer.setFrameShadow(QFrame.Sunken)
        self.timer.setLineWidth(5)
        self.timer.setStyleSheet("""color: red;
                                    background: black;
                                    border-radius: 2px;
                                    font: bold 15px Tahoma;
                                    padding-left: 1px;""")
        layout.addWidget(self.timer)




if __name__ == '__main__':
	# app = QApplication(sys.argv)
    from Testing.dummies import DummyProcessor
    win = GameGUI(DummyProcessor())
    win.start_new_game()
    win.start()
