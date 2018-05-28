"""
minefield_widget.py - Minefield widget implementation

April 2018, Lewis Gaul

Exports:
  PanelWidget
    A panel widget class, to be packed in a parent container. Receives
    clicks and calls any registered functions.
    Arguments:
      parent - Parent widget
    Methods:
"""

import sys
from os.path import join
import logging

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap#, QPainter, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QLabel

from minegauler.utils import GameState
from .utils import img_dir, FaceState


class PanelWidget(QWidget):
    """
    The panel widget.
    """
    all_cb_names = ['new_game_cb']
    def __init__(self, parent, ctrlr):
        super().__init__(parent)
        self.ctrlr = ctrlr
        # self.setStyleSheet("border: 0px")
        # self.setFixedSize(1, 1)
        self.setFixedHeight(40)
        self.setMinimumWidth(140)
        # Callback to controller for starting a new game.
        self.new_game_cb = ctrlr.new_game
        self.setup_UI()
    
    def setup_UI(self):
        """
        Set up the widgets contained in the panel.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setAlignment(Qt.AlignCenter)
        # Mine counter widget.
        self.mines_counter = QLabel(self)
        self.mines_counter.setFixedSize(39, 26)
        self.mines_counter.setStyleSheet("""color: red;
                                            background: black;
                                            border-radius: 2px;
                                            font: bold 15px Tahoma;
                                            padding-left: 1px;""")
        layout.addWidget(self.mines_counter)
        self.set_mines_counter(0)
        layout.addStretch()
        # Face button.
        self.face_button = QLabel(self)
        self.face_button.setFixedSize(32, 32)
        self.face_button.setFrameShape(QFrame.Panel)
        self.face_button.setFrameShadow(QFrame.Raised)
        self.face_button.setLineWidth(3)
        layout.addWidget(self.face_button)
        self.set_face(FaceState.READY)
        layout.addStretch()
        # Timer widget.
        self.timer = Timer(self)
        layout.addWidget(self.timer.label)    
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            self.face_button.setFrameShadow(QFrame.Sunken)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            self.face_button.setFrameShadow(QFrame.Raised)
            if self.rect().contains(event.pos()) and self.new_game_cb:
                self.new_game_cb()

    def new_game(self):
        self.set_face(FaceState.READY)
        self.timer.stop()
        self.timer.set_time(0)
    
    def start_game(self):
        self.timer.start()
        
    def end_game(self, game_state):
        if game_state == GameState.LOST:
            self.set_face(FaceState.LOST)
        elif game_state == GameState.WON:
            self.set_face(FaceState.WON)
        self.timer.stop()
    
    def set_face(self, state):
        life = 1
        fname = f'face{life}{state.value}.png'
        pixmap = QPixmap(join(img_dir, 'faces', fname))
        self.face_button.setPixmap(
            pixmap.scaled(26, 26, transformMode=Qt.SmoothTransformation))
            
    def set_mines_counter(self, num):
        """
        This method is to be registered as a callback with a controller, as
        the widget itself can have no way of knowing how many mines are left to
        be found.
        """
        self.mines_counter.setText(f"{min(999, num):03d}")
            
        
class Timer(QTimer):
    def __init__(self, parent):
        super().__init__()
        self.label = QLabel('000', parent)
        self.label.setFixedSize(39, 26)
        self.label.setStyleSheet("""color: red;
                                    background: black;
                                    border-radius: 2px;
                                    font: bold 15px Tahoma;
                                    padding-left: 1px;""")
        self.timeout.connect(self.update)
        
    def start(self):
        self.seconds = 1
        self.set_time(self.seconds)
        super().start(1000) # Update every second
        
    def update(self):
        self.seconds += 1
        self.set_time(self.seconds)
        
    def set_time(self, seconds):
        self.label.setText('{:03d}'.format(min(seconds, 999)))


        
       
if __name__ == '__main__':
    app = QApplication(sys.argv)
    panel_widget = PanelWidget(None)
    panel_widget.show()
    sys.exit(app.exec_())