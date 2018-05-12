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
import logging

from PyQt5.QtCore import Qt
# from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QLabel


class PanelWidget(QWidget):
    """
    The panel widget.
    """
    all_cb_names = ['new_game_cb']
    def __init__(self, parent):
        super().__init__(parent)
        # self.setStyleSheet("border: 0px")
        # self.setFixedSize(1, 1)
        self.setFixedHeight(40)
        self.setMinimumWidth(140)
        # Callback to controller for starting a new game.
        self.new_game_cb = None
        self.setup_UI()
    
    def setup_UI(self):
        """
        
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
        self.mines_counter.setText("000")
        layout.addWidget(self.mines_counter)
        layout.addStretch()
        # Face button.
        self.face_button = QLabel(self)
        self.face_button.setFixedSize(32, 32)
        self.face_button.setFrameShape(QFrame.Panel)
        self.face_button.setFrameShadow(QFrame.Raised)
        self.face_button.setLineWidth(3)
        layout.addWidget(self.face_button)
        layout.addStretch()
        # Timer widget.
        # self.timer = TimerWidget(self)
        self.timer = QLabel(self)
        self.timer.setFixedSize(39, 26)
        self.timer.setStyleSheet("""color: red;
                                    background: black;
                                    border-radius: 2px;
                                    font: bold 15px Tahoma;
                                    padding-left: 1px;""")
        self.timer.setText("000")
        layout.addWidget(self.timer)    
    
    def register_all_cbs(self, ctrlr):
        """
        Register a callback for each callback specified in self.all_cb_names
        using methods of the ctrlr which match the callback names. If any
        methods are missing no callback is registered and no error is raised.
        """
        for cb_name in self.all_cb_names:
            if hasattr(ctrlr, cb_name[:-3]):
                setattr(self, cb_name, getattr(ctrlr, cb_name[:-3]))

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
        print('New')
        # Reset mine counter and timer.
        
    def end_game(self):
        print("Ending")
        # Stop the timer.

        
       
if __name__ == '__main__':
    app = QApplication(sys.argv)
    panel_widget = PanelWidget(None)
    panel_widget.show()
    sys.exit(app.exec_())