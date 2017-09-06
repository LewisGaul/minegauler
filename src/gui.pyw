"""
This file contains the GUI for minesweeper in two parts: the layout (BasicGui)
and the view and controller part of the app (GameGui).
"""

import sys
from os.path import join, exists

from PyQt5.QtWidgets import *
                            # (QApplication, QMainWindow, QWidget, QDesktopWidget,
                            #  QGridLayout, QPushButton, QLabel,)
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import pyqtSlot, Qt

from utils import im_direc


app = QApplication(sys.argv)

class BasicGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Basic layout'
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle(self.title)
        self.mainWidget = QWidget(self)
        self.setCentralWidget(self.mainWidget)
        # self.setGeometry(500, 250, 200, 300)
        self.resize(200, 100)
        self.centre()

    def centre(self):
        qr = self.frameGeometry()
        centre = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(centre)
        self.move(qr.topLeft())


class GameGUI(BasicGUI):
    styles = {'buttons': 'standard',
              'numbers': 'standard',
              'markers':  'standard'}
    btn_size = 50

    def __init__(self, processor):
        super().__init__()
        self.setWindowTitle('MineGaulerQt')
        self.procr = processor
        self.get_pixmaps()
        self.make_minefield()

    @classmethod
    def make_pixmap(cls, fname1, im_type=None, fname2=None, prop=None):
        def get_path(im_type, fname):
            base = join(im_direc, im_type)
            path = join(base, cls.styles[im_type], fname)
            if not exists(path):
                path = join(base, 'standard', fname)
            return path
        path1 = get_path('buttons', fname1)
        if im_type and fname2:
            image = QImage(path1).scaled(cls.btn_size, cls.btn_size,
                                         transformMode=Qt.SmoothTransformation)
            size2 = cls.btn_size*prop
            overlay = QPixmap(get_path(im_type, fname2)).scaled(size2, size2,
                                         transformMode=Qt.SmoothTransformation)
            painter = QPainter(image)
            margin = cls.btn_size * (1 - prop) / 2
            painter.drawPixmap(margin, margin, overlay)
            painter.end()
            image = QPixmap.fromImage(image)
        else:
            image = QPixmap(path1).scaled(cls.btn_size, cls.btn_size,
                                          transformMode=Qt.SmoothTransformation)
        return image

    @classmethod
    def get_pixmaps(cls, required='all'):
        if required in ['all', 'buttons']:
            cls.btn_images = dict()
            cls.btn_images['up'] = cls.make_pixmap('btn_up.png')
            cls.btn_images['down'] = cls.make_pixmap('btn_down.png')
            cls.btn_images[0] = cls.btn_images['down']
        if required in ['all', 'numbers', 'buttons']:
            for i in range(1, 19):
                cls.btn_images[i] = cls.make_pixmap('btn_down.png', 'numbers',
                                                    'num{}.png'.format(i), 7/8)
        if required in ['all', 'markers', 'buttons']:
            cls.mine_images = [0]
            cls.hit_images = [0]
            cls.life_images = [0]
            cls.flag_images = [0]
            cls.cross_images = [0]
            for i in range(1, 4):
                cls.mine_images.append(cls.make_pixmap('btn_down.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                cls.hit_images.append(cls.make_pixmap('btn_down_hit.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                cls.life_images.append(cls.make_pixmap('btn_down_life.png',
                    'markers', 'mine{}.png'.format(i), 7/8))
                cls.flag_images.append(cls.make_pixmap('btn_up.png',
                    'markers', 'flag{}.png'.format(i), 5/8))
                cls.cross_images.append(cls.make_pixmap('btn_up.png',
                    'markers', 'cross{}.png'.format(i), 5/8))

    def make_minefield(self):
        layout = QGridLayout(self.mainWidget)
        layout.setSpacing(0)
        self.buttons = []
        for j in range(self.procr.y_size):
            row = []
            for i in range(self.procr.x_size):
                # b = QLabel(self)
                b = Cell(self, i, j)
                layout.addWidget(b, j, i)
                row.append(b)
            self.buttons.append(row)

    def start(self):
        self.show()
        self.centre() #### Try using geometry instead, before showing
        sys.exit(app.exec_())

    def reveal_cell(self, x, y):
        b = self.buttons[y][x]
        b.reveal(self.procr.game.board[y][x])

    def finalise_loss(self):
        for (x, y) in self.procr.game.mf.all_coords:
            b = self.buttons[y][x]
            b.remove_clickability()
            board_cell = self.procr.game.board[y][x]
            if str(board_cell)[0] in ['M', '!', 'X']:
                b.reveal(board_cell)

    def finalise_win(self):
        for (x, y) in self.procr.game.mf.all_coords:
            b = self.buttons[y][x]
            b.remove_clickability()
            n = self.procr.game.mf[y][x]
            if n > 0:
                b.setPixmap(self.flag_images[n])

    def flag(self, x, y):
        b = self.buttons[y][x]
        b.setPixmap(self.flag_images[1])
        b.is_clickable = False
    def unflag(self, x, y):
        b = self.buttons[y][x]
        b.setPixmap(self.btn_images['up'])
        b.is_clickable = True


class Cell(QLabel):
    def __init__(self, parent, x, y):
        super().__init__(parent)
        self.parent = parent
        self.x = x
        self.y = y
        self.refresh()

    def mouse_press(self, e):
        print("press")
        # print(e.buttons())
        if e.button() == Qt.LeftButton and self.is_clickable:
            self.setPixmap(self.parent.btn_images['down'])
            # self.left_press()
        elif e.button() == Qt.RightButton:
            self.parent.procr.toggle_flag(self.x, self.y)
            # self.right_press()

    def mouse_release(self, e):
        print("release")
        if e.button() == Qt.LeftButton:
            self.parent.procr.click(self.x, self.y)
            # self.left_release()
        elif e.button() == Qt.RightButton:
            pass
            # self.right_release()

    def mouse_double_click(self, e):
        print("double")

    ### Actions on mouse event
    # def left_press(self):
    #     pass
    # def left_release(self):
    #     pass
    # def right_press(self):
    #     pass
    # def right_release(self):
    #     pass

    def refresh(self):
        self.setPixmap(self.parent.btn_images['up'])
        self.is_clickable = True
        self.mousePressEvent = self.mouse_press
        self.mouseReleaseEvent = self.mouse_release
        self.mouseDoubleClickEvent = self.mouse_double_click

    def remove_clickability(self):
        for event in ['mousePressEvent', 'mouseReleaseEvent',
                      'mouseDoubleClickEvent']:
            setattr(self, event, lambda e: None)

    def reveal(self, contents):
        self.remove_clickability()
        if type(contents) is int:
            self.setPixmap(self.parent.btn_images[contents])
            return
        elif type(contents) is str:
            char = contents[0]
            if len(contents) == 1:
                n = 1     # Represents one mine
            else:
                n = int(contents[1])
        if char == 'M':
            self.setPixmap(self.parent.mine_images[n])
        elif char == '!':
            self.setPixmap(self.parent.hit_images[n])
        elif char == 'X':
            self.setPixmap(self.parent.cross_images[n])
        elif char == 'L':
            self.setPixmap(self.parent.life_images[n])



if __name__ == '__main__':
	# app = QApplication(sys.argv)
	win = BasicGUI()
	win.show()
	sys.exit(app.exec_())
