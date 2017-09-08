"""
This file contains the GUI for minesweeper in two parts: the layout (BasicGui)
and the view and controller part of the app (GameGui).
"""

import sys
from os.path import join, exists

from PyQt5.QtWidgets import *
                            # (QApplication, QMainWindow, QWidget, QDesktopWidget,
                            #  QGridLayout, QPushButton, QLabel,)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QIcon
from PyQt5.QtCore import pyqtSignal, Qt, QSize

from utils import im_direc


app = QApplication(sys.argv)

class GameGUI(QMainWindow):
    btn_size = 16
    styles = {'buttons': 'pi',
              'numbers': 'standard',
              'markers':  'standard'}
    def __init__(self, processor):
        super().__init__()
        self.setWindowTitle('MineGaulerQt')
        self.procr = processor
        self.settings = {'btn_size': self.btn_size, 'styles': self.styles}
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
        self.minefield_widget = MinefieldWidget(self.body, self.procr,
                                                self.settings)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(self.minefield_widget)
        self.setMaximumSize(self.body.width(),
                            self.panel.height() + self.body.height())

    def start(self):
        self.move(500, 150)
        self.show()
        return app.exec_()

    def reveal_cell(self, x, y):
        b = self.minefield_widget.buttons[y][x]
        b.reveal(self.procr.game.board[y][x])

    def finalise_loss(self):
        self.panel.face_button.set_face('lost', 1)
        for (x, y) in self.procr.game.mf.all_coords:
            b = self.minefield_widget.buttons[y][x]
            b.remove_clickability()
            board_cell = self.procr.game.board[y][x]
            if str(board_cell)[0] in ['M', '!', 'X']:
                b.reveal(board_cell)

    def finalise_win(self):
        self.panel.face_button.set_face('won', 1)
        for (x, y) in self.procr.game.mf.all_coords:
            b = self.minefield_widget.buttons[y][x]
            b.remove_clickability()
            n = self.procr.game.mf[y][x]
            if n > 0:
                b.setPixmap(self.flag_images[n])

    def flag(self, x, y, n):
        b = self.buttons[y][x]
        b.setPixmap(self.flag_images[n])
        b.is_clickable = False
    def unflag(self, x, y):
        b = self.buttons[y][x]
        b.setPixmap(self.btn_images['up'])
        b.is_clickable = True

    def start_new_game(self):
        self.panel.face_button.set_face('ready', 1)
        for (x, y) in self.procr.game.mf.all_coords:
            self.minefield_widget.buttons[y][x].refresh()


class MinefieldWidget(QWidget):
    def __init__(self, parent, processor, settings):
        super().__init__(parent)
        self.procr = processor
        for attr in ['btn_size', 'styles']:
            setattr(self, attr, settings[attr])
        self.populate()
        self.get_pixmaps()
        self.mouse_coord = None
    def populate(self):
        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.buttons = []
        for j in range(self.procr.y_size):
            row = []
            for i in range(self.procr.x_size):
                b = CellButton(self, self.procr, i, j)
                layout.addWidget(b, j, i)
                row.append(b)
            self.buttons.append(row)
    def make_pixmap(self, fname1, im_type, fname2=None, prop=None):
        def get_path(im_type, fname):
            base = join(im_direc, im_type)
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
        if event.buttons() == Qt.LeftButton:
            self.buttons[y][x].pressed.emit()
    def mouseReleaseEvent(self, event):
        x, y = event.x() // self.btn_size, event.y() // self.btn_size
        # print(x, y)
        self.mouse_coord = None
        if event.button() == Qt.LeftButton:
            self.buttons[y][x].clicked.emit()
    def mouseMoveEvent(self, event):
        x, y = event.x() // self.btn_size, event.y() // self.btn_size
        if (x, y) != self.mouse_coord:
            old_x, old_y = self.mouse_coord
            self.mouse_coord = (x, y)
            if event.buttons() == Qt.LeftButton:
                self.buttons[old_y][old_x].released.emit()
                self.buttons[y][x].pressed.emit()


class CellButton(QLabel):
    pressed = pyqtSignal()
    released = pyqtSignal()
    clicked = pyqtSignal()
    def __init__(self, parent, processor, x, y):
        super().__init__(parent)
        self.parent = parent
        self.procr = processor
        self.x, self.y = x, y
    def push(self):
        self.setPixmap(self.parent.btn_images['down'])
    def release(self):
        self.setPixmap(self.parent.btn_images['up'])
    def click(self):
        self.procr.click(self.x, self.y)
    # def right_press(self):
    #     self.procr.toggle_flag(self.x, self.y)
    # def mouse_double_click(self, e):
    #     print("double")
    def refresh(self):
        self.setPixmap(self.parent.btn_images['up'])
        self.is_clickable = True
        self.pressed.connect(self.push)
        self.released.connect(self.release)
        self.clicked.connect(self.click)
    def remove_interaction(self):
        for signal in ['pressed', 'released', 'clicked']:
            getattr(self, signal).disconnect()
    def reveal(self, contents):
        self.remove_interaction()
        if type(contents) is int:
            self.setPixmap(self.parent.btn_images[contents])
        elif type(contents) is str:
            char = contents[0]
            mines = int(contents[1])
            if char == 'M':
                self.setPixmap(self.parent.mine_images[mines])
            elif char == '!':
                self.setPixmap(self.parent.hit_images[mines])
            elif char == 'X':
                self.setPixmap(self.parent.cross_images[mines])
            elif char == 'L':
                self.setPixmap(self.parent.life_images[mines])


class FaceButton(QLabel):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.pixmap = None
        self.setFixedSize(size, size)
        self.setLineWidth(3)
        self.setFrameShadow(QFrame.Raised)
        self.setFrameShape(QFrame.Panel)
    def set_face(self, state, life=1):
        fname = 'face' + str(life) + state + '.png'
        pixmap = QPixmap(join(im_direc, 'faces', fname))
        self.setPixmap(pixmap.scaled(self.width()-6, self.height()-6,
                       transformMode=Qt.SmoothTransformation))

class TopPanel(QAbstractButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.populate()
    def paintEvent(self, e):
        pass
    def sizeHint(self):
        return QSize(100, 40)
    def populate(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setAlignment(Qt.AlignCenter)
        self.mine_counter = QLabel('099', self)
        self.mine_counter.setFixedWidth(20)
        layout.addWidget(self.mine_counter)
        layout.addStretch()
        self.face_button = FaceButton(self, 32)
        layout.addWidget(self.face_button)
        layout.addStretch()
        self.timer = QLabel('000', self)
        self.timer.setFixedWidth(20)
        layout.addWidget(self.timer)
    # def mousePressEvent(self, e):
    #     self.face_button.setFrameShadow(QFrame.Sunken)
    # def mouseReleaseEvent(self, e):
    #     self.face_button.setFrameShadow(QFrame.Raised)
        # if self.underMouse():
        #     self.clicked.emit()


if __name__ == '__main__':
	# app = QApplication(sys.argv)
	win = BasicGUI()
	win.show()
	sys.exit(app.exec_())
