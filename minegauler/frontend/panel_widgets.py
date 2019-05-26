"""
panel_widgets.py - Widgets in the top panel

April 2018, Lewis Gaul

Exports:
PanelWidget
    A panel widget class, to be packed in a parent container. Receives
    clicks and calls any registered functions.
"""

import logging
import sys
from os.path import join

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QLabel

from minegauler.frontend.utils import img_dir
from minegauler.shared.internal_types import FaceState, GameState


class PanelWidget(QWidget):
    """
    The panel widget.
    """
    def __init__(self, parent, ctrlr):
        """
        Arguments:
        parent
            Qt container widget.
        ctrlr (minegauler.backend.Controller)
            To access game engine methods.
        """
        super().__init__(parent)
        self.ctrlr = ctrlr
        self.setFixedHeight(40)
        self.setMinimumWidth(140)
        self.setup_UI()
        self.game_state = GameState.INVALID
        # Callback to controller for starting a new game.
        # cb_core.end_game.connect(self.end_game)
        # cb_core.new_game.connect(lambda: self.set_face(FaceState.READY))
        # cb_core.start_game.connect(self.timer.start)
        # cb_core.set_mines_counter.connect(self.set_mines_counter)
        # cb_core.at_risk.connect(lambda: self.set_face(FaceState.ACTIVE))
        # cb_core.no_risk.connect(lambda: self.set_face(FaceState.READY))
    
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
        self.set_mines_counter(self.ctrlr.mines_remaining)
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
        layout.addWidget(self.timer.widget)

    # --------------------------------------------------------------------------
    # Qt method overrides
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            self.face_button.setFrameShadow(QFrame.Sunken)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            self.face_button.setFrameShadow(QFrame.Raised)
            if self.rect().contains(event.pos()):
                self.request_new_game()

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def request_new_game(self):
        """
        A new game has been requested, call backend.
        """
        self.set_face(FaceState.READY)
        self.timer.stop()
        self.timer.set_time(0)
        self.ctrlr.new_game()
    
    def set_face(self, state):
        """
        Arguments:
        state (str | GameState | FaceState)
        """
        try:
            state = state.value.lower()
        except AttributeError:
            pass
        life = 1
        fname = f'face{life}{state}.png'
        pixmap = QPixmap(join(img_dir, 'faces', fname))
        self.face_button.setPixmap(
            pixmap.scaled(26, 26, transformMode=Qt.SmoothTransformation))
            
    def set_mines_counter(self, num):
        """
        This method is to be registered as a callback with a controller, as
        the widget itself can have no way of knowing how many mines are left to
        be found.
        """
        if num < 0:
            foreground = 'black'
            background = 'red'
        else:
            foreground = 'red'
            background = 'black'
        self.mines_counter.setStyleSheet(f"""color: {foreground};
                                            background: {background};
                                            border-radius: 2px;
                                            font: bold 15px Tahoma;
                                            padding-left: 1px;""")
        self.mines_counter.setText(f"{min(999, abs(num)):03d}")

    def update_game_state(self, state):
        """
        Receive an update from a backend.

        Arguments:
        state (GameState)
            The current game state.
        """
        if self.game_state != state:
            if state == GameState.ACTIVE:
                self.timer.start()
            elif state in {GameState.WON, GameState.LOST}:
                self.timer.stop()
                self.set_face(state)
        self.game_state = state



class Timer(QTimer):
    def __init__(self, parent):
        super().__init__()
        self.widget = QLabel('000', parent)
        self.widget.setFixedSize(39, 26)
        self.widget.setStyleSheet("""color: red;
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
        self.widget.setText('{:03d}'.format(min(seconds, 999)))


        
       
if __name__ == '__main__':
    from minegauler.backend import Controller, GameOptsStruct
    app = QApplication(sys.argv)
    panel_widget = PanelWidget(None, Controller(GameOptsStruct()))
    panel_widget.show()
    sys.exit(app.exec_())